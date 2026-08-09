# Governance and release policy

The maintainers of the OpenWorkProtocol repositories steward the specification
and reference artifacts. There is no standards body, certification authority,
foundation, paid support promise, or compatibility program behind this release
candidate. Decisions and their evidence belong in the public repository.

Protocol changes follow `docs/09-changing-the-protocol.md`: evidence from two
unrelated domains or enforcement of an existing invariant is the normal bar.
A maintainer may make an explicit exception, but the exception, rationale,
compatibility impact, and dissent must be recorded. Normative text, schema,
conformance evidence, and release assessment move together.

Release candidates may change to close demonstrated correctness or safety
defects. After 1.0, the compatibility contract in specification §4 governs:
breaking changes require a major revision; additive behavior must be
discoverable. A release is tagged only after clean-room acceptance and a
reviewed READY verdict. This repository does not grant authority to publish;
publishing and remote changes remain maintainer actions.

The MIT license governs code and specification text. No trademark registration
or separate trademark-use license is asserted by this repository. Use of the
project name must not imply conformance, certification, or endorsement beyond
evidence the user can inspect.
