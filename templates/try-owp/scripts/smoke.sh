#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

# The unrendered template source intentionally contains a provider placeholder.
# Give tests a valid actor while preserving that token for the renderer.
if [[ "${OWP_TEMPLATE_SOURCE:-0}" == "1" ]]; then
  export OWP_FIELD_LAB_PROVIDER_ID="${OWP_FIELD_LAB_PROVIDER_ID:-provider:template}"
fi

echo "==> unit/integration/security/static suite"
python3 -m unittest discover -s tests -v

echo
echo "==> Python compile"
python3 -m compileall -q owp_field_lab tests

echo
echo "==> CLI entry points"
python3 -m owp_field_lab.server --help >/dev/null
python3 -m owp_field_lab.admin --help >/dev/null

echo
echo "==> browser JavaScript syntax"
if command -v node >/dev/null 2>&1; then
  node --check owp_field_lab/static/app.js >/dev/null
else
  echo "SKIP: node not installed; JavaScript behavior remains covered by static/HTTP tests"
fi

echo
echo "==> package manifest"
test -s PACKAGE_FILES.txt
if [[ -n "$(sort PACKAGE_FILES.txt | uniq -d)" ]]; then
  echo "Duplicate path in PACKAGE_FILES.txt" >&2
  exit 1
fi
while IFS= read -r file; do
  [[ -n "$file" ]] || continue
  [[ "$file" != /* && "$file" != *".."* ]] || { echo "Unsafe package path: $file" >&2; exit 1; }
  test -f "$file" || { echo "Missing package path: $file" >&2; exit 1; }
done < PACKAGE_FILES.txt

# The release tree is an allowlist: no accidental notes, databases, secrets or stale files.
mapfile -t declared < <(sort PACKAGE_FILES.txt)
mapfile -t actual < <(find . -type f \
  ! -path './.git/*' \
  ! -path './__pycache__/*' \
  ! -path '*/__pycache__/*' \
  ! -name '*.pyc' \
  ! -path './data/*' \
  ! -path './build/*' \
  ! -path './dist/*' \
  | sed 's#^./##' | sort)
if ! diff -u <(printf '%s\n' "${declared[@]}") <(printf '%s\n' "${actual[@]}"); then
  echo "Release tree differs from PACKAGE_FILES.txt" >&2
  exit 1
fi

for file in \
  README.md PRIVACY.md SECURITY.md FEATURE_TEST_MAP.md \
  docs/DEPLOY.md docs/OPERATOR.md spec/FIELD_LAB_PROFILE.md \
  deploy/Caddyfile.example deploy/cloudflared-config.yml.example deploy/owp-field-lab.env.example deploy/owp-field-lab.service.example \
  owp_field_lab/static/index.html owp_field_lab/static/privacy.html owp_field_lab/static/styles.css owp_field_lab/static/app.js
do
  test -s "$file"
done

echo
echo "==> public contract anchors"
grep -Fq "open GitHub pull requests" README.md
grep -Fq "greenfield build ideas" README.md
grep -Fq "No money is collected" README.md owp_field_lab/static/index.html
grep -Fq "bounded private FIFO queue" README.md
grep -Fq "APPROVE/STEER/REJECT" README.md
grep -Fq "portable handoff exports" README.md
grep -Fq "not a normative OWP profile" README.md
if [[ "${OWP_TEMPLATE_SOURCE:-0}" == "1" ]]; then
  python3 - <<'PY2'
from pathlib import Path
required = [
    "__" + "OWP_PUBLIC_HOSTNAME__",
    "__" + "OWP_OPERATOR_NAME__",
    "__" + "OWP_INSTANCE_TITLE__",
    "__" + "OWP_PROVIDER_ACTOR__",
    "__" + "OWP_PROTOCOL_URL__",
]
parts=[]
for p in Path('.').rglob('*'):
    if not p.is_file() or '__pycache__' in p.parts:
        continue
    try: parts.append(p.read_text(encoding='utf-8'))
    except UnicodeDecodeError: pass
text='\n'.join(parts)
missing=[x for x in required if x not in text]
if missing: raise SystemExit("missing template token(s): " + ", ".join(missing))
print("template source tokens present")
PY2
fi
grep -Fq "A work item should remain understandable, steerable, evidenced and portable" spec/FIELD_LAB_PROFILE.md

echo
echo "==> template rendering"
if [[ "${OWP_TEMPLATE_SOURCE:-0}" == "1" ]]; then
  echo "template source mode: unresolved rendering tokens are expected"
else
  python3 - <<'PY2'
from pathlib import Path
import re
pattern = re.compile("__" + r"OWP_[A-Z0-9_]+__")
hits=[]
for p in Path('.').rglob('*'):
    if not p.is_file() or '__pycache__' in p.parts or p.suffix == '.pyc':
        continue
    try: text=p.read_text(encoding='utf-8')
    except UnicodeDecodeError: continue
    found=sorted(set(pattern.findall(text)))
    if found: hits.append((str(p), found))
if hits:
    for p, found in hits: print(f"{p}: {', '.join(found)}")
    raise SystemExit("Unresolved template token found")
print("rendered template contains no unresolved tokens")
PY2
fi

echo
echo "==> release hygiene"
if find . -type f \( -name '*.sqlite*' -o -name '*.db' -o -name '*.pem' -o -name '*.key' -o -name '.env' \) | grep -q .; then
  echo "Private/runtime material found in release tree" >&2
  exit 1
fi

echo
echo "PASS: OWP Field Lab release smoke"
