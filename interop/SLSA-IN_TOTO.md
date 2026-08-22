# SLSA 1.2 and in-toto attestation alignment (informative)

Checked 2026-08-21.

References:

- SLSA 1.2: https://slsa.dev/spec/v1.2/
- SLSA Source requirements: https://slsa.dev/spec/v1.2/source-requirements
- in-toto Attestation v1.2: https://github.com/in-toto/attestation/tree/main/spec/v1
- in-toto Test Result: https://github.com/in-toto/attestation/blob/main/spec/predicates/test-result.md

The Software Work Integrity Profile intentionally reuses supply-chain evidence
rather than defining a separate OWP build-provenance format.

- SLSA Source can provide source-control provenance and verification summaries
  about how a revision came to exist. OWP does not assign SLSA Source levels.
- SLSA Build provenance can describe how a build output was produced from
  source. OWP may require it as contract evidence but does not redefine it.
- SLSA Source VSAs use a revision digest such as `gitCommit` and may include
  `gitTree`. OWP's validator subject uses the same commit/tree identity distinction.
- in-toto Statement v1 is the preferred envelope for the OWP validator
  attestation.
- in-toto's Test Result predicate is preferred when expressing ordinary test
  outcomes; its subject is the exact source artifact tested. OWP additionally
  requires that subject to equal the delivered result commit/tree.

OWP does not add another provenance format. It adds a
work-contract rule that links an agreed Definition of Done and an Attempt's
exact starting snapshot to independently re-checkable supply-chain evidence.
