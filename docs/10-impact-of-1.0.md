# Migration to Open Work Protocol 1.0-rc2

This document identifies compatibility changes and required migration actions
for implementations built against OWP 0.3 or 1.0-rc1.

## Version compatibility

OWP 1.0-rc2 supersedes 1.0-rc1 and is not wire-compatible with it. A conforming
RC2 surface reports `1.0-rc2`. A request pinned to RC1 receives
`UNSUPPORTED_VERSION` unless the deployment separately implements the RC1
contract.

## Required RC1 to RC2 changes

| Area | RC2 requirement | Migration action |
|---|---|---|
| Cancellation | `work.cancel` and terminal state/event `cancelled` are part of the core contract. | Add cancellation handling to schemas, storage, clients, and state transitions. |
| Request media type | HTTP POST requests use `application/json`. | Set and validate `Content-Type: application/json`. |
| Request size | HTTP request bodies are limited to 1 MiB. | Reject oversized bodies before protocol dispatch. |
| Mutation recovery | Retried mutations use `Idempotency-Key`. | Persist actor-scoped request hashes and exact results atomically with the mutation. |
| Client deadlines | Client and proxy requests use bounded deadlines. | Add cancellation-aware request timeouts and bounded retry behavior. |
| Version negotiation | Unsupported pins return `UNSUPPORTED_VERSION`. | Branch on the error and select only a revision implemented by both parties. |

## Required 0.3 to RC2 changes

| Area | Previous behavior | RC2 behavior |
|---|---|---|
| Attention result | Bare array or page envelope | Always `{rows, cursor, total, more}` |
| Attention cursor | Integer position | Opaque keyset token returned by the surface |
| Item-read authority | Agent access permitted | Operator or authorized creator-client access |
| Discovery | Deployment-specific | `surface.describe` reports revision, features, authority, grants, and vocabulary |
| Structure updates | Limited fields | `work.update` supports `intent`, `depends_on`, and `kind`; `work.reprioritize` supports `urgency` |
| Fleet projection | Not defined | `sessions` and `session.view` |
| Event authorship | `session` | `actor`, with `session` retained as a deprecated alias for the stated compatibility period |

Clients must read `attention().rows`, treat cursors as opaque, obtain assignment
data through the assignment packet, and use an appropriate operator or creator
grant for item reads.

## Behavioral requirements

- Assignment ordering is total and exposes the creation ordinal required for
  conformance testing.
- The surface does not author explanatory prose on behalf of clients.
- Grants compose as a union across grants and an intersection of constraints
  within each grant.
- No actor may decide its own output, including completion proposals and
  questions.
- Attention ordering is total across rows, including rows with identical
  primary sort fields.
- Transport failure is distinct from a protocol error and is never converted
  into terminal work state.

## Validation

After migration, regenerate implementation types from the RC2 schema, run the
implementation test suite, and run the wire conformance suite with distinct
operator and agent credentials. A deployment must advertise only the protocol
revisions it implements.
