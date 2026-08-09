# Example coverage

The OWP release includes five runnable repositories selected to exercise the
same protocol contract across materially different domains. All five use the
shared reference implementation.

## Coverage summary

| Repository | Domain | Primary protocol coverage | Operator interface |
|---|---|---|---|
| `owp-code` | Software development | Atomic assignment, concurrent sessions, review, collision recovery, conformance | Operator console |
| `owp-desk` | Freight operations | Transaction chains, entity links, financial authority, external waits, high-volume intake | Load board |
| `owp-ops` | Infrastructure operations | Observations, proposals, maintenance triggers, staged execution, rollback | Estate board |
| `owp-publish` | Editorial production | Retrieval, citations, continuity, author authority, non-linear work | Writing room |
| `owp-research` | Research | Source catalog, deduplication, attributed claims, contradictions, scope policy | Briefing room |

## Cross-domain coverage

The examples validate these cross-domain properties:

1. Domain vocabulary remains in deployment-owned links and knowledge records;
   the surface does not interpret domain nouns.
2. Work state and event history remain durable across process and session
   boundaries.
3. Questions can wait for operator input without preventing unrelated work.
4. Authority is expressed through actor classes and scoped grants rather than
   domain-specific permissions.
5. Operator projections remain bounded and provide enough context to select an
   action without transferring the entire work history.
6. Creator clients own clocks, observation cursors, scheduling, and external
   side effects; the protocol surface does not act autonomously.

## Evidence boundary

The examples provide evidence of reference behavior in multiple domains. They
are not independent implementations because each embeds or invokes the same
reference surface. Independent interoperability remains unverified until a
separately authored surface passes the wire conformance suite and exchanges
work successfully with an independently authored client.

## Reproduction

Each repository contains:

- a lockfile-based installation procedure;
- an automated test suite;
- a release evidence summary in `EVIDENCE.md`;
- an operator acceptance runbook in `docs/deploy.md`; and
- an embedded-runtime provenance record where applicable.

Validation commands and aggregate results are recorded in
[`RELEASE_READINESS.md`](../RELEASE_READINESS.md).
