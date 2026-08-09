# Open Work Protocol 1.0-rc2 release readiness

Audit date: **2026-08-08**  
Verdict: **READY for a public release candidate**  
Scope: local release preparation only; nothing was pushed, published, tagged,
or written to a remote service.

This verdict means the documented source trees are reproducible, the one
reference implementation meets the RC2 contract, every advertised example
runs standalone, and no known Blocker or High finding remains. It does **not**
mean production certification, independent interoperability, or suitability of
open/static-token mode for an internet-facing deployment.

## Repository and component inventory

| Local repository | Baseline HEAD | Disposition | Public components |
|---|---:|---|---|
| `owp` | `db6dbd8db69a` | In scope; canonical specification | RC2 prose, normative HTTP annex, requirement inventory/matrix, design and change record, governance, release tooling |
| `owp-code` | `c9ab43f0d2ae` | In scope; sole reference implementation | Zod schema, SQLite surface, HTTP binding, CLI, operator console, fleet/watcher clients, 50-check wire conformance kit, unit/E2E/strain suites |
| `owp-desk` | `ca34b8c53429` | In scope; standalone freight example | load-board UI/proxy, inbound and entity clients, fixtures, agent skill, embedded RC2 runtime |
| `owp-ops` | `cb5a26f47f97` | In scope; standalone estate example and generic watcher | estate board/proxy, watcher, window client, runbooks/packaging, agent skill, embedded RC2 runtime |
| `owp-publish` | `13e4faebfc4f` | In scope; standalone editorial example | writing room/proxy, manuscript recall/correlation, continuity client, fixtures, agent skill, embedded RC2 runtime |
| `owp-research` | `d3c44fd82eb4` | In scope; standalone research example | briefing room/proxy, catalog/dedup/claim tooling, fixtures, agent skill, embedded RC2 runtime |
| `owp-research-1` | `d3c44fd82eb4` | Excluded | Superseded duplicate of `owp-research`, same origin/HEAD, with stale sibling-bootstrap assumptions; not a second implementation or release artifact |
| `owp-github` | not a repository | Excluded | Parent directory containing six history-free publication staging clones; duplicates the release set and is not source authority |

All applicable `AGENTS.md` and canonical `SKILL.md` files were read before
changes. Each runnable repository is private npm metadata (`0.1.0`,
`private:true`, MIT, Node `>=23.6`) and deliberately refuses npm publication.
The package version identifies the example artifact; `1.0-rc2` identifies the
protocol contract and is reported/pinned independently.

## Protocol baseline

- Canonical normative files: `spec/owp-1.0-rc2.md` and
  `spec/annex-http-1.0-rc2.md`.
- Maturity: release candidate, explicitly not production readiness.
- Compatibility: RC2 supersedes RC1 and advertises only RC2. RC2 is allowed to
  close defects before 1.0; after 1.0, §4 requires a major revision for a
  breaking verb/state/error change.
- Normative vocabulary: RFC 2119 `MUST`, `MUST NOT`, `SHOULD`, `SHOULD NOT`,
  and `MAY`; lowercase prose and historical §§21–22 are informative.
- Inventory: `REQUIREMENTS.json` and `CONFORMANCE_MATRIX.md` trace **145**
  keyword occurrences (76 MUST, 30 MUST NOT, 18 SHOULD, 0 SHOULD NOT, 21 MAY)
  to location, applicability, evidence, result, and gap.
- Claims: five independent domain experiences share one implementation.
  Independent implementation interoperability has not been demonstrated and is
  not claimed.

## Example-by-example standalone acceptance

The final gate reconstructs each public tree from its explicit manifest into a
new temporary directory. No sibling checkout, `.owp-deps`, existing build
output, user database, or global package is used.

| Repository | Clean install and audit | Tests/checks | Operator acceptance | Result |
|---|---|---|---|---|
| `owp-code` | `npm ci`; 0 vulnerabilities | type-check; schema reproduce; 94/94 tests; 50/50 token-auth conformance | CLI help; one-shot fleet; UI and describe 200; clean SIGTERM | PASS |
| `owp-desk` | `npm ci`; 0 vulnerabilities | 24/24 tests | init twice; seeded load board 200; embedded surface describe 200; shutdown | PASS |
| `owp-ops` | `npm ci`; 0 vulnerabilities | 43/43 tests, including Docker absent/compatibility paths | init twice; estate board 200; one-shot watcher; embedded surface; shutdown | PASS |
| `owp-publish` | `npm ci`; 0 vulnerabilities | 56/56 tests | init twice; writing room/manuscript 200; local retrieval survives surface failure; shutdown | PASS |
| `owp-research` | `npm ci`; 0 vulnerabilities | 35/35 tests | init twice; briefing room 200; catalog stats; embedded surface; shutdown | PASS |

Every repository also passes Codex manifest validation with the installed
validator, `claude plugin validate --strict`, canonical skill validation, and
an isolated offline Pi local install. `package-lock.json` and `npm ci` agree.
Each embedded reference runtime has an exact `MANIFEST.sha256`; all four copies
are byte-identical to the audited RC2 source set.

Operator commands, prerequisites, expected results, cleanup, port overrides,
timeouts, credentials, and error troubleshooting are in each
`docs/deploy.md`. Public per-repository summaries are in `EVIDENCE.md`.

## Adversarial findings and dispositions

| ID | Severity | Finding/evidence | Disposition | Affected components |
|---|---|---|---|---|
| R-01 | High | §7.3 named only `references` as registered while §19 also registered example-local `git`, `hosts`, `sources`, `artifacts` | Fixed: §19 now distinguishes protocol registrations from deployment vocabulary | Spec, registries |
| R-02 | High | A timeout left mutation outcome unknown; blind retry could duplicate work | Fixed: durable actor-scoped `Idempotency-Key`, canonical request hashing, atomic mutation/replay record, exact replay, mismatch refusal, restart test, 24 h minimum retention | Annex, HTTP/store, CLI/UIs/proxies, conformance |
| R-03 | High | HTML-form-compatible content types and unbounded bodies let a hostile page drive a loopback operator endpoint or exhaust it | Fixed: JSON-only POST, 1 MiB body bound, Origin refusal on the surface, no-store/nosniff/CSP, proxy parity, negative tests | Annex, HTTP surface, four proxies/UIs |
| R-04 | High | No terminal withdrawal existed for todo/in-progress/parked/review work | Fixed: reasoned `work.cancel`; all working states covered; clears holder/pending data; refuses live dependents; operator/grant authorization; terminal history retained | Spec, schema, surface/store, CLI/UI, conformance |
| R-05 | Medium | RC1 contained normative post-cut edits while still presenting itself as the current cut | Fixed: RC2 filenames, pin, schema, runtime, tests, links, and examples agree; RC1 is historical | All repositories |
| R-06 | Medium | Public language could be read as independent interoperability evidence | Fixed: claims narrowed to reference conformance/domain portability; shared implementation stated beside evidence | Spec/README/evidence |
| R-07 | Medium | Proxy fetches could hang indefinitely and HTTP retry guidance invited storms | Fixed: 10 s default configurable proxy/CLI/UI deadlines; bounded retry/jitter/cancellation rules; no shipped automatic mutation retry | Annex, clients, runbooks |
| R-08 | Medium | Release gate told `owp-code` to run nonexistent `npm run demo`; evidence said fleet served a console although it is one-shot | Fixed: repository-specific commands and accurate expected behavior | Release/runbook docs |
| R-09 | Medium | Embedded runtime provenance claimed an unmodified old commit after RC2 changes | Fixed: explicit RC2 snapshot statement plus exact per-file SHA-256 manifests | Four domain repositories |
| R-10 | Low | Security reporting, contribution, maintenance, trademark, and release authority were unstated | Fixed: `SECURITY.md`, `CONTRIBUTING.md`, `GOVERNANCE.md`; no certification/foundation/SLA claim | Public metadata |
| R-11 | Medium | The server entrypoint relied on the default signal action and exited 143 on `SIGTERM` instead of closing its listener and SQLite handle | Fixed: explicit idempotent `SIGINT`/`SIGTERM` shutdown plus a subprocess exit-status test; resynced into every embedded runtime | Reference and embedded servers |
| L-01 | Medium | No independently authored surface has passed the kit | Accepted limitation: no interoperability claim; the kit is ready for external use | Adoption claim |
| L-02 | Medium | Routable TLS/reverse-proxy and external credential lifecycle were not exercised locally | Conditional limitation: standalone claim is loopback; every runbook makes TLS/auth a separate deployment gate | Internet deployment |
| L-03 | Low | Validation is Linux/Node 24 only; no Windows/macOS or long-duration soak | Deferred transparently; Node floor is documented, and no cross-platform/soak claim is made | Portability/operations |
| L-04 | Low | Static bearer tokens are a reference arrangement, not a complete identity system | Accepted and documented; annex permits replacement, requires TLS when routable, and recommends distinct high-entropy tokens | Authentication binding |
| L-05 | Low | Hosted workflows used mutable major action tags rather than commit SHAs | Fixed before publication: checkout 7.0.1 and Node setup 7.0.0 are pinned to reviewed commit SHAs | Hosted CI |

No Blocker or High finding is open. Medium findings are fixed or explicitly
bounded above; none invalidates the standalone RC claim.

## Adversarial review conclusions

- **Protocol implementer:** State exits, dependency cancellation, tiebreak
  readings, registered names, error recovery, revision selection, extension
  preservation, and link replacement now have one implementable reading.
- **Operator:** Every example starts from a fresh tree, names its ports and
  credentials, differentiates empty from unavailable, provides deterministic
  cleanup, and fails closed on malformed/cross-origin protocol input.
- **Security reviewer:** Open mode is loopback-only and browser hardening is
  explicit; agent/operator/grant boundaries and self-verdict denial are tested.
  Routable auth/TLS remains deployment-owned and is not represented as tested.
- **Failure reviewer:** Claims are atomic; cancellation cannot strand live
  downstream items; state errors require reread; mutations are not blindly
  retried; proxies abort; transport failure remains distinct from surface
  errors.
- **Standards reviewer:** Normative keywords are mechanically inventoried,
  informative history is separated, HTTP `/v0` is identified as a binding
  generation rather than protocol revision, and permissions are not counted as
  test passes.
- **Internet critic:** The project states who wrote the evidence, what was not
  independently verified, what governance does not exist, and why READY means
  public RC—not production certification.

## Exact final validation commands

Run from the source workspace:

```sh
node tools/build-requirement-matrix.mjs
tools/build-public-trees.sh /tmp/owp-public-rc2

# in each runnable public tree
npm ci
npm test
npm audit --audit-level=high

# owp-code additionally
npm run check
npm run schema
npm run schema:verify
node conformance/run.ts http://127.0.0.1:PORT \
  --operator-token TOKEN --agent-token TOKEN
npm run fleet -- --sessions 4 --items 24 --concurrency 2

# each domain tree
npm run init                    # twice, against scratch state
npm run demo                    # verify HTTP 200, then terminate
npm run surface                 # verify / and surface.describe, then terminate

# every runnable tree
python3 ~/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py .
claude plugin validate --strict .
python3 ~/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/NAME
PI_CODING_AGENT_DIR=FRESH_DIR PI_OFFLINE=1 pi install -l .
git diff --check
```

The public-tree builder refuses a non-empty destination and excludes `.git`,
`node_modules`, `.owp-deps`, databases, tokens, sessions, private findings, and
development-only chronology. No publish/push/tag command is part of the gate.

## Final recommendation

**READY** to assemble and review a public **1.0-rc2** release candidate from the
manifested trees. Do not label it 1.0 final, independently interoperable,
production-certified, or internet-safe by default. Before any remote release,
a maintainer should inspect the final diff and generated tree, choose the
public commits/tags, enable private vulnerability reporting and branch
protection, and rerun CI in the actual hosting environment.
