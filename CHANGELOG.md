# Revision history

- Expanded the self-hostable `templates/try-owp/` surface to cover PR and greenfield-idea Field Lab flows, added deployment identity rendering and 58-test generated-instance validation, Caddy/Cloudflare ingress examples, and repo-wide docs/site links while preserving experiment/conformance and private-admin security boundaries.
- Added a permanent repository-local Markdown link gate and aligned Field Lab handoff/profile metadata with the RC3 development candidate while preserving the explicit non-conformance claim.

## 1.0-rc3 — 2026-08-21 (development candidate)

RC3 preserves the RC2 core state machine and HTTP verb semantics while adding a
normative optional Software Work Integrity Profile.

### Software work integrity

- Requires customer + provider + orchestrator + independent OWP validator to
  accept the same Definition of Done contract digest before execution.
- Binds an exact Git base commit/tree to every Attempt, including revisions and
  cross-provider handoffs.
- Treats provider Delivery Claims as untrusted input until independently
  reconstructed.
- Requires exact-result commit/tree subject binding for deterministic test/build
  evidence and fail-closed `INDETERMINATE` when required validation cannot run.
- Chains revisions from validator-attested prior state and requires paid STEER
  acceptance deltas to be evaluated, not merely hashed.

### Interoperability refresh

- Aligns A2A notes to released A2A 1.0 task/extension semantics.
- Reuses SLSA 1.2 and in-toto attestation/test-result concepts rather than
  defining duplicate supply-chain formats.
- Refreshes optional commerce/trust notes for x402 v2, AP2 v0.2, and ERC-8004.

### Executable evidence

- Adds 7 static profile vectors and 21 dynamic adversarial/real-Git tests.
- Adds a dependency-free verifier capable of exact base/tree/ancestry/diff/scope
  validation and fresh-checkout deterministic command execution.
- Expands the generated normative inventory to include the selected profile.

### Public surfaces and security documentation

- Makes `https://openworkprotocol.org/` the current project/docs namespace and
  corrects unpublished RC3 profile/schema identifiers from the earlier `.io`
  draft namespace.
- Documents `https://try.openworkprotocol.org/` as a deliberately non-conformant
  Field Lab rather than presenting the experiment as the protocol.
- Adds a static main website with a prominent Try OWP path, exact-base security
  explainer, release-claim boundaries, and pinned GitHub Pages actions.
- Adds repo-wide URL/surface consistency checks and website smoke validation.
- Credits [grogugo](https://github.com/grogugo) for security feedback that
  influenced the exact-base/untrusted-worker security work.

### Claim boundary

RC3 is ready for implementation review, not yet a published interoperability
release. The external reference repos and an unrelated independent validator /
provider handoff remain release gates.

## 1.0-rc2 — 2026-08-08

RC2 supersedes RC1 and closes correctness, recovery, and loopback security
findings identified during release validation.

### Core protocol

- Added terminal cancellation through `work.cancel` and state/event
  `cancelled`.
- Clarified registered names, extension preservation, state transitions,
  assignment ordering, authority scope, and error recovery.
- Added explicit claim boundaries for shared-reference evidence and
  independent interoperability.

### HTTP binding

- Added actor-scoped mutation idempotency and exact replay behavior.
- Required JSON POST requests and a 1 MiB request-body limit.
- Added origin validation and browser-facing response hardening.
- Defined bounded deadlines, retry behavior, and transport-failure handling.

### Reference artifacts

- Published a reproducible machine-readable schema.
- Expanded authenticated wire conformance to 50 obligations.
- Added explicit signal handling and orderly resource shutdown.
- Recorded exact provenance for reference-runtime copies embedded in the four
  domain examples.

### Compatibility

RC2 is not wire-compatible with RC1. Implementations must follow the
[migration guide](docs/10-impact-of-1.0.md) and advertise only the revisions
they implement.

## 1.0-rc1

RC1 introduced the 1.0 lifecycle, discovery, bounded projections, authority
classes and grants, machine-readable schema, and normative HTTP binding. It is
superseded by RC2.

## 0.3

Version 0.3 was the pre-release design baseline. It is retained only as project
history and is not a supported protocol target.
