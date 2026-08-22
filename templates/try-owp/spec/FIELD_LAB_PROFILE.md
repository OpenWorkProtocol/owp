# OWP Field Lab Profile 0.1

Status: **field-lab profile; not a normative Open Work Protocol revision and not a conformance claim.**

This profile defines a small public workflow for exercising Open Work Protocol ideas with external requests and work items at `__OWP_PUBLIC_HOSTNAME__`.

## Purpose

The field lab exercises one portability property:

> A work item should remain understandable, steerable, evidenced and portable even when the agent or provider doing the work changes.

Provider-internal execution details remain outside the public work record. The field
lab records only the portable request, lifecycle decisions, evidence, disposition, and
handoff state.

## Roles

- **Customer** — submits work, answers durable questions, and approves, steers or rejects a valid delivery.
- **Provider/operator** — __OWP_OPERATOR_NAME__; privately reviews the queue, explicitly accepts or passes, performs the work, and records delivery evidence.
- **Validator actor** — a separately named validation record with evidence. The profile records separation from delivery but does not prove organizational independence.
- **Surface** — the public HTTP service plus the private SQLite work store.

## Work types

Exactly two intake types exist in 0.1.

### `github_pr`

Required:

- open `https://github.com/<owner>/<repo>/pull/<number>` URL;
- requested finished outcome;
- USD value signal;
- authorization/data-use attestation.

The surface verifies the PR through GitHub's public API and snapshots its current head and size metadata. The PR is re-verified when an attempt begins.

### `idea`

Required:

- short idea title;
- requested finished outcome;
- USD value signal;
- authorization/data-use attestation.

Optional:

- one HTTPS context URL.

An idea does not receive invented repository metadata. If implementation later creates a repository or PR, that evidence can be attached to delivery/handoff records.

## Commercial signal

`value_signal_usd` records the customer-provided estimate of the outcome's value. It is research metadata only.

The profile has no payment collection, escrow, debt, payout, provider auction, or bid-based queue ordering. Value never changes FIFO order and never guarantees acceptance.

## Working set

The private active working set is capped at 20 items. Capacity is enforced transactionally. The public surface exposes only aggregate occupancy.

Active states:

- `proposed` — submitted, provider decision pending;
- `todo` — accepted or steered and ready for an attempt;
- `in_progress` — an attempt is active;
- `parked` — waiting on a customer answer;
- `review` — delivery is awaiting or has valid validation and customer disposition.

Terminal states:

- `completed` — customer approved a valid delivery;
- `cancelled` — provider passed or customer rejected.

## Provider actions

- `accept` — explicit decision to take the work;
- `pass` — explicit terminal refusal with reason;
- `start` — begins the next numbered attempt; re-verifies PR work first;
- `ask` — parks active work on a durable question containing at least two options and optional HTTPS evidence;
- `deliver` — records a delivery summary and HTTPS evidence;
- `validate` — records `valid` or `invalid`, a named validator label and HTTPS evidence.

Invalid validation returns the item to `in_progress` for repair.

## Customer actions

Customer actions require the high-entropy claim token returned at intake.

- `answer` — selects one offered option; resumes parked work;
- `approve` — completes a valid delivery;
- `steer` — supplies an instruction and returns the item to `todo` for a new numbered attempt;
- `reject` — supplies a reason and closes the item;
- `export_handoff` — downloads the current token-free portable work record.

## Evidence and history

Every state mutation appends a SHA-256 hash-linked event. The database can verify the complete chain for each work item and `/healthz` fails if SQLite integrity or an event chain fails.

Hash linking is tamper detection inside this deployment, not a claim of external notarization. An attacker with unrestricted database rewrite access could rewrite records and hashes; private backups provide a separate comparison point.

## Portability record

The handoff JSON includes:

- field-lab profile identifier;
- export time and chain-verification result;
- work source and requested outcome;
- value signal;
- lifecycle state and attempt number;
- questions and durable customer answers;
- complete event history, including evidence URLs.

It never includes the customer claim token or its stored hash.

## HTTP surface

Public:

- `GET /`
- `GET /privacy`
- `GET /healthz`
- `GET /api/status`
- `GET /api/live`
- `GET /api/owp/describe`
- `POST /api/submissions`

Customer-token protected:

- `GET /api/work/<OWP-ref>`
- `GET /api/work/<OWP-ref>/handoff`
- `POST /api/work/<OWP-ref>/answer`
- `POST /api/work/<OWP-ref>/disposition`

There is deliberately no remote operator/admin HTTP API. Operator mutations are local CLI actions against the private work store.

## Security boundary

The public web process must not clone or execute customer repositories. It records requests, GitHub metadata, decisions and evidence only. Provider work occurs in the operator's separate tooling/environment.

The included deployment binds Python to loopback behind HTTPS and runs the service unprivileged with read-only source and a private writable data directory.

## Relationship to Open Work Protocol

This profile exercises OWP concepts—durable work, explicit assignment/decision boundaries, questions and decisions, evidence-backed completion, operator/customer separation and portable handoff—without claiming that this application implements every normative requirement of Open Work Protocol 1.0-rc3 development candidate.

The canonical protocol remains authoritative: <__OWP_PROTOCOL_URL__>.
