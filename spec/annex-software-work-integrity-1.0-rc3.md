# Annex B — Software Work Integrity Profile (normative, 1.0-rc3)

Status: **Normative optional profile** for deployments that declare
`software_work_integrity` through `surface.describe().features`.

This annex answers one narrow but high-consequence question:

> How can a customer know that a returned software patch was derived from the
> exact source state that was agreed before execution, that the delivered Git
> tree is the tree independently tested, and that a handoff cannot promote an
> unverified provider claim into trusted shared state?

The profile composes with OWP Core. It does not make the OWP surface a Git
server, build service, payment rail, or trust oracle. The surface continues to
store and round-trip envelopes and to record client actions. Contract authors,
providers, orchestrators, validators, customer clients, source-control systems,
build systems, and payment/authority systems produce and interpret the evidence.

The key words **MUST**, **MUST NOT**, **SHOULD**, **SHOULD NOT**, and **MAY** are
to be interpreted as described in BCP 14 when, and only when, they appear in
all capitals.

---

## B.1 Profile boundary and actors

A software-integrity flow has four agreement roles:

1. **Customer** — the human operator or authorized customer client that owns the
   requested outcome and final disposition.
2. **Provider** — the party accountable for supplying the delivery claim.
3. **Orchestrator** — the execution authority that assigns and supervises the
   provider-side work. It may internally use any agents, models, tools, or
   workers.
4. **OWP validator** — an independently controlled validator that determines
   whether the evidence policy and deterministic Definition of Done can be
   verified and later validates the returned result.

The provider and orchestrator MAY be operated by the same organization. The OWP
validator MUST be controlled independently of both for a flow that claims
`independent_validation: true`.

The protocol never assumes an execution worker is trustworthy. A provider,
orchestrator, subagent, CI job controlled by them, or worker-produced manifest
MUST be treated as a **claim source**, not as validation authority.

A deployment MUST NOT call a delivery independently validated merely because a
provider signed it, a CI system under provider control reported success, a
payment settled, or the event ledger preserved the claim without modification.

---

## B.2 Registered profile link types

A deployment selecting this profile SHOULD publish these globally scoped link
types in its project vocabulary:

- `https://openworkprotocol.org/links/software-work/agreement/v1`
- `https://openworkprotocol.org/links/software-work/execution/v1`
- `https://openworkprotocol.org/links/software-work/delivery/v1`
- `https://openworkprotocol.org/links/software-work/validation/v1`
- `https://openworkprotocol.org/links/software-work/disposition/v1`

A link entry SHOULD contain an immutable artifact URI when one exists and MUST
contain the digest required by the relevant section below. The OWP surface MUST
round-trip these entries exactly and MUST NOT interpret their Git, test,
payment, or attestation semantics.

The profile link types are additive registered envelope values under Core §4.2.
They do not add core verbs or alter the core state machine.

---

## B.3 Canonical profile digests

Every `sha256:` digest defined by this profile is over RFC 8785 JSON
Canonicalization Scheme (JCS) bytes, then SHA-256, rendered as lowercase
`sha256:<64 lowercase hex>`.

To keep the profile deterministic in simple implementations, a hashed profile
object:

- MUST use printable ASCII object/property names;
- MUST NOT contain JSON floating-point numbers;
- MUST use decimal strings for monetary values;
- MUST use integers only inside the interoperable IEEE-754 safe-integer range;
- MUST preserve Unicode string values exactly as JCS requires.

An implementation MUST reject a claimed digest whose canonical payload does not
recompute to the claim.

---

## B.4 Definition of Done and four-party agreement

### B.4.1 Contract body

Before the first paid or otherwise authorized execution Attempt, the parties
MUST agree on one immutable `contract_body` containing at least:

```json
{
  "profile": "https://openworkprotocol.org/profiles/software-work-integrity/v1",
  "work_ref": "PAY-4",
  "outcome": "Implement retry logic without changing unrelated behavior.",
  "definition_of_done": [
    {
      "id": "native-tests",
      "tier": "deterministic",
      "statement": "Repository native tests pass from a fresh checkout.",
      "command": "npm test"
    }
  ],
  "scope": {
    "allowed_paths": ["src/**", "test/**"],
    "forbidden_paths": [".github/**", ".env", "secrets/**"]
  },
  "evidence_policy": {
    "independent_validation": true,
    "fresh_environment": true,
    "require_exact_result_subject": true,
    "require_diff_review": true
  }
}
```

Each Definition-of-Done item MUST have a stable `id`, a tier, and an objective
statement. Deterministic items MUST additionally describe an executable command
or an equivalently precise machine policy. Evidence-backed items MUST describe
the evidence and integrity check. Human-judged items MUST be explicitly marked
`human` and MUST NOT be misrepresented as machine-validated.

The contract body MUST distinguish objective delivery validity from final
customer preference. A validator's `VALID` result MUST NOT be treated as a
customer `APPROVE` decision.

### B.4.2 Contract digest and acknowledgements

`contract_digest` is the canonical digest of `contract_body` only. Agreement
acknowledgements are outside that digest to avoid a circular object.

A Work Agreement is accepted only when all four roles have acknowledged the
**same** `contract_digest`:

```json
{
  "contract_body": { "...": "..." },
  "contract_digest": "sha256:...",
  "acknowledgements": [
    {"role":"customer", "actor_id":"customer:acme", "decision":"ACCEPT", "contract_digest":"sha256:..."},
    {"role":"provider", "actor_id":"provider:alpha", "decision":"ACCEPT", "contract_digest":"sha256:..."},
    {"role":"orchestrator", "actor_id":"orchestrator:alpha", "decision":"ACCEPT", "contract_digest":"sha256:..."},
    {"role":"owp_validator", "actor_id":"validator:independent", "decision":"ACCEPT", "contract_digest":"sha256:..."}
  ]
}
```

The customer MUST acknowledge that the Definition of Done expresses the desired
outcome and customer-owned human criteria.

The provider MUST acknowledge that it is willing to deliver against that exact
Definition of Done.

The orchestrator MUST acknowledge that it can provision and supervise an
execution capable of satisfying the required evidence policy.

The independent OWP validator MUST acknowledge **preflight verifiability**: the
machine/evidence criteria are sufficiently precise to validate, the required
source and execution evidence can be obtained independently, and no criterion
requires trusting a provider assertion as its own proof.

The validator acknowledgement is not a promise that future work will pass; it
is agreement that the contract has a valid, independently judgeable completion
boundary.

A contract MUST NOT be considered accepted when any required role is absent,
uses a different `contract_digest`, or returns anything other than `ACCEPT`.

---

## B.5 Attempt-specific execution commitment

A Work Agreement defines the outcome across Attempts. The exact starting Git
state can change on every revision or provider handoff. Therefore the immutable
source snapshot MUST be bound to **each Attempt**, not only to the Work
Agreement.

Before an Attempt begins, the customer/provider/orchestrator/validator workflow
MUST produce an `execution_commitment` containing at least:

```json
{
  "profile": "https://openworkprotocol.org/profiles/software-work-integrity/v1",
  "work_ref": "PAY-4",
  "attempt_id": "attempt-2",
  "revision": 1,
  "contract_digest": "sha256:...",
  "provider_id": "provider:beta",
  "orchestrator_id": "orchestrator:beta",
  "source_snapshot": {
    "repository_uri": "https://github.com/example/repo",
    "object_format": "sha1",
    "base_commit": "0123456789abcdef0123456789abcdef01234567",
    "base_tree": "89abcdef0123456789abcdef0123456789abcdef"
  },
  "acceptance_delta": [],
  "parent": null
}
```

`object_format` MUST be `sha1` or `sha256` for this version of the Git profile.
A SHA-1 object identifier MUST contain exactly 40 lowercase hexadecimal
characters. A SHA-256 object identifier MUST contain exactly 64 lowercase
hexadecimal characters. Abbreviated object identifiers MUST NOT be used in a
normative execution commitment.

The source snapshot MUST identify the exact commit **and** tree expected before
execution. A branch, tag, pull-request number, symbolic ref, or moving name MAY
be retained as human context but MUST NOT replace the immutable object IDs.

`execution_commitment_digest` is the canonical digest of the execution
commitment.

### B.5.1 Attempt acceptance

The Work Agreement establishes the shared Definition of Done, but it does not
by itself accept a moving source snapshot or a later paid STEER. Before **every**
Attempt, all four agreement roles MUST acknowledge the same
`execution_commitment_digest`:

```json
{
  "execution_commitment_digest": "sha256:...",
  "acknowledgements": [
    {"role":"customer", "actor_id":"customer:acme", "decision":"ACCEPT", "execution_commitment_digest":"sha256:..."},
    {"role":"provider", "actor_id":"provider:beta", "decision":"ACCEPT", "execution_commitment_digest":"sha256:..."},
    {"role":"orchestrator", "actor_id":"orchestrator:beta", "decision":"ACCEPT", "execution_commitment_digest":"sha256:..."},
    {"role":"owp_validator", "actor_id":"validator:independent", "decision":"ACCEPT", "execution_commitment_digest":"sha256:..."}
  ]
}
```

The customer acknowledgement confirms the exact Attempt source and any
customer-requested acceptance delta. The provider accepts execution against that
snapshot. The orchestrator accepts responsibility for provisioning that exact
Attempt. The independent validator confirms that the source snapshot can be
obtained through its controlled path and that the effective acceptance set
remains independently judgeable.

An Attempt MUST NOT be treated as accepted, funded for execution, or started
under this profile when any role is absent, acknowledges a different digest, or
returns anything other than `ACCEPT`.

Payment receipts, spending mandates, capability grants, or other authority
artifacts SHOULD bind to `execution_commitment_digest`; they MUST NOT be placed
inside the execution commitment merely to make the commitment depend on a
receipt that itself depends on the commitment.

A provider or orchestrator MUST NOT begin the Attempt until the source snapshot
is fixed, all four Attempt acknowledgements are present, and the execution
commitment digest is available to all parties that must authorize, execute, or
validate the Attempt.

### B.5.2 Revisions and handoffs

For revision zero, `parent` MUST be `null`.

For a later revision or cross-provider handoff, `parent` MUST contain:

```json
{
  "attempt_id": "attempt-1",
  "validator_attestation_digest": "sha256:...",
  "customer_disposition_digest": "sha256:..."
}
```

The new `source_snapshot.base_commit` and `source_snapshot.base_tree` MUST equal
the exact validated result commit and tree named by the parent validator
attestation. This equality is the handoff trust boundary.

A provider-reported prior `result_commit`, branch tip, PR head, workspace, or
handoff prose MUST NOT substitute for the validator-attested result.

A paid STEER MAY add an `acceptance_delta`. Each delta item MUST use the same
Definition-of-Done item shape as B.4.1 and MUST be inside the hashed execution
commitment. A validator MUST execute or verify the effective acceptance set:

`contract_body.definition_of_done + execution_commitment.acceptance_delta`.

Hashing an acceptance delta without evaluating it is non-conformant.

---

## B.6 Provider delivery claim

The provider returns a `delivery_claim` bound to the exact Attempt:

```json
{
  "work_ref": "PAY-4",
  "attempt_id": "attempt-2",
  "contract_digest": "sha256:...",
  "execution_commitment_digest": "sha256:...",
  "provider_id": "provider:beta",
  "repository_uri": "https://github.com/example/repo",
  "claimed_base_commit": "0123456789abcdef0123456789abcdef01234567",
  "result_commit": "fedcba9876543210fedcba9876543210fedcba98",
  "result_tree": "76543210fedcba9876543210fedcba9876543210",
  "diff_digest": "sha256:...",
  "evidence_refs": []
}
```

A delivery claim is untrusted input. Its Git object IDs, check results, artifact
hashes, CI links, and evidence references MUST NOT become trusted merely because
they are well-formed, signed by the provider, recorded in an OWP event, or
stored on a protected branch.

The provider's `claimed_base_commit` MUST equal the execution commitment's
`source_snapshot.base_commit`; a mismatch is `INVALID` without attempting to
reinterpret the provider's intent.

---

## B.7 Independent Git validation

The independent validator MUST validate from its own controlled environment. It
MUST NOT treat the provider's working directory, provider-controlled cache, or
provider-supplied checkout as the authoritative validation workspace.

For a Git-backed Attempt that can be validated deterministically, the validator
MUST perform the following checks or an equivalent set that proves the same
properties:

1. Load and recompute the Work Agreement `contract_digest`.
2. Load and recompute the `execution_commitment_digest`.
3. Confirm the Attempt and Delivery Claim bind to both digests.
4. Obtain the authoritative repository/source through a validator-controlled
   path.
5. Resolve the exact committed `source_snapshot.base_commit` and verify the
   corresponding tree equals `source_snapshot.base_tree`.
6. Obtain the claimed result object without accepting a moving branch name as
   its identity.
7. Verify the result commit exists and recompute its tree.
8. Verify the recomputed tree equals `delivery_claim.result_tree`.
9. Verify the result is derived from the expected base according to the
   contract's history policy. At minimum, where ordinary linear ancestry is the
   declared policy, the base MUST be an ancestor of the result.
10. Compute the exact base-to-result change set and verify `diff_digest` when
    present.
11. Enforce allowed/forbidden path and other contract-specific negative policy.
12. Create a clean, detached checkout or equivalent immutable filesystem view
    of the exact result tree.
13. Execute every deterministic item in the effective acceptance set against
    that exact result.
14. Verify every evidence-backed item and label every human-only item as human;
    the validator MUST NOT synthesize a machine pass for a human criterion.
15. Bind build/test evidence to the exact result commit/tree.
16. Emit a validator attestation and retain evidence sufficient for an
    independent re-check according to the contract's evidence policy.

If the validator cannot independently obtain the required source, cannot run a
required deterministic check, cannot establish the exact test subject, or lacks
required isolation, it MUST return `INDETERMINATE`, not `VALID`.

A failed deterministic requirement, source mismatch, ancestry violation, tree
substitution, forbidden-path change, contract mismatch, Attempt mismatch, or
result/test subject mismatch MUST return `INVALID`.

A profile implementation MAY impose a stricter history policy, including
single-parent linear history, merge restrictions, commit-signature policy,
source-control provenance, two-party review, or SLSA Source levels.

### B.7.1 Portable change-set digest

When `delivery_claim.diff_digest` is supplied, it names the canonical profile
change set, not terminal-formatted patch text. The validator constructs a
path-sorted array with one entry per changed path, with rename detection
disabled:

```json
[
  {
    "path": "src/retry.js",
    "status": "M",
    "old_mode": "100644",
    "old_object": "<full Git object id>",
    "new_mode": "100644",
    "new_object": "<full Git object id>"
  }
]
```

Absent sides of an add/delete are `null`. Profile-v1 changed paths MUST be
valid UTF-8 strings. Validators MUST reject a path that cannot round-trip as
UTF-8 and MUST sort change-set entries by the unsigned lexicographic byte order
of the UTF-8 encoding of `path`; locale collation MUST NOT be used. `diff_digest`
is the B.3 canonical SHA-256 digest of this array. Validators MUST derive the
entries from the exact base/result trees, MUST use full object ids, and MUST NOT
let local rename, textconv, external-diff, replacement-object, or graft
configuration redefine the identity being checked.

---

## B.8 Test/build subject binding

A bare statement such as `"tests":"PASS"` is never sufficient evidence under
this profile.

Every reusable deterministic test/build result MUST identify the exact artifact
it evaluated. For Git source, the result SHOULD use an in-toto Statement whose
subject digest includes `gitCommit` and SHOULD also include `gitTree`.

The in-toto Test Result predicate
`https://in-toto.io/attestation/test-result/v0.1` SHOULD be used for ordinary
test results when it can express the evidence. The statement subject MUST equal
the validator-recomputed result commit/tree.

A test performed on commit B MUST NOT be accepted as evidence for delivered
commit C merely because B and C are close, share a branch, or have the same
provider.

Build provenance MAY additionally use SLSA Build Provenance. Source-control
trust MAY use SLSA Source provenance or Source Verification Summary Attestations.
OWP does not redefine SLSA levels.

---

## B.9 Validator attestation

The validator SHOULD emit an in-toto Statement v1 with predicate type:

`https://openworkprotocol.org/attestation/software-work-validation/v1`

The Statement subject MUST identify the exact validated result commit and tree.
The predicate MUST include at least:

- `work_ref`;
- `attempt_id`;
- `contract_digest`;
- `execution_commitment_digest`;
- expected source commit/tree;
- observed result commit/tree;
- `delivery_claim_digest`;
- validator identity;
- validator policy/version;
- effective acceptance item results;
- evidence digests/references;
- overall outcome: `VALID`, `INVALID`, or `INDETERMINATE`.

`validator_attestation_digest` is the canonical digest of the complete
attestation object or, when a signed attestation envelope is used, the digest of
the immutable attestation object identified by that envelope. An implementation
MUST document which object the digest names and MUST verify it consistently.

A `VALID` attestation means the named machine/evidence policy passed for the
exact subject. It does not mean the customer likes the result, that every legal
obligation is satisfied, or that payment is final.

---

## B.10 Customer disposition and handoff

After validation, the customer issues an immutable disposition:

```json
{
  "work_ref": "PAY-4",
  "attempt_id": "attempt-2",
  "validator_attestation_digest": "sha256:...",
  "decision": "APPROVE",
  "feedback": {}
}
```

`decision` MUST be `APPROVE`, `STEER`, or `REJECT`.

`customer_disposition_digest` is the canonical digest of that disposition.

An `APPROVE` decision MAY allow the operator to accept the pending core
CompletionRecord and let the deliverable exit `review` as `completed`.

A `STEER` decision creates a new Attempt. Its source snapshot MUST begin at the
prior validator-attested result, and its `parent` MUST bind both the prior
validator attestation and the STEER disposition. New objective acceptance
requirements MUST appear in the new Attempt's `acceptance_delta`.

A `REJECT` decision does not retroactively make a technically `VALID` delivery
invalid; it records that customer acceptance was not obtained. The customer's
reason and continuation determine what happens next under Core §12–13.

A handoff package MUST name the validator-attested current commit/tree and the
attestation digest. It MUST NOT promote a provider-reported branch tip or result
SHA to portable trusted state without independent validation.

---

## B.11 Commerce, authority, reputation, and transport composition

Payment and authority are separate proof domains from delivery validity.

- A successful payment MUST NOT be represented as proof that software passed
  validation.
- A validator `VALID` result MUST NOT be represented as proof that payment was
  authorized or settled.
- A reputation score MUST NOT replace exact delivery evidence for the current
  Attempt.

Where x402 v2 is used, OWP metadata SHOULD be carried in the protocol's
extension fields and SHOULD bind the payment requirement/payload/settlement
record to `execution_commitment_digest`.

Where AP2 is used, any commerce-layer mandate/receipt binding SHOULD reference
the same execution commitment when the containing commerce protocol provides a
safe extension point. OWP does not redefine AP2 mandates, payment roles, or
deterministic validation responsibilities.

Where ERC-8004 is used, identity, reputation, or validation registry entries MAY
reference OWP validator evidence. OWP MUST NOT define one universal on-chain
quality score.

Where A2A 1.0 transports provider work, the OWP profile MUST use an A2A extension
URI rather than redefining A2A core fields. A2A `taskId` values are
server-generated and MUST NOT be replaced by an OWP work ref or Attempt id.
OWP identifiers and digests SHOULD ride in typed extension metadata. A2A
`contextId` MAY group related work interactions but MUST NOT be treated as the
portable OWP work identity.

See the informative interoperability notes under `interop/`.

---

## B.12 Core OWP lifecycle integration

This profile does not add a new core state.

A recommended mapping is:

1. **`proposed` / `todo`** — author the contract body; collect four-party
   acknowledgements.
2. **before `in_progress`** — fix the Attempt source snapshot and execution
   commitment; collect the four Attempt acknowledgements; then obtain any
   required authority/payment binding.
3. **`in_progress`** — provider/orchestrator executes. Internal worker state is
   opaque to OWP.
4. **`work.complete` -> `review`** — provider submits CompletionRecord and
   Delivery Claim; ownership releases as Core requires.
5. **while `review`** — independent validator emits `VALID`, `INVALID`, or
   `INDETERMINATE`; operator client renders the result and evidence.
6. **operator acceptance** — only after a `VALID` result where the project
   policy requires independent validation. Human-only criteria remain the
   customer's decision.
7. **STEER / provider change** — new Attempt begins from the prior
   validator-attested result, never from a provider assertion.

A deployment claiming this profile MUST NOT configure a straight-to-exit
completion path for work whose contract requires independent validation unless
an independently produced `VALID` attestation for that exact result already
exists.

---

## B.13 Threats this profile is required to detect

A conforming validator test suite MUST include negative coverage for at least:

1. expected base differs from provider-claimed base;
2. expected base object does not exist;
3. result object does not exist;
4. result history is unrelated to the expected base;
5. result tree differs from the claimed tree;
6. provider tests commit B but delivers commit C;
7. abbreviated or malformed Git object identifiers;
8. forbidden/unrelated changed paths;
9. delivery binds the wrong Work Agreement or Attempt;
10. revision/handoff begins from an unvalidated provider result;
11. paid STEER acceptance delta is recorded but not executed;
12. provider or orchestrator attempts to self-validate where independent
    validation is required;
13. a required validation command cannot be run and the implementation tries to
    report `VALID` instead of `INDETERMINATE`;
14. one of the four Work Agreement roles acknowledges a different contract digest;
15. one of the four Attempt roles is absent or acknowledges a different execution commitment digest;
16. payment/reputation evidence is substituted for delivery validation.

A passing happy path without these negative cases is insufficient profile
conformance.

---

## B.14 Privacy and secret handling

The validator MUST treat repositories and build inputs as hostile.

Validation SHOULD run in a disposable sandbox or an equivalently isolated
environment with no ambient user credentials. Secrets not explicitly required
by the validation policy MUST NOT be exposed to the result under test.

A validator SHOULD fetch source and dependencies with least privilege and SHOULD
retain only the evidence required by the Work Agreement and applicable policy.
Sensitive evidence MAY be content-addressed and access-controlled rather than
embedded directly in OWP records.

The profile does not require public source, public attestations, or public build
logs.

---

## B.15 Conformance claim

A deployment MAY claim `OWP Software Work Integrity Profile v1` only when:

- Core OWP conformance requirements that apply to the deployment are satisfied;
- the deployment advertises `software_work_integrity`;
- four-party agreement is enforced before the first Attempt;
- each Attempt has a valid execution commitment with exact source snapshot and
  four acknowledgements of that exact execution commitment digest;
- revisions/handoffs chain from validator-attested prior results;
- deterministic/evidence criteria are evaluated independently against the exact
  result subject;
- inability to validate fails closed as `INDETERMINATE`;
- required negative vectors in B.13 pass;
- the customer disposition remains distinct from validator outcome.

The reference vectors and dependency-free verifier in this repository check the
profile object's portable invariants. They do not establish that an external Git
forge, build sandbox, A2A provider, x402 facilitator, AP2 participant, or
ERC-8004 registry is secure.
