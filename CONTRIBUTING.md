# Contributing

Open an issue before proposing a protocol change. Describe the independent
deployment evidence or the existing invariant that requires it, and identify
the affected normative requirements. The decision bar and exception process
are in `docs/09-changing-the-protocol.md`.

For specification changes:

```sh
node tools/build-requirement-matrix.mjs
tools/build-public-trees.sh /tmp/owp-public-candidate
git diff --check
```

Update the prose, schema/reference implementation, conformance checks, matrix,
risk register, and compatibility analysis together. A passing reference suite
is necessary but does not by itself justify changing the contract. Do not add
domain vocabulary to the core unless it clears the stated bar.

Contributions are accepted under the repository's MIT license. Follow the
security policy for vulnerabilities and never commit secrets, databases,
session files, build outputs, or private deployment data.
