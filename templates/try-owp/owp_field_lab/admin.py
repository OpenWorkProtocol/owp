from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from .errors import FieldLabError
from .github import GitHubVerifier
from .service import WorkService


def service_from_env() -> WorkService:
    db = os.environ.get("OWP_FIELD_LAB_DB", "./data/owp-field-lab.sqlite3")
    db_path = Path(db)
    if not db_path.exists():
        raise ValueError(
            f"database does not exist: {db_path}. Start the server first or set OWP_FIELD_LAB_DB correctly."
        )
    queue_max = int(os.environ.get("OWP_FIELD_LAB_QUEUE_MAX", "20"))
    token = os.environ.get("GITHUB_TOKEN")
    return WorkService(db_path, queue_max=queue_max, verifier=GitHubVerifier(token=token), provider_actor=os.environ.get("OWP_FIELD_LAB_PROVIDER_ID", "provider"))


def dump(value):
    print(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False))


def write_private(path: str, data: str) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    try:
        try:
            os.chmod(target, 0o600)
        except OSError:
            pass
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(data)
    except Exception:
        try:
            os.close(fd)
        except OSError:
            pass
        raise


def print_queue_table(rows: list[dict]) -> None:
    if not rows:
        print("Private queue is empty.")
        return
    print(f"{'#':>2}  {'WORK REF':<29} {'STATE':<11} {'VALUE':>10} {'TYPE':<10} SOURCE")
    print("-" * 112)
    for index, row in enumerate(rows, 1):
        print(
            f"{index:>2}  {row['public_id']:<29} {row['state']:<11} "
            f"${row['value_signal_usd']:>9} {row['work_kind']:<10} {row['source_label']}"
        )
        outcome = " ".join(row["outcome"].split())
        if len(outcome) > 92:
            outcome = outcome[:89] + "..."
        print(f"    {outcome}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Private OWP Field Lab operator CLI")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("status", help="Show queue capacity and service status")

    p = sub.add_parser("queue", help="Show the private queue")
    p.add_argument("--all", action="store_true")
    p.add_argument("--json", action="store_true", help="Emit machine-readable JSON")

    p = sub.add_parser("show", help="Show one work item via portable handoff projection")
    p.add_argument("work_ref")

    p = sub.add_parser("accept")
    p.add_argument("work_ref")
    p.add_argument("--note", default="")

    p = sub.add_parser("pass")
    p.add_argument("work_ref")
    p.add_argument("--reason", required=True)

    p = sub.add_parser("start", help="Refresh the PR when applicable and start an attempt")
    p.add_argument("work_ref")

    p = sub.add_parser("ask")
    p.add_argument("work_ref")
    p.add_argument("--text", required=True)
    p.add_argument("--option", action="append", required=True)
    p.add_argument("--evidence", action="append", default=[])

    p = sub.add_parser("deliver")
    p.add_argument("work_ref")
    p.add_argument("--summary", required=True)
    p.add_argument("--evidence", action="append", required=True)

    p = sub.add_parser("validate")
    p.add_argument("work_ref")
    p.add_argument("--result", choices=["valid", "invalid"], required=True)
    p.add_argument("--validator", required=True, help="Named validation actor/tool")
    p.add_argument("--evidence", action="append", required=True)
    p.add_argument("--note", default="")

    p = sub.add_parser("verify-chain")
    p.add_argument("work_ref")

    sub.add_parser("verify-all", help="SQLite quick-check plus every event chain")

    p = sub.add_parser("backup", help="Create a consistent private SQLite backup")
    p.add_argument("--out", required=True)

    p = sub.add_parser("export-handoff")
    p.add_argument("work_ref")
    p.add_argument("--out")

    p = sub.add_parser("export-bids")
    p.add_argument("--out")

    p = sub.add_parser("export-research", help="Private JSONL research export")
    p.add_argument("--out")

    return parser


def run(args, svc: WorkService) -> int:
    if args.cmd == "status":
        dump(svc.public_status())
    elif args.cmd == "queue":
        rows = svc.admin_queue(include_terminal=args.all)
        if args.json:
            dump(rows)
        else:
            print_queue_table(rows)
    elif args.cmd == "show":
        dump(svc.export_handoff(args.work_ref))
    elif args.cmd == "accept":
        dump(svc.accept(args.work_ref, args.note))
    elif args.cmd == "pass":
        dump(svc.pass_work(args.work_ref, args.reason))
    elif args.cmd == "start":
        dump(svc.start(args.work_ref))
    elif args.cmd == "ask":
        dump(svc.ask(args.work_ref, args.text, args.option, args.evidence))
    elif args.cmd == "deliver":
        dump(svc.deliver(args.work_ref, args.summary, args.evidence))
    elif args.cmd == "validate":
        dump(
            svc.validate_delivery(
                args.work_ref,
                args.result,
                args.evidence,
                args.note,
                validator=args.validator,
            )
        )
    elif args.cmd == "verify-chain":
        ok, detail = svc.verify_chain(args.work_ref)
        print(("PASS" if ok else "FAIL") + ": " + detail)
        return 0 if ok else 1
    elif args.cmd == "verify-all":
        result = svc.verify_all()
        dump(result)
        return 0 if result["ok"] else 1
    elif args.cmd == "backup":
        print(svc.backup_database(args.out))
    elif args.cmd == "export-handoff":
        data = json.dumps(svc.export_handoff(args.work_ref), indent=2, sort_keys=True, ensure_ascii=False) + "\n"
        if args.out:
            write_private(args.out, data)
            print(args.out)
        else:
            print(data, end="")
    elif args.cmd == "export-bids":
        data = svc.export_bids_csv()
        if args.out:
            write_private(args.out, data)
            print(args.out)
        else:
            print(data, end="")
    elif args.cmd == "export-research":
        data = svc.export_research_jsonl()
        if args.out:
            write_private(args.out, data)
            print(args.out)
        else:
            print(data, end="")
    return 0


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return run(args, service_from_env())
    except (FieldLabError, ValueError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
