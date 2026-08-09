# Revision history

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
