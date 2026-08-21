# Contributing

Open an issue before proposing a protocol change. Describe the independent
deployment evidence or the existing invariant that requires it, and identify
the affected normative requirements. The decision bar and exception process
are in `docs/09-changing-the-protocol.md`.

For specification changes:

```sh
node tools/build-requirement-matrix.mjs
node tools/test-software-work-integrity-vectors.mjs
node tools/test-software-work-integrity.mjs
node tools/test-project-surface.mjs
node tools/test-site.mjs
node tools/test-doc-links.mjs
node -e "const fs=require('fs'); for (const f of fs.readdirSync('schemas').filter(x=>x.endsWith('.json'))) JSON.parse(fs.readFileSync('schemas/'+f,'utf8'))"
git diff --check
```

Update the prose, schemas/reference verifier, conformance checks, matrix,
risk register, and compatibility analysis together. A passing reference suite
is necessary but does not by itself justify changing the contract. Do not add
domain vocabulary to the core unless it clears the stated bar.

Contributions are accepted under the repository's MIT license. Follow the
security policy for vulnerabilities and never commit secrets, databases,
session files, build outputs, or private deployment data.


For website or Field Lab documentation changes, keep the project surfaces
separate: `openworkprotocol.org` explains the protocol and
`try.openworkprotocol.org` runs the field experiment. Do not turn Field Lab
behavior into a normative requirement without clearing the protocol-change bar.

Credit security/design feedback when it materially changes the threat model or
requirements; do not imply authorship or endorsement that was not given.


## Try OWP template changes

Changes under `templates/try-owp/` are non-normative product/example changes,
but they must preserve the public/private boundary: no public queue listing, no
remote admin HTTP API, no payment collection, and no execution of submitted
untrusted code in the intake process. Run both the raw-template and rendered-instance gates before submitting a change:

```sh
OWP_TEMPLATE_SOURCE=1 bash templates/try-owp/scripts/smoke.sh
tmp="$(mktemp -d)"
./scripts/new-try-owp.sh "$tmp/field-lab" --operator "Contributor Test" --hostname try-test.example.com --provider-id provider:test --no-test
(cd "$tmp/field-lab" && ./scripts/smoke.sh)
```
