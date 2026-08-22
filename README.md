<p align="center">
  <img src="assets/brand/owp-icon-black.svg" width="112" alt="Open Work Protocol">
</p>

# Open Work Protocol

Open Work Protocol (OWP) defines a durable coordination contract between agent
fleets and human operators. It standardizes work lifecycle, assignment,
questions, decisions, completion, recovery, authority, and bounded operator
projections while leaving domain vocabulary and user interfaces to each
deployment.

## Release status

The current development candidate is **Open Work Protocol 1.0-rc3**. The last
published release remains **1.0-rc2** until the external reference repositories
and independent interoperability evidence are upgraded.

RC3 preserves the RC2 core lifecycle and adds the normative optional
**Software Work Integrity Profile** for exact-source software contracts:

- four-party Definition of Done consensus before contract acceptance;
- an immutable Git source snapshot bound to every execution Attempt;
- provider delivery claims treated as untrusted input;
- independent reconstruction of base/result/tree/diff and exact-result tests;
- in-toto-compatible validator/test attestations;
- revision and provider handoff from validator-attested state only.

Current spec-repository evidence:

- Normative requirement occurrences inventoried: **256**
- Software Work Integrity adversarial/real-Git tests: **21/21**
- Static portable profile vectors: **7/7**
- Known Blocker/High findings in the spec-local profile checks: **0**

The historical RC2 release evidence (including the five shared-reference
runnable repositories and their 252 automated tests) remains valid for RC2. It
MUST NOT be represented as RC3 implementation or independent interoperability
evidence.

## Normative documents

- [Core specification](spec/owp-1.0-rc3.md)
- [HTTP and JSON binding](spec/annex-http-1.0-rc3.md)
- [Software Work Integrity Profile](spec/annex-software-work-integrity-1.0-rc3.md)
- [Software Work Integrity schemas](schemas/)
- [Normative requirement inventory](REQUIREMENTS.json)
- [Conformance matrix](CONFORMANCE_MATRIX.md)

## RC3 profile verification

```sh
node tools/test-software-work-integrity-vectors.mjs
node tools/test-software-work-integrity.mjs
```

For a concrete bundle and repository, the verifier can also reconstruct Git
reality and execute deterministic acceptance commands in a fresh clone:

```sh
node tools/verify-software-work-integrity.mjs \
  --bundle path/to/bundle.json \
  --git-repo path/to/repository \
  --allow-exec
```

`--allow-exec` is intentionally explicit because the contract may contain build
or test commands. Production validators should execute those commands in a
hardened disposable sandbox, not in the caller's ambient environment.

## Release documentation

- [RC3 readiness assessment](RELEASE_READINESS.md)
- [RC3 candidate record](RELEASE_CANDIDATE_1.0_RC3.md)
- [Last published RC2 release record](RELEASE_RECORD.md)
- [Revision history](CHANGELOG.md)
- [Migration guide](docs/10-impact-of-1.0.md)
- [Protocol change policy](docs/09-changing-the-protocol.md)
- [Software work integrity explainer](docs/11-software-work-integrity.md)
- [External standards alignment](docs/12-external-standards-alignment.md)
- [Try OWP field-lab relationship](docs/13-try-owp-field-lab.md)
- [Project URLs and public surfaces](docs/14-project-surfaces.md)
- [Run your own Try OWP](docs/15-run-your-own-try-owp.md)
- [Acknowledgments](ACKNOWLEDGMENTS.md)

## Implementations and examples

The repositories below are the historical RC2 reference evidence. They are not
yet RC3 Software Work Integrity implementations.

| Repository | Purpose | RC2 tests |
|---|---|---:|
| [`owp-code`](https://github.com/OpenWorkProtocol/owp-code) | Reference surface, schema, CLI, operator console, and conformance suite | 94 |
| [`owp-desk`](https://github.com/OpenWorkProtocol/owp-desk) | Freight back-office example | 24 |
| [`owp-ops`](https://github.com/OpenWorkProtocol/owp-ops) | Infrastructure operations example and reference watcher | 43 |
| [`owp-publish`](https://github.com/OpenWorkProtocol/owp-publish) | Editorial workflow example | 56 |
| [`owp-research`](https://github.com/OpenWorkProtocol/owp-research) | Research workflow example | 35 |

Independent implementation interoperability remains an explicit RC3 release
gate.

## Try OWP — field evaluation, separate from conformance

**[try.openworkprotocol.org](https://try.openworkprotocol.org/)** is the public
OWP Field Lab. It exists to exercise durable work with external requests while
keeping the field experiment distinct from the protocol specification.

The Field Lab records requests, explicit ACCEPT/PASS decisions, numbered
attempts, questions, delivery evidence, a separately named validation record,
customer APPROVE/STEER/REJECT, and portable handoff state. It does **not** claim
full OWP 1.0 conformance, independent implementation interoperability, payment,
or full RC3 Software Work Integrity validation. In particular, a named validator
record is not the same thing as independently reconstructing and testing the
exact Attempt-bound Git result.

This separation lets field observations inform protocol development without
changing the protocol's conformance or evidence requirements. See
[docs/13-try-owp-field-lab.md](docs/13-try-owp-field-lab.md).

### Run your own field lab

The repo includes a self-hostable, non-normative Try OWP template
(PR **and** greenfield-idea intake):

```sh
./scripts/new-try-owp.sh ../my-try-owp \
  --operator "Acme Agent Lab" \
  --hostname try.example.com \
  --provider-id provider:acme
cd ../my-try-owp
python3 -m owp_field_lab.server --host 127.0.0.1 --port 8080
```

The bootstrapper renders deployment identity, runs the generated smoke suite by
default, and leaves secrets out. The embedded template currently passes **58
tests**. See [Run your own Try OWP](docs/15-run-your-own-try-owp.md). The operator
queue is available only through host-side administration, and the intake service does
not execute submitted code.

## Protocol boundary

OWP is not an agent runtime, scheduler, workflow language, document store,
retrieval system, development environment, or reference user interface. The
protocol defines shared envelopes and invariants. Deployments define their
domain records, presentation, delivery, scheduling, and automation.

## Conformance

Candidate surfaces can be evaluated with the conformance suite in
[`owp-code`](https://github.com/OpenWorkProtocol/owp-code):

```sh
git clone https://github.com/OpenWorkProtocol/owp-code
cd owp-code
npm ci
npm test
npm run conformance -- http://127.0.0.1:7117 \
  --operator-token "$OWP_OPERATOR_TOKEN" \
  --agent-token "$OWP_AGENT_TOKEN"
```

Conformance results from the shared reference implementation are not evidence
of interoperability between independent implementations.

## Security

Open mode is limited to loopback evaluation. Routable deployments require TLS,
authentication, protected operator clients, scoped credentials, request
limits, and deployment-specific identity lifecycle controls. Vulnerabilities
should be reported according to [SECURITY.md](SECURITY.md).

## Project

- Website: [openworkprotocol.org](https://openworkprotocol.org/)
- Try OWP Field Lab: [try.openworkprotocol.org](https://try.openworkprotocol.org/)
- Canonical specification repository: [OpenWorkProtocol/owp](https://github.com/OpenWorkProtocol/owp)
- GitHub organization: [OpenWorkProtocol](https://github.com/OpenWorkProtocol)
- Security reporting: [SECURITY.md](SECURITY.md)
- License: [MIT](LICENSE)
