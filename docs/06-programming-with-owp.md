# Implementing with Open Work Protocol

The specification defines shared envelopes, lifecycle, invariants, and
observable behavior. An OWP deployment supplies the domain vocabulary,
operator experience, agent instructions, delivery binding, and creator
clients.

## Responsibility boundary

| Protocol responsibility | Deployment responsibility |
|---|---|
| Deliverables, sessions, events, parks, policies, and completion records | Domain records and terminology |
| Atomic claim and deterministic assignment | Agent runtime and execution environment |
| Questions, decisions, continuations, and review | Domain-specific approval policy |
| Bounded attention, portfolio, item, and session projections | Operator interface and presentation |
| Authority classes and scoped grants | Identity provider and credential lifecycle |
| Discovery and normative errors | Transport selection and service topology |
| Conformance requirements | Deployment acceptance and monitoring |

Behavior belongs in the protocol when independent implementations require the
same observable contract. Behavior belongs in a deployment when it can be
represented through an existing envelope or client without altering shared
semantics.

## Domain vocabulary

Deployments define values for link types, deliverable kinds, policy types,
continuations, and optional assignment tiebreaks. Vocabulary must be published
through `project.create({vocabulary})` and returned by `surface.describe`.

Names should describe domain roles rather than specific products. A
deliverable may carry multiple link types when each type has a distinct
meaning. Local names do not acquire interoperability semantics unless they are
registered according to the protocol change policy.

## Operator experience

The specification defines projections rather than screens. Operator clients
may use dashboards, documents, terminal views, command-line output, or another
presentation appropriate to the deployment.

Operator clients should:

- render the `action` field as the operation that clears an attention row;
- treat `reason` as explanatory text rather than a control discriminator;
- avoid presenting an action that belongs to a different actor;
- use `totals` for aggregate presentation without exhausting the queue;
- provide the evidence and policy context required for a decision; and
- preserve bounded reads and opaque cursors.

No operator interface has normative status. A conforming client uses the same
published verbs and projections as every other client.

## Agent binding

An agent binding defines operational instructions for sessions, including:

- registration and assignment acquisition;
- progress and status reporting;
- question evidence and option construction;
- parking and handoff quality;
- completion record content;
- review boundaries; and
- domain-specific policy interpretation.

Agent-local scratch state is not part of the protocol record. Information
needed by another session or the operator must be written to the applicable
deliverable, event, question, park, link, or completion record.

## Delivery binding

The core protocol is binding-independent. A deployment selects how clients
reach the surface and how callers authenticate. Implementations using the
published HTTP and JSON binding must follow Annex A.

Loopback open mode is intended for local evaluation. Routable deployments
require TLS, authenticated actor classes, protected operator clients, scoped
credentials, request limits, and deployment-owned identity lifecycle controls.

## Creator clients

Scheduling, observation, notification, and external side effects belong to
clients. Examples include schedulers that create proposals, watchers that
report drift, and janitors that release abandoned claims.

A creator client maintains its own clock and observation cursor, uses a scoped
grant, and records mutations through protocol verbs. The reference watcher in
`owp-ops/src/watcher.ts` accepts deployment vocabulary as input and returns the
created references keyed by observation identity; it does not introduce
protocol-level domain vocabulary.

## Protocol boundary evaluation

Evaluate a proposed shared behavior in this order:

1. Determine whether a second unrelated domain requires the same semantics.
2. Determine whether the behavior can use an existing extension envelope.
3. Determine whether an existing invariant requires a shared interpretation.
4. Determine whether omitting the behavior would make independently authored
   clients or surfaces incompatible.

Proposals that change the shared contract follow
[`09-changing-the-protocol.md`](09-changing-the-protocol.md).

## Conformance validation

The conformance suite evaluates observable behavior through the selected
binding and does not access implementation internals:

```sh
node conformance/run.ts https://surface.example \
  --operator-token "$OWP_OPERATOR_TOKEN" \
  --agent-token "$OWP_AGENT_TOKEN"
```

Each result identifies the applicable specification section. Unit tests remain
necessary for implementation correctness but do not replace wire-level
conformance evidence.
