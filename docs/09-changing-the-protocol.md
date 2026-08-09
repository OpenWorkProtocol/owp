# Protocol change policy

This policy defines the evidence and compatibility requirements for changing
the Open Work Protocol specification.

## Admission criteria

A proposed protocol change must satisfy at least one of these criteria:

1. Two unrelated deployment domains require the same interoperable behavior.
2. An existing protocol invariant cannot be implemented or tested consistently
   without the change.
3. A correctness or security defect requires clarification or remediation.

Deployment-specific nouns, presentation, scheduling, evaluation, notification,
and automation remain outside the protocol unless independent evidence shows
that portable implementations require a shared contract.

## Proposal requirements

A proposal must include:

- the behavior that cannot be represented by the current contract;
- reproducible evidence or a failing observable-behavior test;
- affected normative requirements and compatibility impact;
- evidence from a second unrelated domain when the proposal adds capability;
- the smallest compatible representation; and
- corresponding specification, schema, conformance, and migration updates.

The preferred representation order is an extension value, a field on an
existing envelope, a new verb, and finally a new record type. Larger changes
require evidence that the smaller representation cannot preserve the intended
guarantee.

## Review and disposition

Maintainers record one of the following dispositions:

- **Accepted:** the proposal satisfies the admission criteria and all required
  artifacts are updated.
- **Deferred:** the evidence is credible but insufficient for a portable
  protocol requirement.
- **Deployment-specific:** the behavior belongs in local vocabulary or a
  client implementation.
- **Rejected:** the proposal conflicts with protocol scope, invariants, or
  compatibility guarantees.

The disposition record must identify the evidence, rationale, compatibility
effect, and any minority position. A reference implementation change alone is
not sufficient evidence for a normative change.

## Experimental features

An experimental feature may change or be removed in a later revision. A
surface declares implemented experimental features through
`surface.describe`. Graduation requires:

- two independent implementations;
- sustained operational use; and
- no unresolved ambiguity in behavior, routing, authority, or recovery.

## Registered names

A registered extension name requires the same shape and semantics in at least
two deployments. Until registration, names remain deployment-local and do not
carry interoperability guarantees.

## Revision rules

Additive optional behavior is discoverable through `surface.describe`.
Breaking verb, state, error, or invariant changes require a major protocol
revision. Renamed fields remain available under the deprecated name for at
least the compatibility period stated by the specification.
