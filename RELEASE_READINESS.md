# Open Work Protocol 1.0-rc3 development readiness

Assessment date: **2026-08-21**
Release status: **Development candidate; RC2 remains the last published release**
Assessment result: **READY FOR IMPLEMENTATION REVIEW**

## Scope of this assessment

RC3 preserves the 1.0-rc2 core lifecycle and HTTP binding semantics and adds a
normative optional **Software Work Integrity Profile**. The profile addresses
exact-base and untrusted-worker software delivery without making the OWP surface
Git-aware.

This repository now contains executable spec-local evidence for the new profile.
It does **not** yet contain upgraded copies of the external `owp-code`, domain
example, independent provider, or hardened production validator implementations.
Therefore RC3 is not represented as a published interoperable release.

## Spec-local qualification

| Evidence | Result |
|---|---:|
| Normative RFC 2119 occurrences inventoried | 256/256 |
| Static Software Work Integrity vectors | 7/7 |
| Dynamic adversarial/real-Git profile tests | 21/21 |
| Requirement/matrix reproducibility | PASS |
| Profile JSON schemas parse | PASS |
| Exact Git SHA-1/SHA-256 length policy | PASS |
| Four-party Definition of Done consensus gate | PASS |
| Attempt-specific exact source commitment | PASS |
| Exact-result in-toto test subject binding | PASS |
| Revision/handoff from validator-attested result only | PASS |
| Project URL / RC3 namespace consistency | PASS |
| Static main-site smoke and local-link validation | PASS |
| Documentation local-link integrity | PASS |
| Generated Try OWP template smoke | 58/58 |

## Threats exercised locally

The dynamic suite proves rejection of:

- provider-claimed base mismatch;
- abbreviated Git object ids;
- actual base-tree mismatch;
- result-tree substitution;
- tests run on a different result commit;
- missing deterministic test evidence;
- stale/tampered deterministic test evidence digest;
- incomplete four-party contract consensus;
- provider self-validation under an independence requirement;
- split contract-digest acknowledgement;
- incomplete/split Attempt execution-commitment consensus;
- delivery bound to the wrong Attempt;
- paid STEER acceptance delta omitted from validation;
- deterministic command execution without explicit validator permission;
- required execution/isolation that the reference verifier cannot honestly provide (classified `INDETERMINATE`);
- forbidden/out-of-scope changed paths;
- unrelated result history;
- revision/handoff starting from something other than the prior
  validator-attested result;

The positive path creates a temporary Git repository, verifies commit/tree
identity and ancestry, hashes the canonical exact base-to-result change set, fresh-clones the result,
checks out the exact commit/tree, and runs the deterministic Definition of Done.

## External standards alignment

The profile was refreshed against current public specifications on 2026-08-21:

- A2A 1.0.0;
- SLSA 1.2 Source/Build tracks;
- in-toto Attestation v1.2 and Test Result v0.1 predicate;
- x402 Protocol v2;
- AP2 v0.2 public specification;
- ERC-8004.

Informative mapping notes live under `interop/`. External standards remain their
own source of truth.

## Public surface status

The root website remains the protocol/docs entry point at
`https://openworkprotocol.org/`. The separate Field Lab at
`https://try.openworkprotocol.org/` is explicitly labeled as an experiment and
does not count as independent RC3 conformance or interoperability evidence.

## Remaining release gates

| ID | Severity | Gate | Why it remains |
|---|---|---|---|
| RC3-G01 | High | Upgrade `owp-code` and its wire/schema conformance kit to advertise and round-trip the profile vocabulary. | This ZIP contains the spec repository only. |
| RC3-G02 | High | Run the profile with an independently controlled Git validator against an unrelated provider/orchestrator. | Local tests separate roles logically but execute on one machine. |
| RC3-G03 | High | Demonstrate a cross-provider STEER/handoff whose second Attempt starts from the first independent validator-attested tree. | Required to prove the central portability claim outside fixtures. |
| RC3-G04 | Medium | Exercise a hardened disposable build sandbox with untrusted repository inputs and no ambient credentials. | The dependency-free verifier uses a fresh clone but the fixture runner is not a production sandbox. |
| RC3-G05 | Medium | Add external TCK runs, including at least one independently authored implementation. | Independent interoperability remains unproven. |
| RC3-G06 | Medium | Validate one A2A 1.0 transport binding and, separately, one payment/authority binding if claimed by a deployment. | Interop docs are informative; no external service is bundled here. |

No remaining gate is hidden behind a `PASS`. RC3 may be pushed for review and
implementation work now; it MUST NOT be tagged/published as the final 1.0
release on the strength of this repository alone.

## Reproduction

```sh
node tools/build-requirement-matrix.mjs
git diff --exit-code -- REQUIREMENTS.json CONFORMANCE_MATRIX.md
node tools/test-software-work-integrity-vectors.mjs
node tools/test-software-work-integrity.mjs
node tools/test-project-surface.mjs
node tools/test-site.mjs
node tools/test-doc-links.mjs
node -e 'for (const f of require("fs").readdirSync("schemas")) JSON.parse(require("fs").readFileSync("schemas/"+f,"utf8")); console.log("schemas parse")'
```

## Determination

**READY FOR IMPLEMENTATION REVIEW.** The new normative profile is internally
coherent and executable at the spec/reproducibility level. A truthful published
RC3 interoperability claim waits on the external gates above.


## Non-normative try surface

The candidate repository also ships a self-hostable Try OWP field-lab template.
A rendered instance passes 58 template tests. This remains product/example
evidence and is not counted as normative RC3 conformance or independent
interoperability evidence.
