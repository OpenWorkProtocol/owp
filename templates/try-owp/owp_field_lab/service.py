from __future__ import annotations

import csv
import hashlib
import hmac
import io
import json
import os
import re
import secrets
import sqlite3
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urlsplit

from .db import append_event, connect, init_db, utc_now, verify_event_chain
from .errors import (
    DuplicateSubmission,
    InvalidTransition,
    NotFound,
    QueueFull,
    Unauthorized,
    ValidationError,
)
from .github import GitHubVerifier, PRSnapshot, parse_pr_url

ACTIVE_STATES = {"proposed", "todo", "in_progress", "parked", "review"}
TERMINAL_STATES = {"completed", "cancelled"}
INTAKE_NOTICE_VERSION = "2026-08-21-field-lab-v1"
PROFILE = "owp-field-lab/0.1"



def normalize_optional_https(value: str) -> str:
    value = (value or "").strip()
    if not value:
        return ""
    if len(value) > 2000:
        raise ValidationError("Context URL must be 2,000 characters or fewer.")
    parsed = urlsplit(value)
    if parsed.scheme.lower() != "https" or not parsed.hostname:
        raise ValidationError("Context URL must use https:// or be left blank.")
    return value


def normalize_work_kind(value: str) -> str:
    kind = (value or "github_pr").strip().lower()
    if kind not in {"github_pr", "idea"}:
        raise ValidationError("Work type must be github_pr or idea.")
    return kind

def parse_bid_usd(value: Any) -> int:
    try:
        text = str(value).strip()
        amount = Decimal(text)
    except (InvalidOperation, ValueError):
        raise ValidationError("Value signal must be a valid USD amount.")
    if not amount.is_finite():
        raise ValidationError("Value signal must be a finite USD amount.")
    if amount <= 0:
        raise ValidationError("Value signal must be greater than $0.")
    if amount > Decimal("1000000"):
        raise ValidationError("Value signal cannot exceed $1,000,000 in this field lab.")
    cents_exact = amount * 100
    if cents_exact != cents_exact.quantize(Decimal("1"), rounding=ROUND_HALF_UP):
        raise ValidationError("Value signal may have at most two decimal places.")
    return int(cents_exact)


def cents_to_usd(cents: int) -> str:
    cents = int(cents)
    return f"{cents // 100}.{cents % 100:02d}"


def normalize_evidence(values: list[str] | None, *, required: bool) -> list[str]:
    cleaned: list[str] = []
    for raw in values or []:
        value = (raw or "").strip()
        if not value:
            continue
        if len(value) > 2000:
            raise ValidationError("Evidence links must be 2,000 characters or fewer.")
        parsed = urlsplit(value)
        if parsed.scheme.lower() != "https" or not parsed.hostname:
            raise ValidationError("Evidence must use an https:// URL.")
        if value not in cleaned:
            cleaned.append(value)
    if len(cleaned) > 20:
        raise ValidationError("At most 20 evidence links may be recorded at once.")
    if required and not cleaned:
        raise ValidationError("At least one evidence link is required.")
    return cleaned


class WorkService:
    def __init__(
        self,
        db_path: str | Path,
        queue_max: int = 20,
        verifier: GitHubVerifier | Callable[[str], PRSnapshot] | None = None,
        provider_actor: str = "provider",
    ):
        self.db_path = Path(db_path)
        self.queue_max = int(queue_max)
        if self.queue_max < 1 or self.queue_max > 20:
            raise ValueError("queue_max must be between 1 and 20")
        init_db(self.db_path)
        self.verifier = verifier or GitHubVerifier()
        actor = (provider_actor or "provider").strip()
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:@/-]{0,127}", actor):
            raise ValueError("provider_actor must be a stable 1-128 character identifier")
        self.provider_actor = actor

    def _verify_pr(self, url: str) -> PRSnapshot:
        verifier = self.verifier
        if callable(verifier) and not hasattr(verifier, "verify"):
            return verifier(url)
        return verifier.verify(url)  # type: ignore[union-attr]

    def public_status(self) -> dict[str, Any]:
        with connect(self.db_path) as conn:
            occupied = int(
                conn.execute("SELECT COUNT(*) FROM submissions WHERE terminal = 0").fetchone()[0]
            )
            latest = conn.execute(
                "SELECT updated_at FROM submissions ORDER BY updated_at DESC LIMIT 1"
            ).fetchone()
        available = max(0, self.queue_max - occupied)
        return {
            "queue": {
                "max": self.queue_max,
                "occupied": occupied,
                "available": available,
                "accepting": available > 0,
            },
            "updated_at": latest["updated_at"] if latest else utc_now(),
        }

    def submit(
        self,
        work_kind: str,
        bid_usd: Any,
        outcome: str,
        *,
        attested: bool = False,
        pr_url: str = "",
        idea_title: str = "",
        context_url: str = "",
    ) -> dict[str, Any]:
        if attested is not True:
            raise ValidationError("Submission requires the authorization and data-use attestation.")
        if str(work_kind).strip().lower().startswith("https://github.com/"):
            # Convenience form for programmatic PR callers: submit(pr_url, value, outcome).
            if not pr_url:
                pr_url = str(work_kind)
            kind = "github_pr"
        else:
            kind = normalize_work_kind(work_kind)
        outcome = (outcome or "").strip()
        if len(outcome) < 12:
            raise ValidationError("Describe the outcome you want in at least 12 characters.")
        if len(outcome) > 4000:
            raise ValidationError("Outcome must be 4,000 characters or fewer.")
        bid_cents = parse_bid_usd(bid_usd)
        context_url = normalize_optional_https(context_url)

        if kind == "github_pr":
            snapshot = self._verify_pr(pr_url)
            idea_title = ""
            source_key = snapshot.pr_url
            fields = {
                "pr_url": snapshot.pr_url,
                "repo_owner": snapshot.repo_owner,
                "repo_name": snapshot.repo_name,
                "pr_number": snapshot.pr_number,
                "pr_title": snapshot.title,
                "pr_author": snapshot.author_login,
                "head_sha": snapshot.head_sha,
                "head_ref": snapshot.head_ref,
                "base_ref": snapshot.base_ref,
                "additions": snapshot.additions,
                "deletions": snapshot.deletions,
                "changed_files": snapshot.changed_files,
                "commits": snapshot.commits,
                "size_band": snapshot.size_band,
            }
        else:
            idea_title = (idea_title or "").strip()
            if len(idea_title) < 8 or len(idea_title) > 160:
                raise ValidationError("Idea title must be between 8 and 160 characters.")
            source_key = None
            fields = {
                "pr_url": "", "repo_owner": "", "repo_name": "", "pr_number": 0,
                "pr_title": "", "pr_author": "", "head_sha": "", "head_ref": "",
                "base_ref": "", "additions": 0, "deletions": 0, "changed_files": 0,
                "commits": 0, "size_band": "idea",
            }

        token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
        public_id = "OWP-" + secrets.token_hex(12).upper()
        now = utc_now()

        conn = connect(self.db_path)
        try:
            conn.execute("BEGIN IMMEDIATE")
            occupied = int(conn.execute("SELECT COUNT(*) FROM submissions WHERE terminal = 0").fetchone()[0])
            if occupied >= self.queue_max:
                raise QueueFull(f"The field-lab queue is full ({self.queue_max}/{self.queue_max}).")
            try:
                cur = conn.execute(
                    """INSERT INTO submissions (
                        public_id, token_hash, work_kind, source_key, idea_title, context_url,
                        pr_url, repo_owner, repo_name, pr_number, pr_title, pr_author, head_sha,
                        head_ref, base_ref, additions, deletions, changed_files, commits, size_band,
                        bid_cents, outcome, state, provider_decision, validation_status, attempt_number,
                        terminal, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, NULL, 0, 0, ?, ?)""",
                    (
                        public_id, token_hash, kind, source_key, idea_title, context_url,
                        fields["pr_url"], fields["repo_owner"], fields["repo_name"], fields["pr_number"],
                        fields["pr_title"], fields["pr_author"], fields["head_sha"], fields["head_ref"],
                        fields["base_ref"], fields["additions"], fields["deletions"],
                        fields["changed_files"], fields["commits"], fields["size_band"],
                        bid_cents, outcome, "proposed", now, now,
                    ),
                )
            except sqlite3.IntegrityError as exc:
                if kind == "github_pr":
                    existing = conn.execute(
                        "SELECT 1 FROM submissions WHERE source_key = ? AND terminal = 0",
                        (source_key,),
                    ).fetchone()
                    if existing:
                        raise DuplicateSubmission("That PR is already active in the field lab.") from exc
                raise
            submission_id = int(cur.lastrowid)
            source_payload: dict[str, Any]
            if kind == "github_pr":
                source_payload = {
                    "kind": kind, "pr_url": fields["pr_url"], "head_sha": fields["head_sha"],
                    "size": {"band": fields["size_band"], "additions": fields["additions"],
                             "deletions": fields["deletions"], "changed_files": fields["changed_files"]},
                }
            else:
                source_payload = {"kind": kind, "title": idea_title, "context_url": context_url}
            append_event(
                conn, submission_id, "work.requested", "customer",
                {
                    "source": source_payload, "value_signal_cents": bid_cents, "outcome": outcome,
                    "intake_notice_version": INTAKE_NOTICE_VERSION,
                    "authorization_and_data_use_attested": True,
                },
            )
            conn.execute("COMMIT")
        except Exception:
            try:
                conn.execute("ROLLBACK")
            except sqlite3.OperationalError:
                pass
            raise
        finally:
            conn.close()

        return {
            "work_ref": public_id,
            "claim_token": token,
            "work": self._public_work_by_id(public_id, token),
            "queue": self.public_status()["queue"],
        }

    def _row_for_ref(self, conn, public_id: str):
        row = conn.execute(
            "SELECT * FROM submissions WHERE public_id = ?", (public_id,)
        ).fetchone()
        if not row:
            raise NotFound("Work item not found.")
        return row

    def _authorize(self, row, token: str) -> None:
        supplied = hashlib.sha256((token or "").encode("utf-8")).hexdigest()
        if not hmac.compare_digest(supplied, row["token_hash"]):
            raise Unauthorized("Invalid claim token.")

    def _public_work_by_id(self, public_id: str, token: str) -> dict[str, Any]:
        with connect(self.db_path) as conn:
            row = self._row_for_ref(conn, public_id)
            self._authorize(row, token)
            return self._work_projection(conn, row)

    def get_work(self, public_id: str, token: str) -> dict[str, Any]:
        return self._public_work_by_id(public_id, token)

    def _work_projection(self, conn, row) -> dict[str, Any]:
        events = conn.execute(
            """SELECT seq, event_type, actor, payload_json, created_at, prev_hash, event_hash
               FROM events WHERE submission_id = ? ORDER BY seq""",
            (row["id"],),
        ).fetchall()
        questions = conn.execute(
            """SELECT id, text, options_json, evidence_json, answer_json, status, created_at, answered_at
               FROM questions WHERE submission_id = ? ORDER BY created_at""",
            (row["id"],),
        ).fetchall()
        chain_ok, chain_detail = verify_event_chain(conn, row["id"])
        source: dict[str, Any]
        if row["work_kind"] == "github_pr":
            source = {
                "kind": "github_pr", "url": row["pr_url"],
                "repo": f"{row['repo_owner']}/{row['repo_name']}", "number": row["pr_number"],
                "title": row["pr_title"], "author": row["pr_author"], "head_sha": row["head_sha"],
                "head_ref": row["head_ref"], "base_ref": row["base_ref"],
                "additions": row["additions"], "deletions": row["deletions"],
                "changed_files": row["changed_files"], "commits": row["commits"],
                "size_band": row["size_band"],
            }
        else:
            source = {"kind": "idea", "title": row["idea_title"], "context_url": row["context_url"]}
        projection = {
            "profile": PROFILE, "work_ref": row["public_id"], "state": row["state"],
            "provider_decision": row["provider_decision"], "validation_status": row["validation_status"],
            "attempt_number": row["attempt_number"], "created_at": row["created_at"],
            "updated_at": row["updated_at"],
            "integrity": {"chain_verified": chain_ok, "detail": chain_detail},
            "source": source,
            "value_signal_usd": cents_to_usd(row["bid_cents"]),
            "simulated_bid_usd": cents_to_usd(row["bid_cents"]),
            "outcome": row["outcome"],
            "events": [
                {"seq": e["seq"], "type": e["event_type"], "actor": e["actor"],
                 "payload": json.loads(e["payload_json"]), "created_at": e["created_at"],
                 "prev_hash": e["prev_hash"], "event_hash": e["event_hash"]}
                for e in events
            ],
            "questions": [
                {"id": q["id"], "text": q["text"], "options": json.loads(q["options_json"]),
                 "evidence": json.loads(q["evidence_json"]),
                 "answer": json.loads(q["answer_json"]) if q["answer_json"] else None,
                 "status": q["status"], "created_at": q["created_at"], "answered_at": q["answered_at"]}
                for q in questions
            ],
        }
        if row["work_kind"] == "github_pr":
            projection["pr"] = source
        return projection

    def admin_queue(self, include_terminal: bool = False) -> list[dict[str, Any]]:
        clause = "" if include_terminal else "WHERE terminal = 0"
        with connect(self.db_path) as conn:
            rows = conn.execute(
                f"""SELECT public_id, work_kind, idea_title, context_url, pr_url, pr_title, pr_author,
                           size_band, additions, deletions, changed_files, bid_cents, outcome, state,
                           provider_decision, validation_status, attempt_number, created_at, updated_at
                    FROM submissions {clause} ORDER BY id"""
            ).fetchall()
        result = []
        for r in rows:
            item = {k: r[k] for k in r.keys() if k != "bid_cents"}
            item["value_signal_usd"] = cents_to_usd(r["bid_cents"])
            item["bid_usd"] = item["value_signal_usd"]
            item["source_label"] = (
                r["pr_url"].removeprefix("https://github.com/")
                if r["work_kind"] == "github_pr" else r["idea_title"]
            )
            result.append(item)
        return result

    def _admin_transition(
        self,
        public_id: str,
        expected: set[str],
        new_state: str,
        event_type: str,
        payload: dict[str, Any],
        updates: dict[str, Any] | None = None,
        terminal: bool | None = None,
        actor: str | None = None,
    ) -> dict[str, Any]:
        updates = updates or {}
        actor = actor or self.provider_actor
        conn = connect(self.db_path)
        try:
            conn.execute("BEGIN IMMEDIATE")
            row = self._row_for_ref(conn, public_id)
            if row["state"] not in expected:
                raise InvalidTransition(
                    f"{public_id} is {row['state']}; expected one of {sorted(expected)}."
                )
            now = utc_now()
            fields = {"state": new_state, "updated_at": now, **updates}
            if terminal is not None:
                fields["terminal"] = 1 if terminal else 0
            assignments = ", ".join(f"{k} = ?" for k in fields)
            conn.execute(
                f"UPDATE submissions SET {assignments} WHERE id = ?",
                (*fields.values(), row["id"]),
            )
            append_event(conn, row["id"], event_type, actor, payload)
            conn.execute("COMMIT")
            row = self._row_for_ref(conn, public_id)
            return self._work_projection(conn, row)
        except Exception:
            try:
                conn.execute("ROLLBACK")
            except sqlite3.OperationalError:
                pass
            raise
        finally:
            conn.close()

    def accept(self, public_id: str, note: str = "") -> dict[str, Any]:
        return self._admin_transition(
            public_id,
            {"proposed"},
            "todo",
            "provider.accepted",
            {"note": note},
            updates={"provider_decision": "ACCEPT"},
        )

    def pass_work(self, public_id: str, reason: str) -> dict[str, Any]:
        reason = (reason or "").strip()
        if len(reason) < 3:
            raise ValidationError("PASS requires a short reason.")
        return self._admin_transition(
            public_id,
            {"proposed"},
            "cancelled",
            "provider.passed",
            {"reason": reason},
            updates={"provider_decision": "PASS"},
            terminal=True,
        )

    def start(self, public_id: str) -> dict[str, Any]:
        with connect(self.db_path) as pre:
            pre_row = self._row_for_ref(pre, public_id)
            kind = pre_row["work_kind"]
            pr_url = pre_row["pr_url"]

        snapshot = self._verify_pr(pr_url) if kind == "github_pr" else None
        conn = connect(self.db_path)
        try:
            conn.execute("BEGIN IMMEDIATE")
            row = self._row_for_ref(conn, public_id)
            if row["state"] != "todo":
                raise InvalidTransition(f"{public_id} must be todo before an attempt starts.")
            now = utc_now()
            source_start: dict[str, Any] = {"kind": kind}
            if snapshot is not None:
                snapshot_fields = {
                    "pr_title": snapshot.title, "pr_author": snapshot.author_login,
                    "head_sha": snapshot.head_sha, "head_ref": snapshot.head_ref,
                    "base_ref": snapshot.base_ref, "additions": snapshot.additions,
                    "deletions": snapshot.deletions, "changed_files": snapshot.changed_files,
                    "commits": snapshot.commits, "size_band": snapshot.size_band,
                }
                changed = any(row[key] != value for key, value in snapshot_fields.items())
                intake_head = row["head_sha"]
                if changed:
                    assignments = ", ".join(f"{key} = ?" for key in snapshot_fields)
                    conn.execute(
                        f"UPDATE submissions SET {assignments}, updated_at = ? WHERE id = ?",
                        (*snapshot_fields.values(), now, row["id"]),
                    )
                    append_event(
                        conn, row["id"], "pr.snapshot_refreshed", self.provider_actor,
                        {"previous_head_sha": intake_head, "head_sha": snapshot.head_sha,
                         "size_band": snapshot.size_band, "changed_files": snapshot.changed_files,
                         "churn": snapshot.additions + snapshot.deletions},
                    )
                    row = self._row_for_ref(conn, public_id)
                source_start.update({"head_sha_at_intake": intake_head, "head_sha_at_start": row["head_sha"]})
            else:
                source_start.update({"idea_title": row["idea_title"], "context_url": row["context_url"]})

            attempt = int(row["attempt_number"]) + 1
            conn.execute(
                """UPDATE submissions SET state = 'in_progress', attempt_number = ?,
                   validation_status = NULL, updated_at = ? WHERE id = ?""",
                (attempt, now, row["id"]),
            )
            attempt_payload = {"attempt_number": attempt, "source": source_start}
            if kind == "github_pr":
                attempt_payload.update({
                    "head_sha_at_intake": source_start.get("head_sha_at_intake", ""),
                    "head_sha_at_start": source_start.get("head_sha_at_start", ""),
                })
            append_event(conn, row["id"], "attempt.started", self.provider_actor, attempt_payload)
            conn.execute("COMMIT")
            row = self._row_for_ref(conn, public_id)
            return self._work_projection(conn, row)
        except Exception:
            try:
                conn.execute("ROLLBACK")
            except sqlite3.OperationalError:
                pass
            raise
        finally:
            conn.close()

    def ask(
        self,
        public_id: str,
        text: str,
        options: list[str],
        evidence: list[str] | None = None,
    ) -> dict[str, Any]:
        text = (text or "").strip()
        options = [o.strip() for o in options if o and o.strip()]
        evidence = normalize_evidence(evidence, required=False)
        if len(text) < 5 or len(text) > 2000:
            raise ValidationError("Question text must be between 5 and 2,000 characters.")
        if len(options) < 2 or len(options) > 12:
            raise ValidationError("Questions require between 2 and 12 options.")
        if any(len(option) < 1 or len(option) > 500 for option in options):
            raise ValidationError("Question options must be 500 characters or fewer.")
        if len(set(options)) != len(options):
            raise ValidationError("Question options must be distinct.")
        qid = "Q-" + secrets.token_hex(8).upper()

        conn = connect(self.db_path)
        try:
            conn.execute("BEGIN IMMEDIATE")
            row = self._row_for_ref(conn, public_id)
            if row["state"] != "in_progress":
                raise InvalidTransition("Questions can be asked only while work is in progress.")
            now = utc_now()
            conn.execute(
                """INSERT INTO questions
                (id, submission_id, text, options_json, evidence_json, answer_json, status, created_at, answered_at)
                VALUES (?, ?, ?, ?, ?, NULL, 'open', ?, NULL)""",
                (qid, row["id"], text, json.dumps(options), json.dumps(evidence), now),
            )
            conn.execute(
                "UPDATE submissions SET state = 'parked', updated_at = ? WHERE id = ?",
                (now, row["id"]),
            )
            append_event(
                conn,
                row["id"],
                "question.asked",
                self.provider_actor,
                {"question_id": qid, "text": text, "options": options, "evidence": evidence},
            )
            conn.execute("COMMIT")
            row = self._row_for_ref(conn, public_id)
            return self._work_projection(conn, row)
        except Exception:
            try:
                conn.execute("ROLLBACK")
            except sqlite3.OperationalError:
                pass
            raise
        finally:
            conn.close()

    def answer(self, public_id: str, token: str, question_id: str, option: str, note: str = ""):
        conn = connect(self.db_path)
        try:
            conn.execute("BEGIN IMMEDIATE")
            row = self._row_for_ref(conn, public_id)
            self._authorize(row, token)
            if row["state"] != "parked":
                raise InvalidTransition("This work item is not waiting on a question.")
            question = conn.execute(
                "SELECT * FROM questions WHERE id = ? AND submission_id = ?",
                (question_id, row["id"]),
            ).fetchone()
            if not question or question["status"] != "open":
                raise InvalidTransition("That question is not open.")
            options = json.loads(question["options_json"])
            if option not in options:
                raise ValidationError("Answer must select one of the offered options.")
            answer = {"option": option, "note": (note or "").strip()[:2000]}
            now = utc_now()
            conn.execute(
                """UPDATE questions SET answer_json = ?, status = 'answered', answered_at = ?
                   WHERE id = ?""",
                (json.dumps(answer, sort_keys=True), now, question_id),
            )
            conn.execute(
                "UPDATE submissions SET state = 'in_progress', updated_at = ? WHERE id = ?",
                (now, row["id"]),
            )
            append_event(
                conn,
                row["id"],
                "question.answered",
                "customer",
                {"question_id": question_id, **answer},
            )
            conn.execute("COMMIT")
            row = self._row_for_ref(conn, public_id)
            return self._work_projection(conn, row)
        except Exception:
            try:
                conn.execute("ROLLBACK")
            except sqlite3.OperationalError:
                pass
            raise
        finally:
            conn.close()

    def deliver(self, public_id: str, summary: str, evidence: list[str]) -> dict[str, Any]:
        summary = (summary or "").strip()
        evidence = normalize_evidence(evidence, required=True)
        if len(summary) < 5 or len(summary) > 4000:
            raise ValidationError("Delivery summary must be between 5 and 4,000 characters.")
        return self._admin_transition(
            public_id,
            {"in_progress"},
            "review",
            "delivery.submitted",
            {"summary": summary, "evidence": evidence},
            updates={"validation_status": None},
        )

    def validate_delivery(
        self,
        public_id: str,
        result: str,
        evidence: list[str],
        note: str = "",
        validator: str = "",
    ) -> dict[str, Any]:
        result = result.lower().strip()
        if result not in {"valid", "invalid"}:
            raise ValidationError("Validation result must be valid or invalid.")
        evidence = normalize_evidence(evidence, required=True)
        validator = (validator or "").strip()
        if len(validator) < 2 or len(validator) > 120:
            raise ValidationError("Validation requires a named validator label (2-120 characters).")
        note = (note or "").strip()[:2000]
        new_state = "review" if result == "valid" else "in_progress"
        return self._admin_transition(
            public_id,
            {"review"},
            new_state,
            "validation.recorded",
            {"result": result, "validator": validator, "evidence": evidence, "note": note},
            updates={"validation_status": result},
            actor=f"validator:{validator}",
        )

    def disposition(
        self, public_id: str, token: str, action: str, note: str = ""
    ) -> dict[str, Any]:
        action = action.lower().strip()
        if action not in {"approve", "steer", "reject"}:
            raise ValidationError("Disposition must be approve, steer, or reject.")
        note = (note or "").strip()[:2000]
        if action in {"steer", "reject"} and len(note) < 5:
            raise ValidationError(f"{action.capitalize()} requires a short reason or instruction.")

        conn = connect(self.db_path)
        try:
            conn.execute("BEGIN IMMEDIATE")
            row = self._row_for_ref(conn, public_id)
            self._authorize(row, token)
            if row["state"] != "review" or row["validation_status"] != "valid":
                raise InvalidTransition("A valid delivery must be recorded before disposition.")
            now = utc_now()
            if action == "approve":
                state, terminal = "completed", 1
                event = "customer.approved"
            elif action == "steer":
                state, terminal = "todo", 0
                event = "customer.steered"
            else:
                state, terminal = "cancelled", 1
                event = "customer.rejected"
            conn.execute(
                """UPDATE submissions SET state = ?, terminal = ?, validation_status = NULL,
                   updated_at = ? WHERE id = ?""",
                (state, terminal, now, row["id"]),
            )
            append_event(
                conn,
                row["id"],
                event,
                "customer",
                {"note": note, "attempt_number": row["attempt_number"]},
            )
            conn.execute("COMMIT")
            row = self._row_for_ref(conn, public_id)
            return self._work_projection(conn, row)
        except Exception:
            try:
                conn.execute("ROLLBACK")
            except sqlite3.OperationalError:
                pass
            raise
        finally:
            conn.close()

    def verify_chain(self, public_id: str) -> tuple[bool, str]:
        with connect(self.db_path) as conn:
            row = self._row_for_ref(conn, public_id)
            return verify_event_chain(conn, row["id"])

    def export_handoff(self, public_id: str) -> dict[str, Any]:
        """Portable, token-free snapshot another provider can ingest."""
        with connect(self.db_path) as conn:
            row = self._row_for_ref(conn, public_id)
            projection = self._work_projection(conn, row)
            ok, detail = verify_event_chain(conn, row["id"])
        return {
            "profile": PROFILE,
            "spec_reference": "Open Work Protocol 1.0-rc3 development-candidate concepts; field-lab profile, not conformance claim",
            "exported_at": utc_now(), "chain_verified": ok, "chain_detail": detail, "work": projection,
        }

    def customer_handoff(self, public_id: str, token: str) -> dict[str, Any]:
        with connect(self.db_path) as conn:
            row = self._row_for_ref(conn, public_id)
            self._authorize(row, token)
        return self.export_handoff(public_id)

    def export_bids_csv(self) -> str:
        out = io.StringIO()
        writer = csv.writer(out)
        writer.writerow(["work_ref", "created_at", "work_kind", "source", "size_band",
                         "additions", "deletions", "changed_files", "commits",
                         "bid_usd", "value_signal_usd", "provider_decision", "terminal_state"])
        with connect(self.db_path) as conn:
            rows = conn.execute("SELECT * FROM submissions ORDER BY id").fetchall()
        for r in rows:
            source = (f"{r['repo_owner']}/{r['repo_name']}#{r['pr_number']}"
                      if r["work_kind"] == "github_pr" else r["idea_title"])
            writer.writerow([r["public_id"], r["created_at"], r["work_kind"], source, r["size_band"],
                             r["additions"], r["deletions"], r["changed_files"], r["commits"],
                             cents_to_usd(r["bid_cents"]), cents_to_usd(r["bid_cents"]), r["provider_decision"] or "",
                             r["state"] if r["terminal"] else ""])
        return out.getvalue()

    def export_research_jsonl(self) -> str:
        """Private research export pairing work request, value signal, source, and outcome."""
        with connect(self.db_path) as conn:
            rows = conn.execute("SELECT * FROM submissions ORDER BY id").fetchall()
        records = []
        for r in rows:
            source = ({
                "kind": "github_pr", "pr_url": r["pr_url"],
                "repo": f"{r['repo_owner']}/{r['repo_name']}", "pr_number": r["pr_number"],
                "title": r["pr_title"], "author": r["pr_author"], "head_sha": r["head_sha"],
                "size_band": r["size_band"], "additions": r["additions"], "deletions": r["deletions"],
                "changed_files": r["changed_files"], "commits": r["commits"],
            } if r["work_kind"] == "github_pr" else {
                "kind": "idea", "title": r["idea_title"], "context_url": r["context_url"]
            })
            records.append({
                "work_ref": r["public_id"], "created_at": r["created_at"], "source": source,
                "value_signal_usd": cents_to_usd(r["bid_cents"]),
                "bid_usd": cents_to_usd(r["bid_cents"]),
                "requested_outcome": r["outcome"], "provider_decision": r["provider_decision"],
                "attempts": r["attempt_number"], "state": r["state"], "terminal": bool(r["terminal"]),
            })
        return "".join(json.dumps(record, sort_keys=True, ensure_ascii=False) + "\n" for record in records)

    def backup_database(self, out_path: str | Path) -> Path:
        out = Path(out_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        if out.resolve() == self.db_path.resolve():
            raise ValidationError("Backup destination must differ from the live database.")

        # Reserve the destination atomically so two operator processes cannot race
        # past an existence check and overwrite one another's backup.
        try:
            fd = os.open(out, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        except FileExistsError as exc:
            raise ValidationError("Backup destination already exists; refusing to overwrite it.") from exc
        os.close(fd)

        src = connect(self.db_path)
        dest = None
        try:
            dest = sqlite3.connect(out)
            src.backup(dest)
        except Exception:
            try:
                out.unlink()
            except OSError:
                pass
            raise
        finally:
            if dest is not None:
                dest.close()
            src.close()
        try:
            out.chmod(0o600)
        except OSError:
            pass
        return out

    def verify_all(self) -> dict[str, Any]:
        with connect(self.db_path) as conn:
            quick = conn.execute("PRAGMA quick_check").fetchone()[0]
            rows = conn.execute("SELECT id, public_id FROM submissions ORDER BY id").fetchall()
            failures = []
            for row in rows:
                ok, detail = verify_event_chain(conn, row["id"])
                if not ok:
                    failures.append({"work_ref": row["public_id"], "detail": detail})
        return {
            "ok": quick == "ok" and not failures,
            "sqlite_quick_check": quick,
            "work_items_checked": len(rows),
            "chain_failures": failures,
        }

