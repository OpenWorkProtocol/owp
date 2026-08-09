# Open Work Protocol 1.0-rc2 release readiness

Assessment date: **2026-08-08**
Release status: **Public release candidate**
Assessment result: **READY**

## Release qualification

Open Work Protocol 1.0-rc2 is approved for public implementation, evaluation,
and feedback. The assessment covers the normative specification, HTTP binding,
reference implementation, conformance suite, and four standalone domain
examples.

The release designation is limited to a release candidate. It does not
represent production certification, independently verified interoperability,
or validation of internet-facing deployments.

## Release components

| Repository | Component | Release |
|---|---|---|
| `OpenWorkProtocol/owp` | Normative specification, HTTP binding, requirement inventory, conformance matrix, governance, and release evidence | `v1.0-rc2` |
| `OpenWorkProtocol/owp-code` | Reference surface, schema, CLI, operator console, and wire conformance suite | `v0.1.0` |
| `OpenWorkProtocol/owp-desk` | Standalone freight back-office example | `v0.1.0` |
| `OpenWorkProtocol/owp-ops` | Standalone infrastructure operations example | `v0.1.0` |
| `OpenWorkProtocol/owp-publish` | Standalone editorial workflow example | `v0.1.0` |
| `OpenWorkProtocol/owp-research` | Standalone research workflow example | `v0.1.0` |

The five runnable repositories use the same reference implementation. Their
results establish reference conformance and portability across the represented
domains; they do not establish interoperability between independently authored
implementations.

## Conformance evidence

| Evidence | Result |
|---|---:|
| Normative requirement occurrences inventoried and traced | 145/145 |
| Authenticated HTTP conformance obligations | 50/50 |
| Reference implementation tests | 94/94 |
| Freight example tests | 24/24 |
| Infrastructure example tests | 43/43 |
| Editorial example tests | 56/56 |
| Research example tests | 35/35 |
| Total automated tests | 252/252 |
| Dependency audits at release | 0 known vulnerabilities |

`REQUIREMENTS.json` and `CONFORMANCE_MATRIX.md` map each normative occurrence
to its specification location, applicability, evidence, result, and any known
gap. The matrix is generated from the normative documents and is checked for
reproducibility in continuous integration.

## Standalone verification

Each runnable repository was installed and tested from a fresh clone without a
sibling checkout, local package path, pre-existing build output, user database,
or global package dependency. Verification included installation, dependency
audit, automated tests, documented initialization, startup, observable HTTP
responses, repeat initialization, and orderly shutdown.

The domain repositories contain provenance-recorded copies of the reference
runtime. `vendor/owp-reference/MANIFEST.sha256` identifies the embedded files
and permits byte-for-byte verification against the released reference source.

## Security and release controls

- Mutation replay protection uses actor-scoped idempotency keys and durable
  request-result records.
- HTTP POST operations require JSON and enforce a 1 MiB request-body limit.
- Loopback browser protections include origin validation, content-type
  enforcement, cache controls, and content security policy headers.
- Cancellation, bounded client deadlines, retry guidance, authorization
  classes, grant scope, and self-verdict restrictions are specified and tested.
- GitHub Actions dependencies are pinned to full commit identifiers.
- Protected default branches require successful continuous integration and
  prohibit force pushes and deletion during normal operation.
- Secret scanning, push protection, dependency alerts, automated security
  updates, and private vulnerability reporting are enabled.

## Known limitations

| ID | Severity | Limitation | Release impact |
|---|---|---|---|
| L-01 | Medium | No independently authored surface has completed the conformance suite. | Independent interoperability is not an approved release claim. |
| L-02 | Medium | Routable TLS, reverse-proxy behavior, and external credential lifecycle were not exercised by the standalone test environment. | Internet-facing deployment requires a separate security acceptance process. |
| L-03 | Low | Release validation used Linux and Node.js 24; Windows, macOS, and long-duration soak testing were not performed. | Cross-platform and soak-test claims are outside the assessed scope. |
| L-04 | Low | Static bearer tokens are provided as a reference binding rather than a complete identity system. | Deployments may replace the binding and remain responsible for identity lifecycle and secret handling. |

No known Blocker or High-severity finding remains open. The Medium and
Low-severity limitations above are bounded release claims rather than
unresolved conformance failures.

## Reproduction commands

```sh
# specification repository
node tools/build-requirement-matrix.mjs
git diff --exit-code -- REQUIREMENTS.json CONFORMANCE_MATRIX.md

# each runnable repository
npm ci
npm audit --audit-level=high
npm test

# reference implementation additionally
npm run check
npm run schema:verify
node conformance/run.ts http://127.0.0.1:PORT \
  --operator-token TOKEN --agent-token TOKEN
```

Repository-specific installation, acceptance, cleanup, and troubleshooting
commands are documented in each `docs/deploy.md` and summarized in each
`EVIDENCE.md`.

## Release determination

The approved public designation is **Open Work Protocol 1.0-rc2 Release
Candidate**. The evidence supports public implementation and evaluation of the
release candidate within the scope and limitations stated above.
