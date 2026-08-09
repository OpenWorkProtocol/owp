# OWP — the Open Work Protocol

**Agents work at machine speed. Operators steer at human speed. OWP is the contract
at the seam.**

Work that outlives a session, decisions that wait without blocking anyone, and a queue
computed for a human who will look at it in four hours — none of which the existing
categories model. Trackers make agents perform human ritual; orchestrators assume you
are at the machine; documentation is append-only and goes stale while still reading as
current.

> **Start here:** [`spec/owp-1.0-rc2.md`](spec/owp-1.0-rc2.md) for the contract,
> or [`docs/04-examples.md`](docs/04-examples.md) for the five deployments that
> forced it to stay general.
>
> **Project site:** [openworkprotocol.io](https://openworkprotocol.io) ·
> **release evidence:** [`RELEASE_READINESS.md`](RELEASE_READINESS.md) ·
> **contact:** [info@openworkprotocol.io](mailto:info@openworkprotocol.io)

## Status: 1.0-rc2 release candidate

Five deliberately different domain examples run on one reference surface — a coding
fleet, an editorial desk, a research catalog, a container estate, and a trucking back
office. **252 tests between them, 50 conformance obligations verified over the wire,
and clean-room standalone launch evidence for every runnable repository.** These are
not independent implementations; no independent interoperability claim is made.

Most of 1.0 came from two or more worlds hitting the same wall independently, or from an
invariant the protocol already carried. A final pass then closed the remaining register on
the operator's ruling, including **six findings only one world had filed** — each marked as
such in [§22](spec/owp-1.0-rc2.md). The convergence bar is still the standing rule
([`docs/09`](docs/09-changing-the-protocol.md)); it was overridden once, deliberately, and
saying so is cheaper than being caught.

```
spec/owp-1.0-rc2.md          the protocol — 22 sections; what is frozen, what may grow
spec/annex-http-1.0-rc2.md   Annex A: the HTTP+JSON binding (normative if you choose HTTP)
OpenWorkProtocol/owp-code/conformance/  50 obligations over the wire against a candidate surface
OpenWorkProtocol/owp-code/schema/       machine-readable schema; prose wins on conflict
CONFORMANCE_MATRIX.md                   all 145 normative keyword occurrences traced
RELEASE_READINESS.md                    inventory, risks, clean-room evidence, verdict
```

## Reading paths

**If you are skeptical** — [`docs/08-the-five-worlds.md`](docs/08-the-five-worlds.md)
(what five unrelated deployments proved), then
[`docs/10-impact-of-1.0.md`](docs/10-impact-of-1.0.md) (what breaks, plus a risk
register naming what could still bite).

**If you are building a surface** — [`spec/owp-1.0-rc2.md`](spec/owp-1.0-rc2.md) §20.1
for the build order, then run `owp-code/conformance/` against your own.

**If you are adopting for a domain** —
[`docs/06-programming-with-owp.md`](docs/06-programming-with-owp.md), then write your
`types/registry.md` before you write code.

**If you want to change it** —
[`docs/09-changing-the-protocol.md`](docs/09-changing-the-protocol.md): the bar is two
unrelated worlds, or an invariant the protocol already carries.

## The five worlds

Chosen to *disagree* with each other. What survived all five is the protocol; what
differed is exactly what the spec refuses to define — including the interface, of which
there is deliberately no reference implementation.

| World | The work it coordinates | Interface character | Tests |
|---|---|---|---|
| [`owp-code`](https://github.com/OpenWorkProtocol/owp-code) | a fleet of coding agents on one codebase; also **the reference surface + conformance kit** | console — cards, dark, triage-first | 94 |
| [`owp-publish`](https://github.com/OpenWorkProtocol/owp-publish) | a novel: scene recall, character correlation, continuity | writing room — manuscript first | 56 |
| [`owp-research`](https://github.com/OpenWorkProtocol/owp-research) | exhaustive research; a catalog that compounds | briefing room — a dossier you decide inside | 35 |
| [`owp-ops`](https://github.com/OpenWorkProtocol/owp-ops) | a container estate; also **the reference watcher** | estate board — a terminal wall | 43 |
| [`owp-desk`](https://github.com/OpenWorkProtocol/owp-desk) | a trucking back office at volume | load board — a dispatcher's grid | 24 |

## Design record

- [`docs/08-the-five-worlds.md`](docs/08-the-five-worlds.md) — what each world proved
- [`docs/01-design.md`](docs/01-design.md) — the final model and its boundaries
- [`docs/04-examples.md`](docs/04-examples.md) — the scenarios and falsification bar
- [`docs/10-impact-of-1.0.md`](docs/10-impact-of-1.0.md) — adoption impact and remaining risks

## What it will never be

Not a development surface. Not an agent runtime. Not a sync target for agent to-do
lists. Not a general-purpose project tool — no calendars, sprints, or story points.
Not a document store or a retrieval engine. **And not a reference UI**: a shared shell
would become the de facto "OWP interface", and the protocol would quietly become one
client's API.

## Licence

MIT — see [`LICENSE`](LICENSE). The specification, the annex, the conformance kit
and every example are under it. A protocol nobody may implement without asking is
not a protocol, so the terms are the permissive ones and they apply to the spec
text as much as to the code.

Superseded drafts and working storyboards remain in the private Forgejo
development record; the GitHub launch contains the released result.
