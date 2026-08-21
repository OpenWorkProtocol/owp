# Open Work Protocol 1.0-rc3 candidate record

Candidate date: **2026-08-21**

This is a development candidate record, **not a publication record**. The last
published release remains `v1.0-rc2` until the RC3 implementation and independent
interop gates in `RELEASE_READINESS.md` are satisfied.

## Candidate purpose

Apply exact-source, untrusted-worker, and handoff trust guarantees to software
work without changing OWP's core surface boundary.

## Candidate additions

- `spec/owp-1.0-rc3.md`
- `spec/annex-http-1.0-rc3.md`
- `spec/annex-software-work-integrity-1.0-rc3.md`
- six machine-readable profile schemas
- dependency-free canonical digest/profile verifier
- adversarial real-Git test suite
- static portable vectors
- A2A 1.0, SLSA/in-toto, x402 v2, AP2 v0.2, and ERC-8004 alignment notes
- updated requirement/conformance inventory and CI

## Cardinal invariant

> No software delivery covered by the profile may be treated as independently
> valid unless an independent validator reconstructs the result from an
> Attempt-bound immutable source snapshot and binds every deterministic/evidence
> result to the exact delivered Git commit/tree.

## Definition of Done contract gate

Before the contract is accepted, the customer, provider, orchestrator, and
independent OWP validator must all acknowledge the same contract digest. Before
each Attempt is accepted for execution/funding, the same four roles must also
acknowledge the exact Attempt execution-commitment digest, including its immutable
source snapshot and any bounded acceptance delta. The validator acknowledgements
are preflight statements that the objective completion boundary is independently
judgeable, not promises that a future delivery will pass.

## Handoff gate

Every revision/provider handoff begins from the prior validator-attested result
commit/tree and binds the prior customer disposition. Provider-reported branch tips
or summaries are not treated as portable trusted state without validation.


## Public project surfaces

- Protocol/docs home: `https://openworkprotocol.org/`
- Try OWP Field Lab: `https://try.openworkprotocol.org/`
- Canonical specification source: `https://github.com/OpenWorkProtocol/owp`

The Try site is a live workflow field experiment and remains outside the RC3
conformance claim until it implements and proves the selected profile gates.

## Security-design acknowledgment

The exact-base/untrusted-worker security work was influenced by a verification
question raised by [grogugo](https://github.com/grogugo). See `ACKNOWLEDGMENTS.md`.


## Non-normative try surface

The candidate repository also ships a self-hostable Try OWP field-lab template
covering PR and greenfield-idea intake. Its generated instance passes 58 template
tests, including provider-identity rendering. It is product/example evidence only
and is not counted as normative RC3 conformance or independent interoperability
evidence.
