from __future__ import annotations

import contextlib
import io
import json
import os
import stat
import tempfile
import threading
import time
import unittest
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from unittest.mock import patch

from owp_field_lab import admin
from owp_field_lab.db import connect
from owp_field_lab.errors import (
    DuplicateSubmission,
    InvalidTransition,
    QueueFull,
    Unauthorized,
    ValidationError,
)
from owp_field_lab.github import GitHubVerifier, PRSnapshot, parse_pr_url
from owp_field_lab.server import create_server
from owp_field_lab.service import WorkService, parse_bid_usd


def snapshot(url: str, churn: int = 42, files: int = 2) -> PRSnapshot:
    owner, repo, number, canonical = parse_pr_url(url)
    return PRSnapshot(
        pr_url=canonical,
        repo_owner=owner,
        repo_name=repo,
        pr_number=number,
        title=f"PR {number}",
        author_login="submitter",
        state="open",
        draft=False,
        head_sha=f"deadbeef{number}",
        head_ref=f"feature-{number}",
        base_ref="main",
        additions=churn,
        deletions=0,
        changed_files=files,
        commits=1,
    )


class FakeVerifier:
    def __init__(self):
        self.overrides: dict[int, dict] = {}

    def verify(self, url: str) -> PRSnapshot:
        _, _, number, _ = parse_pr_url(url)
        base = snapshot(url, churn=10000, files=100) if number == 999 else snapshot(url)
        if number in self.overrides:
            base = replace(base, **self.overrides[number])
        return base


class ServiceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Path(self.tmp.name) / "data" / "field-lab.sqlite3"
        self.verifier = FakeVerifier()
        self.svc = WorkService(self.db, queue_max=20, verifier=self.verifier)

    def tearDown(self):
        self.tmp.cleanup()

    def submit(self, number=1, bid="250.00", outcome="Make this production-ready and prove the tests pass."):
        return self.svc.submit(
            f"https://github.com/example/project/pull/{number}",
            bid,
            outcome,
            attested=True,
        )

    def deliver_and_validate(self, ref: str):
        self.svc.deliver(ref, "Implementation and tests complete.", ["https://example.test/commit"])
        return self.svc.validate_delivery(
            ref,
            "valid",
            ["https://example.test/ci"],
            validator="fresh-clone-ci",
        )

    def test_exact_usd_bid_is_integer_cents_and_rejects_non_money(self):
        self.assertEqual(parse_bid_usd("123.45"), 12345)
        self.assertEqual(parse_bid_usd("1"), 100)
        for bad in ("1.001", "0", "-1", "NaN", "Infinity", "1000000.01"):
            with self.subTest(bad=bad), self.assertRaises(ValidationError):
                parse_bid_usd(bad)

    def test_pr_url_parser_canonicalizes_identity_and_rejects_unsafe_forms(self):
        self.assertEqual(
            parse_pr_url("https://github.com/Org/Repo/pull/42/files?diff=split"),
            ("org", "repo", 42, "https://github.com/org/repo/pull/42"),
        )
        for bad in (
            "http://github.com/Org/Repo/pull/42",
            "https://evil.example/Org/Repo/pull/42",
            "https://github.com@evil.example/Org/Repo/pull/42",
            "https://github.com:443/Org/Repo/pull/42",
            "https://github.com/Org/Repo/issues/42",
        ):
            with self.subTest(bad=bad), self.assertRaises(ValidationError):
                parse_pr_url(bad)

    def test_queue_max_is_hard_capped_at_twenty(self):
        with self.assertRaises(ValueError):
            WorkService(Path(self.tmp.name) / "too-big.sqlite3", queue_max=21, verifier=self.verifier)

    def test_submission_requires_authorization_and_data_use_attestation(self):
        with self.assertRaises(ValidationError):
            self.svc.submit(
                "https://github.com/example/project/pull/1",
                "10",
                "Please make this production ready.",
                attested=False,
            )

    def test_submit_records_real_pr_snapshot_hashes_token_and_tightens_db_permissions(self):
        result = self.submit()
        work = result["work"]
        self.assertEqual(work["simulated_bid_usd"], "250.00")
        self.assertEqual(work["pr"]["head_sha"], "deadbeef1")
        self.assertGreaterEqual(len(result["work_ref"]), 20)
        self.assertTrue(work["integrity"]["chain_verified"])
        with connect(self.db) as conn:
            row = conn.execute("SELECT token_hash FROM submissions").fetchone()
            self.assertNotEqual(row["token_hash"], result["claim_token"])
            self.assertEqual(len(row["token_hash"]), 64)
            event = json.loads(conn.execute("SELECT payload_json FROM events WHERE seq = 1").fetchone()[0])
            self.assertTrue(event["authorization_and_data_use_attested"])
        self.assertEqual(stat.S_IMODE(os.stat(self.db).st_mode), 0o600)

    def test_public_status_exposes_capacity_not_private_queue(self):
        self.submit()
        status = self.svc.public_status()
        self.assertEqual(status["queue"]["occupied"], 1)
        self.assertNotIn("submissions", status)
        self.assertNotIn("bid", json.dumps(status).lower())
        private = self.svc.admin_queue()
        self.assertEqual(private[0]["bid_usd"], "250.00")

    def test_private_queue_enforces_exact_max_20(self):
        for i in range(1, 21):
            self.submit(i)
        self.assertEqual(self.svc.public_status()["queue"]["occupied"], 20)
        with self.assertRaises(QueueFull):
            self.submit(21)

    def test_concurrent_submissions_cannot_overfill_20_slots(self):
        def try_one(i):
            try:
                self.submit(i)
                return "accepted"
            except QueueFull:
                return "full"

        with ThreadPoolExecutor(max_workers=25) as pool:
            results = list(pool.map(try_one, range(1, 26)))
        self.assertEqual(results.count("accepted"), 20)
        self.assertEqual(results.count("full"), 5)
        self.assertEqual(self.svc.public_status()["queue"]["occupied"], 20)

    def test_concurrent_duplicate_pr_submissions_consume_only_one_slot(self):
        def submit_same(_):
            try:
                self.svc.submit(
                    "https://github.com/example/project/pull/777",
                    "50.00",
                    "Make this exact PR production-ready and verify the result.",
                    attested=True,
                )
                return "accepted"
            except DuplicateSubmission:
                return "duplicate"

        with ThreadPoolExecutor(max_workers=12) as pool:
            results = list(pool.map(submit_same, range(12)))
        self.assertEqual(results.count("accepted"), 1)
        self.assertEqual(results.count("duplicate"), 11)
        self.assertEqual(self.svc.public_status()["queue"]["occupied"], 1)


    def test_private_queue_is_received_order_not_bid_ranked(self):
        low = self.submit(1, "1.00")
        high = self.submit(2, "999999.00")
        queue = self.svc.admin_queue()
        self.assertEqual([row["public_id"] for row in queue], [low["work_ref"], high["work_ref"]])

    def test_small_and_very_large_prs_are_both_allowed(self):
        small = self.submit(1)
        giant = self.submit(999)
        self.assertEqual(small["work"]["pr"]["size_band"], "small")
        self.assertEqual(giant["work"]["pr"]["size_band"], "very-large")

    def test_queue_and_event_state_survive_service_restart(self):
        result = self.submit(1)
        self.svc.accept(result["work_ref"])
        restarted = WorkService(self.db, queue_max=20, verifier=self.verifier)
        self.assertEqual(restarted.public_status()["queue"]["occupied"], 1)
        work = restarted.export_handoff(result["work_ref"])["work"]
        self.assertEqual(work["state"], "todo")
        self.assertEqual([e["type"] for e in work["events"]], ["work.requested", "provider.accepted"])

    def test_provider_pass_is_terminal_and_reopens_capacity(self):
        first = self.submit(1)
        self.svc.pass_work(first["work_ref"], "Agent stack cannot safely meet the requested spec.")
        self.assertEqual(self.svc.public_status()["queue"]["occupied"], 0)
        handoff = self.svc.export_handoff(first["work_ref"])
        self.assertEqual(handoff["work"]["provider_decision"], "PASS")
        self.submit(2)

    def test_case_variant_duplicate_pr_cannot_consume_another_slot(self):
        self.submit(1)
        with self.assertRaises(DuplicateSubmission):
            self.svc.submit(
                "https://github.com/EXAMPLE/PROJECT/pull/1/files",
                "99",
                "Make this production ready and verify it.",
                attested=True,
            )

    def test_claim_token_is_required_for_customer_view(self):
        result = self.submit()
        with self.assertRaises(Unauthorized):
            self.svc.get_work(result["work_ref"], "wrong")

    def test_configurable_provider_actor_is_recorded(self):
        custom = WorkService(self.db, verifier=self.verifier, provider_actor="provider:acme-lab")
        result = custom.submit(
            "idea", "25.00", "Build a small example and return durable evidence.",
            attested=True, idea_title="Configurable provider actor example",
        )
        ref = result["work_ref"]
        custom.accept(ref, "Accepted by configured provider.")
        custom.start(ref)
        with connect(self.db) as conn:
            actors = [r[0] for r in conn.execute(
                "SELECT actor FROM events WHERE submission_id = (SELECT id FROM submissions WHERE public_id = ?) ORDER BY seq",
                (ref,),
            ).fetchall()]
        self.assertIn("provider:acme-lab", actors)

    def test_accept_start_question_answer_flow(self):
        result = self.submit()
        ref, token = result["work_ref"], result["claim_token"]
        self.assertEqual(self.svc.accept(ref)["state"], "todo")
        self.assertEqual(self.svc.start(ref)["attempt_number"], 1)
        asked = self.svc.ask(
            ref,
            "Which compatibility target should win?",
            ["Preserve old API", "Prefer new API"],
            ["https://example.test/evidence"],
        )
        self.assertEqual(asked["state"], "parked")
        q = asked["questions"][0]
        answered = self.svc.answer(ref, token, q["id"], "Preserve old API", "Compatibility wins.")
        self.assertEqual(answered["state"], "in_progress")
        self.assertEqual(answered["questions"][0]["status"], "answered")

    def test_attempt_start_refreshes_moved_pr_head_before_work_begins(self):
        result = self.submit(1)
        ref = result["work_ref"]
        self.svc.accept(ref)
        self.verifier.overrides[1] = {
            "head_sha": "cafebabefeed",
            "additions": 400,
            "changed_files": 11,
        }
        started = self.svc.start(ref)
        self.assertEqual(started["pr"]["head_sha"], "cafebabefeed")
        types = [event["type"] for event in started["events"]]
        self.assertEqual(types[-2:], ["pr.snapshot_refreshed", "attempt.started"])
        self.assertEqual(started["events"][-1]["payload"]["head_sha_at_start"], "cafebabefeed")

    def test_question_requires_distinct_options_and_https_evidence(self):
        result = self.submit()
        ref = result["work_ref"]
        self.svc.accept(ref)
        self.svc.start(ref)
        with self.assertRaises(ValidationError):
            self.svc.ask(ref, "Choose?", ["Only one"], [])
        with self.assertRaises(ValidationError):
            self.svc.ask(ref, "Choose?", ["A", "A"], [])
        with self.assertRaises(ValidationError):
            self.svc.ask(ref, "Choose?", ["A", "B"], ["javascript:alert(1)"])

    def test_delivery_requires_https_evidence(self):
        result = self.submit()
        ref = result["work_ref"]
        self.svc.accept(ref)
        self.svc.start(ref)
        for evidence in ([], ["file:///tmp/proof"], ["http://example.test/proof"]):
            with self.subTest(evidence=evidence), self.assertRaises(ValidationError):
                self.svc.deliver(ref, "Done safely.", evidence)

    def test_validation_requires_named_actor_and_invalid_routes_to_repair(self):
        result = self.submit()
        ref = result["work_ref"]
        self.svc.accept(ref)
        self.svc.start(ref)
        self.svc.deliver(ref, "Implementation and tests complete.", ["https://example.test/actions"])
        with self.assertRaises(ValidationError):
            self.svc.validate_delivery(ref, "valid", ["https://example.test/ci"])
        work = self.svc.validate_delivery(
            ref,
            "invalid",
            ["https://example.test/failure"],
            "One gate failed.",
            validator="fresh-clone-ci",
        )
        self.assertEqual(work["state"], "in_progress")
        self.assertEqual(work["validation_status"], "invalid")
        self.assertEqual(work["events"][-1]["actor"], "validator:fresh-clone-ci")

    def test_valid_delivery_requires_customer_disposition(self):
        result = self.submit()
        ref, token = result["work_ref"], result["claim_token"]
        self.svc.accept(ref)
        self.svc.start(ref)
        self.deliver_and_validate(ref)
        work = self.svc.get_work(ref, token)
        self.assertEqual(work["state"], "review")
        self.assertEqual(work["validation_status"], "valid")
        approved = self.svc.disposition(ref, token, "approve", "Ship it.")
        self.assertEqual(approved["state"], "completed")
        self.assertEqual(self.svc.public_status()["queue"]["occupied"], 0)

    def test_customer_steer_requires_instruction_and_creates_another_attempt(self):
        result = self.submit()
        ref, token = result["work_ref"], result["claim_token"]
        self.svc.accept(ref)
        self.svc.start(ref)
        self.deliver_and_validate(ref)
        with self.assertRaises(ValidationError):
            self.svc.disposition(ref, token, "steer", "")
        steered = self.svc.disposition(ref, token, "steer", "Keep API compatibility.")
        self.assertEqual(steered["state"], "todo")
        restarted = self.svc.start(ref)
        self.assertEqual(restarted["attempt_number"], 2)

    def test_customer_reject_requires_reason_and_frees_slot(self):
        result = self.submit()
        ref, token = result["work_ref"], result["claim_token"]
        self.svc.accept(ref)
        self.svc.start(ref)
        self.deliver_and_validate(ref)
        with self.assertRaises(ValidationError):
            self.svc.disposition(ref, token, "reject", "no")
        rejected = self.svc.disposition(ref, token, "reject", "Public API was broken.")
        self.assertEqual(rejected["state"], "cancelled")
        self.assertEqual(self.svc.public_status()["queue"]["occupied"], 0)

    def test_hash_linked_event_chain_detects_tampering_and_projection_surfaces_warning(self):
        result = self.submit()
        ref, token = result["work_ref"], result["claim_token"]
        self.svc.accept(ref)
        self.svc.start(ref)
        self.assertTrue(self.svc.get_work(ref, token)["integrity"]["chain_verified"])
        with connect(self.db) as conn:
            conn.execute("UPDATE events SET payload_json = '{\"tampered\":true}' WHERE seq = 2")
        work = self.svc.get_work(ref, token)
        self.assertFalse(work["integrity"]["chain_verified"])
        self.assertIn("event_hash mismatch", work["integrity"]["detail"])

    def test_handoff_export_is_portable_and_contains_no_claim_secret(self):
        result = self.submit()
        exported = self.svc.export_handoff(result["work_ref"])
        raw = json.dumps(exported)
        self.assertTrue(exported["chain_verified"])
        self.assertEqual(exported["profile"], "owp-field-lab/0.1")
        self.assertNotIn(result["claim_token"], raw)
        self.assertNotIn("token_hash", raw)

    def test_bid_export_pairs_market_signal_with_pr_size(self):
        self.submit(1, "99.50")
        csv_data = self.svc.export_bids_csv()
        self.assertIn("bid_usd", csv_data)
        self.assertIn("99.50", csv_data)
        self.assertIn("size_band", csv_data)
        self.assertNotIn("Make this production-ready", csv_data)

    def test_private_research_export_pairs_value_with_requested_outcome_without_secret(self):
        result = self.submit(1, "123.45", "Preserve API behavior and repair the flaky edge case.")
        data = self.svc.export_research_jsonl()
        record = json.loads(data)
        self.assertEqual(record["bid_usd"], "123.45")
        self.assertIn("flaky edge case", record["requested_outcome"])
        self.assertNotIn(result["claim_token"], data)
        self.assertNotIn("token_hash", data)

    def test_consistent_database_backup_can_be_reopened_and_verified(self):
        result = self.submit()
        self.svc.accept(result["work_ref"])
        backup = Path(self.tmp.name) / "backup.sqlite3"
        self.svc.backup_database(backup)
        self.assertEqual(stat.S_IMODE(os.stat(backup).st_mode), 0o600)
        before = backup.read_bytes()
        with self.assertRaises(ValidationError):
            self.svc.backup_database(backup)
        self.assertEqual(backup.read_bytes(), before)
        restored = WorkService(backup, verifier=self.verifier)
        self.assertEqual(restored.public_status()["queue"]["occupied"], 1)
        self.assertTrue(restored.verify_all()["ok"])

    def test_verify_all_catches_event_tampering(self):
        result = self.submit()
        self.assertTrue(self.svc.verify_all()["ok"])
        with connect(self.db) as conn:
            conn.execute("UPDATE events SET actor = 'tampered' WHERE seq = 1")
        result = self.svc.verify_all()
        self.assertFalse(result["ok"])
        self.assertEqual(len(result["chain_failures"]), 1)

    def test_full_golden_journey(self):
        result = self.submit(7, "500")
        ref, token = result["work_ref"], result["claim_token"]
        self.svc.accept(ref, "Within current agent capability.")
        self.svc.start(ref)
        asked = self.svc.ask(ref, "Pick behavior.", ["A", "B"], ["https://example.test/spec"])
        self.svc.answer(ref, token, asked["questions"][0]["id"], "A", "Spec requires A.")
        self.svc.deliver(ref, "Finished implementation.", ["https://example.test/commit"])
        self.svc.validate_delivery(
            ref,
            "valid",
            ["https://example.test/tests"],
            validator="fresh-clone-ci",
        )
        final = self.svc.disposition(ref, token, "approve")
        self.assertEqual(final["state"], "completed")
        self.assertEqual(
            [e["type"] for e in final["events"]],
            [
                "work.requested",
                "provider.accepted",
                "attempt.started",
                "question.asked",
                "question.answered",
                "delivery.submitted",
                "validation.recorded",
                "customer.approved",
            ],
        )
        self.assertTrue(self.svc.verify_chain(ref)[0])


    def test_idea_submission_runs_without_github_and_enters_same_queue(self):
        result = self.svc.submit(
            "idea", "350.00", "Build a portable artifact review service with a clean handoff.",
            attested=True, idea_title="Portable artifact review service",
            context_url="https://example.test/spec",
        )
        work = result["work"]
        self.assertEqual(work["source"]["kind"], "idea")
        self.assertEqual(work["source"]["title"], "Portable artifact review service")
        self.assertEqual(work["value_signal_usd"], "350.00")
        self.assertEqual(self.svc.public_status()["queue"]["occupied"], 1)

    def test_idea_title_and_context_url_are_validated(self):
        with self.assertRaises(ValidationError):
            self.svc.submit("idea", "10", "A sufficiently long desired outcome.", attested=True, idea_title="short")
        with self.assertRaises(ValidationError):
            self.svc.submit("idea", "10", "A sufficiently long desired outcome.", attested=True,
                            idea_title="A valid idea title", context_url="http://example.test/spec")

    def test_idea_accept_start_delivery_validation_and_customer_approval(self):
        result = self.svc.submit(
            "idea", "500", "Build the smallest working implementation and return evidence.",
            attested=True, idea_title="A real greenfield build request",
        )
        ref, token = result["work_ref"], result["claim_token"]
        self.svc.accept(ref)
        started = self.svc.start(ref)
        self.assertEqual(started["source"]["kind"], "idea")
        self.assertEqual(started["attempt_number"], 1)
        self.svc.deliver(ref, "Built and tested.", ["https://example.test/artifact"])
        self.svc.validate_delivery(ref, "valid", ["https://example.test/validation"], validator="fresh-run")
        final = self.svc.disposition(ref, token, "approve")
        self.assertEqual(final["state"], "completed")
        self.assertTrue(self.svc.verify_chain(ref)[0])

    def test_customer_handoff_for_idea_is_token_protected_and_token_free(self):
        result = self.svc.submit(
            "idea", "125", "Produce a working prototype with evidence and clear handoff.",
            attested=True, idea_title="Prototype a portable handoff demo",
        )
        with self.assertRaises(Unauthorized):
            self.svc.customer_handoff(result["work_ref"], "wrong")
        handoff = self.svc.customer_handoff(result["work_ref"], result["claim_token"])
        raw = json.dumps(handoff)
        self.assertEqual(handoff["profile"], "owp-field-lab/0.1")
        self.assertEqual(handoff["work"]["source"]["kind"], "idea")
        self.assertNotIn(result["claim_token"], raw)


class GitHubVerifierTests(unittest.TestCase):
    def payload(self, **overrides):
        data = {
            "state": "open",
            "draft": False,
            "title": "A real PR",
            "user": {"login": "alice"},
            "head": {"sha": "abc123", "ref": "feature"},
            "base": {"ref": "main"},
            "additions": 120,
            "deletions": 30,
            "changed_files": 5,
            "commits": 2,
        }
        data.update(overrides)
        return data

    def response(self, payload):
        class Response:
            def __enter__(self): return self
            def __exit__(self, *args): return False
            def read(self, _limit=None): return json.dumps(payload).encode()
        return Response()

    def test_real_verifier_constructs_only_github_api_request_and_snapshots_size(self):
        seen = {}
        def fake_urlopen(request, timeout):
            seen["url"] = request.full_url
            seen["auth"] = request.headers.get("Authorization")
            return self.response(self.payload())

        with patch("owp_field_lab.github.urlopen", fake_urlopen):
            snap = GitHubVerifier(token="secret").verify("https://github.com/A/B/pull/9")
        self.assertEqual(seen["url"], "https://api.github.com/repos/a/b/pulls/9")
        self.assertEqual(seen["auth"], "Bearer secret")
        self.assertEqual(snap.size_band, "medium")
        self.assertEqual(snap.head_sha, "abc123")

    def test_rate_limited_github_response_is_actionable(self):
        def fake_urlopen(request, timeout):
            raise HTTPError(request.full_url, 429, "rate", {}, None)
        with patch("owp_field_lab.github.urlopen", fake_urlopen), self.assertRaises(ValidationError) as ctx:
            GitHubVerifier().verify("https://github.com/a/b/pull/9")
        self.assertIn("rate-limited", str(ctx.exception))

    def test_closed_pr_and_missing_head_are_rejected(self):
        for payload in (self.payload(state="closed"), self.payload(head={"sha": "", "ref": "x"})):
            with self.subTest(payload=payload):
                with patch("owp_field_lab.github.urlopen", lambda *_args, **_kwargs: self.response(payload)):
                    with self.assertRaises(ValidationError):
                        GitHubVerifier().verify("https://github.com/a/b/pull/9")


class HTTPTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.verifier = FakeVerifier()
        self.svc = WorkService(Path(self.tmp.name) / "http.sqlite3", verifier=self.verifier)
        self.server = create_server(
            self.svc,
            "127.0.0.1",
            0,
            sse_interval=0.03,
            submission_limit=50,
        )
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base = f"http://127.0.0.1:{self.server.server_port}"

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
        self.tmp.cleanup()

    def request_json(self, path: str, body: dict, token: str | None = None):
        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        request = Request(
            self.base + path,
            data=json.dumps(body).encode(),
            headers=headers,
            method="POST",
        )
        return urlopen(request, timeout=2)

    def submit_http(self, number=1):
        response = self.request_json(
            "/api/submissions",
            {
                "pr_url": f"https://github.com/example/project/pull/{number}",
                "bid_usd": "10.00",
                "outcome": "Please make this PR production ready.",
                "attested": True,
            },
        )
        return json.loads(response.read())

    def test_public_http_has_no_admin_queue_surface(self):
        with self.assertRaises(HTTPError) as ctx:
            urlopen(self.base + "/api/admin/queue")
        self.assertEqual(ctx.exception.code, 404)

    def test_static_page_and_privacy_notice_are_explicit(self):
        raw = urlopen(self.base + "/").read().decode()
        self.assertIn("No money is collected", raw)
        self.assertIn("Private queue", raw)
        self.assertIn("What value would this outcome have to you?", raw)
        self.assertIn("authorized to request this work", raw)
        self.assertIn("Build idea", raw)
        privacy = urlopen(self.base + "/privacy").read().decode()
        self.assertIn("How data may be used", privacy)
        self.assertIn("short-lived in-memory client address", privacy)

    def test_security_headers_are_sent_on_static_and_json(self):
        for url in (self.base + "/", self.base + "/api/status"):
            response = urlopen(url)
            self.assertEqual(response.headers["X-Frame-Options"], "DENY")
            self.assertEqual(response.headers["Cross-Origin-Resource-Policy"], "same-origin")
            self.assertIn("payment=()", response.headers["Permissions-Policy"])
            self.assertIn("frame-ancestors 'none'", response.headers["Content-Security-Policy"])

    def test_submission_requires_application_json_to_block_cross_site_simple_posts(self):
        request = Request(
            self.base + "/api/submissions",
            data=json.dumps({"pr_url": "https://github.com/a/b/pull/1"}).encode(),
            headers={"Content-Type": "text/plain"},
            method="POST",
        )
        with self.assertRaises(HTTPError) as ctx:
            urlopen(request)
        self.assertEqual(ctx.exception.code, 400)
        self.assertIn("Content-Type", ctx.exception.read().decode())

    def test_submission_requires_attestation_over_http(self):
        with self.assertRaises(HTTPError) as ctx:
            self.request_json(
                "/api/submissions",
                {
                    "pr_url": "https://github.com/example/project/pull/1",
                    "bid_usd": "10",
                    "outcome": "Please make this production ready.",
                    "attested": False,
                },
            )
        self.assertEqual(ctx.exception.code, 400)

    def test_wrong_token_and_unknown_ref_share_same_not_found_response(self):
        result = self.submit_http(1)
        for path, token in (
            (f"/api/work/{result['work_ref']}", "wrong"),
            ("/api/work/OWP-AAAAAAAAAAAAAAAAAAAAAAAA", "wrong"),
        ):
            request = Request(self.base + path, headers={"Authorization": f"Bearer {token}"})
            with self.subTest(path=path), self.assertRaises(HTTPError) as ctx:
                urlopen(request)
            self.assertEqual(ctx.exception.code, 404)
            self.assertEqual(json.loads(ctx.exception.read())["error"], "Not found.")

    def test_work_routes_are_exact_not_prefix_matches(self):
        result = self.submit_http(1)
        request = Request(
            self.base + f"/api/work/{result['work_ref']}/junk",
            headers={"Authorization": f"Bearer {result['claim_token']}"},
        )
        with self.assertRaises(HTTPError) as ctx:
            urlopen(request)
        self.assertEqual(ctx.exception.code, 404)

    def test_sse_capacity_live_updates_after_submission(self):
        req = Request(self.base + "/api/live", headers={"Accept": "text/event-stream"})
        response = urlopen(req, timeout=2)
        first = response.readline().decode()
        while first and not first.startswith("event: capacity"):
            first = response.readline().decode()
        data_line = response.readline().decode()
        initial = json.loads(data_line.removeprefix("data: ").strip())
        self.assertEqual(initial["queue"]["occupied"], 0)

        self.svc.submit(
            "https://github.com/example/project/pull/55",
            "10",
            "Please make this PR production ready.",
            attested=True,
        )
        deadline = time.time() + 2
        updated = None
        while time.time() < deadline:
            line = response.readline().decode()
            if line.startswith("data: "):
                candidate = json.loads(line.removeprefix("data: ").strip())
                if candidate["queue"]["occupied"] == 1:
                    updated = candidate
                    break
        response.close()
        self.assertIsNotNone(updated)

    def test_healthz_fails_when_event_chain_is_corrupted(self):
        result = self.svc.submit(
            "https://github.com/example/project/pull/1",
            "10",
            "Please make this PR production ready.",
            attested=True,
        )
        self.assertEqual(json.loads(urlopen(self.base + "/healthz").read())["ok"], True)
        with connect(self.svc.db_path) as conn:
            conn.execute("UPDATE events SET actor = 'corrupt' WHERE seq = 1")
        with self.assertRaises(HTTPError) as ctx:
            urlopen(self.base + "/healthz")
        self.assertEqual(ctx.exception.code, 503)
        self.assertFalse(json.loads(ctx.exception.read())["ok"])

    def test_machine_readable_surface_describes_field_lab_boundary(self):
        described = json.loads(urlopen(self.base + "/api/owp/describe").read())
        self.assertEqual(described["profile"], "owp-field-lab/0.1")
        self.assertFalse(described["conformance_claim"])
        self.assertEqual(described["work_types"], ["github_pr", "idea"])
        self.assertIn("export_handoff", described["customer_actions"])

    def test_idea_submission_over_http_and_customer_handoff_download(self):
        response = self.request_json(
            "/api/submissions",
            {
                "work_kind": "idea",
                "idea_title": "Build an end to end field lab fixture",
                "context_url": "https://example.test/brief",
                "value_usd": "275.00",
                "outcome": "Create a real runnable fixture with evidence and portable state.",
                "attested": True,
            },
        )
        result = json.loads(response.read())
        self.assertEqual(result["work"]["source"]["kind"], "idea")
        request = Request(
            self.base + f"/api/work/{result['work_ref']}/handoff",
            headers={"Authorization": f"Bearer {result['claim_token']}"},
        )
        handoff = json.loads(urlopen(request).read())
        self.assertEqual(handoff["profile"], "owp-field-lab/0.1")
        self.assertNotIn(result["claim_token"], json.dumps(handoff))

    def test_complete_idea_journey_crosses_http_operator_customer_and_handoff(self):
        response = self.request_json(
            "/api/submissions",
            {
                "work_kind": "idea",
                "idea_title": "Build a durable customer support handoff",
                "context_url": "https://example.test/brief",
                "value_usd": "450.00",
                "outcome": "Deliver a working implementation with evidence and portable state.",
                "attested": True,
            },
        )
        intake = json.loads(response.read())
        ref, token = intake["work_ref"], intake["claim_token"]

        self.svc.accept(ref, "Suitable for the field lab.")
        self.svc.start(ref)
        waiting = self.svc.ask(
            ref,
            "Which compatibility rule should the implementation preserve?",
            ["Preserve current behavior", "Prefer the new behavior"],
            ["https://example.test/spec"],
        )
        question_id = waiting["questions"][0]["id"]

        answered = json.loads(self.request_json(
            f"/api/work/{ref}/answer",
            {"question_id": question_id, "option": "Preserve current behavior", "note": "Keep compatibility."},
            token,
        ).read())
        self.assertEqual(answered["state"], "in_progress")

        self.svc.deliver(ref, "Implemented the requested outcome and recorded validation evidence.", ["https://example.test/delivery"] )
        self.svc.validate_delivery(
            ref, "valid", ["https://example.test/validation"], validator="fresh-clone-check"
        )
        completed = json.loads(self.request_json(
            f"/api/work/{ref}/disposition", {"action": "approve", "note": "Accepted."}, token
        ).read())
        self.assertEqual(completed["state"], "completed")

        request = Request(
            self.base + f"/api/work/{ref}/handoff",
            headers={"Authorization": f"Bearer {token}"},
        )
        handoff = json.loads(urlopen(request).read())
        self.assertTrue(handoff["chain_verified"])
        self.assertEqual(handoff["work"]["state"], "completed")
        event_types = [event["type"] for event in handoff["work"]["events"]]
        self.assertEqual(
            event_types,
            [
                "work.requested", "provider.accepted", "attempt.started", "question.asked",
                "question.answered", "delivery.submitted", "validation.recorded", "customer.approved",
            ],
        )

    def test_submission_rate_limiter_returns_429_and_retry_after(self):
        server = create_server(
            WorkService(Path(self.tmp.name) / "rate.sqlite3", verifier=FakeVerifier()),
            "127.0.0.1",
            0,
            submission_limit=1,
            submission_window_seconds=60,
        )
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base = f"http://127.0.0.1:{server.server_port}"
        try:
            def request(number):
                return urlopen(
                    Request(
                        base + "/api/submissions",
                        data=json.dumps({
                            "pr_url": f"https://github.com/example/project/pull/{number}",
                            "bid_usd": "10",
                            "outcome": "Please make this production ready.",
                            "attested": True,
                        }).encode(),
                        headers={"Content-Type": "application/json"},
                        method="POST",
                    )
                )
            self.assertEqual(request(1).status, 201)
            with self.assertRaises(HTTPError) as ctx:
                request(2)
            self.assertEqual(ctx.exception.code, 429)
            self.assertIsNotNone(ctx.exception.headers.get("Retry-After"))
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

    def test_sse_connection_count_is_bounded(self):
        server = create_server(
            WorkService(Path(self.tmp.name) / "sse.sqlite3", verifier=FakeVerifier()),
            "127.0.0.1",
            0,
            sse_interval=0.5,
            sse_max_clients=1,
        )
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base = f"http://127.0.0.1:{server.server_port}"
        first = None
        try:
            first = urlopen(base + "/api/live", timeout=2)
            first.readline()
            with self.assertRaises(HTTPError) as ctx:
                urlopen(base + "/api/live", timeout=2)
            self.assertEqual(ctx.exception.code, 503)
        finally:
            if first:
                first.close()
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)


class AdminCLITests(unittest.TestCase):
    def test_operator_cli_refuses_to_silently_create_missing_database(self):
        with tempfile.TemporaryDirectory() as tmp:
            missing = Path(tmp) / "missing.sqlite3"
            stderr = io.StringIO()
            with patch.dict(os.environ, {"OWP_FIELD_LAB_DB": str(missing)}, clear=False):
                with contextlib.redirect_stderr(stderr):
                    rc = admin.main(["queue"])
            self.assertEqual(rc, 2)
            self.assertFalse(missing.exists())
            self.assertIn("database does not exist", stderr.getvalue())


    def test_operator_cli_drives_core_idea_lifecycle_on_real_database(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "operator.sqlite3"
            svc = WorkService(db_path, verifier=FakeVerifier())
            intake = svc.submit(
                "idea", "500", "Build and prove the requested portable outcome.",
                attested=True, idea_title="Portable operator lifecycle fixture",
            )
            ref, token = intake["work_ref"], intake["claim_token"]
            env = {"OWP_FIELD_LAB_DB": str(db_path)}
            commands = [
                ["accept", ref, "--note", "Suitable."],
                ["start", ref],
                ["deliver", ref, "--summary", "Implemented and verified the requested outcome.",
                 "--evidence", "https://example.test/delivery"],
                ["validate", ref, "--result", "valid", "--validator", "clean-room-check",
                 "--evidence", "https://example.test/validation"],
                ["verify-chain", ref],
            ]
            with patch.dict(os.environ, env, clear=False), contextlib.redirect_stdout(io.StringIO()):
                for command in commands:
                    self.assertEqual(admin.main(command), 0, command)
            completed = WorkService(db_path, verifier=FakeVerifier()).disposition(ref, token, "approve", "Accepted.")
            self.assertEqual(completed["state"], "completed")


class StaticAssetTests(unittest.TestCase):
    def setUp(self):
        root = Path(__file__).resolve().parents[1] / "owp_field_lab" / "static"
        self.html = (root / "index.html").read_text(encoding="utf-8")
        self.js = (root / "app.js").read_text(encoding="utf-8")
        self.css = (root / "styles.css").read_text(encoding="utf-8")

    def test_full_queue_cannot_be_accidentally_reenabled_after_submit(self):
        self.assertIn("accepting = Boolean(q.accepting)", self.js)
        self.assertIn("submitButton.disabled = !accepting", self.js)
        self.assertNotIn("submitButton.disabled = false", self.js)

    def test_public_form_discloses_free_service_data_use_and_authorization(self):
        self.assertIn("No money is collected", self.html)
        self.assertIn("authorized to request this work", self.html)
        self.assertIn("may be retained and analyzed", self.html)
        self.assertIn('id="attested"', self.html)
        self.assertIn('value="github_pr"', self.html)
        self.assertIn('value="idea"', self.html)

    def test_customer_decisions_use_inline_controls_and_handoff_download(self):
        self.assertNotIn("prompt(", self.js)
        self.assertNotIn("alert(", self.js)
        self.assertIn("disposition-note", self.js)
        self.assertIn("download-handoff", self.js)
        self.assertIn("tracking-link", self.js)

    def test_polished_layout_has_mobile_breakpoints_capacity_and_lifecycle(self):
        self.assertIn('class="meter"', self.html)
        self.assertIn("@media(max-width:850px)", self.css)
        self.assertIn("stage-rail", self.html)
        self.assertIn("hero-strip", self.html)


if __name__ == "__main__":
    unittest.main()
