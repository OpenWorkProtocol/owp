# Try OWP Field Lab and the protocol boundary

Canonical field-lab URL: **https://try.openworkprotocol.org/**

Try OWP is a public experiment for putting live work items through OWP-shaped durable
state. The root **https://openworkprotocol.org/** remains the protocol/docs home.
The field lab is intentionally a separate subdomain so an experiment cannot be
confused with a conformance claim.

## What the field lab exercises

The current field-lab slice can record:

- an open GitHub pull request or a greenfield build idea;
- a requested finished outcome and a non-binding USD value signal;
- a private FIFO queue with an explicit capacity ceiling;
- provider `ACCEPT` or `PASS`;
- numbered Attempts;
- durable customer questions and answers;
- delivery evidence;
- a separately named validation actor and evidence;
- customer `APPROVE`, `STEER`, or `REJECT`;
- hash-linked event history; and
- a token-free portable handoff export.

No payment is collected, authorized, escrowed, promised, or owed. Bid/value
signals do not purchase priority or acceptance.

## What it does not prove

The field lab is **not** a claim of full OWP 1.0 conformance and is **not**
independent interoperability evidence. Its current named validation record also
does not, by itself, satisfy the RC3 Software Work Integrity Profile.

For software work covered by that profile, a conforming validator additionally
needs to establish the Attempt-bound source identity and independently verify
the exact result: base commit/tree, result commit/tree, ancestry, change set,
scope/negative policy, and the effective Definition of Done against the exact
delivered subject. If required evidence cannot be obtained or safely executed,
the result is `INDETERMINATE`, not `VALID`.

This distinction is important. The field lab is allowed to test product shape
and customer/provider workflow behavior without lowering the protocol's security
bar to match today's experiment.

## Current deployment boundary

The intended public shape is:

```text
Internet
   |
   v
try.openworkprotocol.org
   |
   v
Cloudflare Tunnel
   |
   v
127.0.0.1:8080
   |
   v
OWP Field Lab service
   |
   v
private SQLite state
```

The application listener stays on loopback. Port 8080 is not a public ingress.
Tunnel credentials, GitHub tokens, customer tracking links, databases, and
backups are private deployment material and must not be committed or pasted
into public logs.

## Relationship to future RC3 evidence

A later Field Lab revision may select the Software Work Integrity Profile. When
it does, the implementation should preserve the current human-friendly flow but
add the exact profile objects behind it:

1. agreed Work Agreement / Definition of Done digest;
2. four-role contract acceptance;
3. Attempt-specific immutable source snapshot;
4. four-role Attempt execution commitment acceptance;
5. provider Delivery Claim treated as untrusted input;
6. independent Validator Attestation over exact result commit/tree; and
7. revision/handoff starting only from validator-attested prior state.

Until those gates are implemented and externally exercised, the site must keep
the field-lab disclaimer visible.

## Self-hostable reference template

The canonical repository includes a generic copy at
[`templates/try-owp/`](../templates/try-owp/) plus
[`scripts/new-try-owp.sh`](../scripts/new-try-owp.sh). Anyone can spin up a
local field lab without the hosted deployment. The template deliberately keeps
the private queue/admin surface local-only and preserves the same experiment ≠
conformance boundary.


## Run the experiment yourself

The main repository ships a non-normative self-hostable copy of the Field Lab
shape under `templates/try-owp/`. Use `scripts/new-try-owp.sh` to render a fresh
standalone deployment with its own operator name, hostname, and durable provider
actor. The generated deployment is tested independently of the normative RC3
profile and remains subject to the same experiment/conformance boundary. See
[`docs/15-run-your-own-try-owp.md`](15-run-your-own-try-owp.md).
