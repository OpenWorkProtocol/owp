#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC="$ROOT/templates/try-owp"
DEST=""
OPERATOR="My Agent Lab"
HOSTNAME="try.localhost"
PROVIDER_ID="provider:local"
INSTANCE_TITLE="Try OWP — Local Field Lab"
PROTOCOL_URL="https://github.com/OpenWorkProtocol/owp"
RUN_TESTS=1

usage() {
  cat <<'EOF'
usage: scripts/new-try-owp.sh DESTINATION [options]

Options:
  --operator NAME       Human-facing operator/provider name
  --hostname HOST       Public hostname without scheme
  --provider-id ID      Stable durable actor id (default: provider:local)
  --title TITLE         Browser/site title
  --protocol-url URL    OWP source/spec link
  --no-test             Render only; skip generated-instance smoke suite
  -h, --help            Show this help

Example:
  ./scripts/new-try-owp.sh ../my-try-owp \
    --operator "Acme Agent Lab" \
    --hostname try.example.com \
    --provider-id provider:acme
EOF
}

[[ $# -gt 0 ]] || { usage >&2; exit 2; }
DEST="$1"; shift
while [[ $# -gt 0 ]]; do
  case "$1" in
    --operator) [[ $# -ge 2 ]] || { echo "missing --operator value" >&2; exit 2; }; OPERATOR="$2"; shift 2;;
    --hostname) [[ $# -ge 2 ]] || { echo "missing --hostname value" >&2; exit 2; }; HOSTNAME="$2"; shift 2;;
    --provider-id) [[ $# -ge 2 ]] || { echo "missing --provider-id value" >&2; exit 2; }; PROVIDER_ID="$2"; shift 2;;
    --title) [[ $# -ge 2 ]] || { echo "missing --title value" >&2; exit 2; }; INSTANCE_TITLE="$2"; shift 2;;
    --protocol-url) [[ $# -ge 2 ]] || { echo "missing --protocol-url value" >&2; exit 2; }; PROTOCOL_URL="$2"; shift 2;;
    --no-test) RUN_TESTS=0; shift;;
    -h|--help) usage; exit 0;;
    *) echo "unknown option: $1" >&2; usage >&2; exit 2;;
  esac
done

command -v python3 >/dev/null || { echo "ERROR: python3 is required" >&2; exit 2; }
[[ -d "$SRC" ]] || { echo "ERROR: template missing: $SRC" >&2; exit 1; }
[[ ! -e "$DEST" ]] || { echo "ERROR: destination already exists: $DEST" >&2; exit 1; }

python3 - "$SRC" "$DEST" "$OPERATOR" "$HOSTNAME" "$PROVIDER_ID" "$INSTANCE_TITLE" "$PROTOCOL_URL" <<'PY'
from pathlib import Path
import re, shutil, sys
src=Path(sys.argv[1]).resolve(); dest=Path(sys.argv[2]).resolve()
operator, hostname, provider_id, title, protocol_url=sys.argv[3:8]
if not operator.strip() or len(operator)>120:
    raise SystemExit("ERROR: operator must be 1-120 characters")
if not re.fullmatch(r"[A-Za-z0-9.-]+", hostname) or ".." in hostname or hostname.startswith(".") or hostname.endswith("."):
    raise SystemExit("ERROR: hostname must be a DNS-style name without scheme/path")
if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:@/-]{0,127}", provider_id):
    raise SystemExit("ERROR: provider-id must be a stable 1-128 character identifier")
if not title.strip() or len(title)>160:
    raise SystemExit("ERROR: title must be 1-160 characters")
if not re.fullmatch(r"https://[^\\s]+", protocol_url):
    raise SystemExit("ERROR: protocol-url must be https://")
shutil.copytree(src,dest,ignore=shutil.ignore_patterns("__pycache__","*.pyc"))
values={
    "__OWP_OPERATOR_NAME__": operator,
    "__OWP_PUBLIC_HOSTNAME__": hostname,
    "__OWP_PROVIDER_ACTOR__": provider_id,
    "__OWP_INSTANCE_TITLE__": title,
    "__OWP_PROTOCOL_URL__": protocol_url,
}
for p in dest.rglob("*"):
    if not p.is_file(): continue
    try: text=p.read_text(encoding="utf-8")
    except UnicodeDecodeError: continue
    for key,val in values.items(): text=text.replace(key,val)
    p.write_text(text,encoding="utf-8")
unresolved=[]
for p in dest.rglob("*"):
    if not p.is_file(): continue
    try: text=p.read_text(encoding="utf-8")
    except UnicodeDecodeError: continue
    if re.search(r"__OWP_[A-Z_]+__",text): unresolved.append(str(p.relative_to(dest)))
if unresolved:
    raise SystemExit("ERROR: unresolved template tokens: "+", ".join(unresolved))
PY

chmod +x "$DEST/scripts/smoke.sh" "$DEST/scripts/live-github-smoke.sh" 2>/dev/null || true
printf 'Created Try OWP instance: %s\n' "$DEST"
printf 'Operator: %s\nHostname: %s\nProvider actor: %s\n' "$OPERATOR" "$HOSTNAME" "$PROVIDER_ID"

if [[ "$RUN_TESTS" == "1" ]]; then
  echo "==> Running generated-instance smoke suite"
  (cd "$DEST" && ./scripts/smoke.sh)
fi

cat <<EOF

NEXT
  cd $(printf '%q' "$DEST")
  export GITHUB_TOKEN="\$(gh auth token)"   # optional but recommended
  python3 -m owp_field_lab.server --host 127.0.0.1 --port 8080

Before public ingress, read:
  $DEST/SECURITY.md
  $DEST/PRIVACY.md
  $DEST/docs/DEPLOY.md
EOF
