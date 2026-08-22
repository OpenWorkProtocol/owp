#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

PR_URL="${1:-}"
if [[ -z "$PR_URL" ]]; then
  echo "usage: $0 https://github.com/owner/repo/pull/123" >&2
  exit 2
fi

python3 - "$PR_URL" <<'PY'
import os
import sys
from owp_field_lab.errors import FieldLabError
from owp_field_lab.github import GitHubVerifier

url = sys.argv[1]
try:
    snapshot = GitHubVerifier(token=os.environ.get("GITHUB_TOKEN"), timeout=10).verify(url)
except FieldLabError as exc:
    print(f"FAIL: {exc}", file=sys.stderr)
    raise SystemExit(1)
print("PASS: live GitHub PR verified")
print(snapshot.pr_url)
print(snapshot.title)
print("head_sha:", snapshot.head_sha)
print("size:", snapshot.size_band, "files:", snapshot.changed_files, "churn:", snapshot.additions + snapshot.deletions)
PY
