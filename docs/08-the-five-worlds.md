# The five worlds — what each one proved

The examples are not the product. They are the instrument: five deliberately
unlike deployments, built on one surface, whose job is to push the protocol from
five directions until the parts that are genuinely universal are the only parts
left in the spec.

This document is the distillation — what each world contributed, and what the
set of them proves together. Use it to pick where to start reading.

## The set at a glance

| World | The work it coordinates | Its operator character | What it uniquely stressed |
|---|---|---|---|
| **owp-code** | many agents on one large codebase | **console** — cards, dark, triage-first | concurrency, fleet supervision, review load at volume |
| **owp-publish** | a novel and an editorial desk | **paper** — one piece at a time | promotion-with-provenance; interpreted voice rules; retrieval |
| **owp-research** | exhaustive reading and catalogs | **dossier** — decide inside the document | steering mid-flight; negative knowledge; corpus scale |
| **owp-ops** | a container/host estate | **terminal wall** — dense, keyboard | creator clients, grants, triggers, drift |
| **owp-desk** | a trucking back office | **load board** — dispatcher grid | volume, repeat transactions, graduated authority |
| *(the CLI)* | anything | **no screen at all** | the standing proof no interface is required |

## What each world contributed to the protocol

**owp-code** — the reference surface itself, and then the pressure that comes
from concurrency: atomic claim-on-`next` (a choose-then-claim split races two
sessions onto one item), the operator item read, the audit that produced the
AAA split, and — at fleet scale — the discovery that `depends_on` was frozen at
creation exactly when cross-cutting refactors need it most. It also holds the
**conformance kit**, which is the artifact that makes everything else portable.

**owp-publish** — proved the surface was protocol, not one world's API: the
editorial desk ran the whole storyboard against an unchanged surface. It
contributed the ruling that the rank vector needed a deployment tiebreak (a
book cannot say "earliest unfinished chapter" with five priority buckets), and
caught the surface **authoring prose** into worklogs — invisible in code, fatal
where notes are the product. `character-voice` is the standing proof that
policies must be interpreted and never evaluated.

**owp-research** — the world that steers mid-flight. It filed R-1 (a steered
study's purpose moves and nothing could restate it), gave upstream questions
their second running-code direction, and demonstrated that *declining* the
tiebreak slot is a first-class choice. Its catalogs are the argument that
retrieval belongs to the deployment: grep, full-text, and embeddings are all
legitimate, and a protocol that picked one would be specifying a search engine.

**owp-ops** — paid the creator-client debt in full. Trigger-scoped grants got
their first real mechanism, `work.unpark` learned that *the trigger is the
address* (so a cron needs no read authority to find its parks), and
`unreconciled` finally got a reference implementation from the one world with a
natural artifact stream. It also ships **the reference watcher**, which
owp-desk then imported rather than rewrote.

**owp-desk** — the cheapest world and therefore the sharpest evidence: it ships
no surface, no watcher, and originally no UI, and still ran its narratives
unchanged. It contributed the finding that `urgency` was unassignable after
creation, and it is the world where volume and repeat transactions test whether
a queue designed for artisanal work survives a business.

## What the set proves together

1. **The line holds.** Five vocabularies — `git`/`worktree`, `manuscript`/
   `characters`, `sources` with credibility, `hosts`/`containers`,
   `documents`/lanes — ride the same envelopes with no surface awareness of any
   of them. Three consecutive worlds needed no new protocol at all.
2. **Convergence is the signal — until the operator overrides it.** Nearly all
   of 1.0 came from two or more worlds hitting the same wall independently:
   restatable structure (four worlds), the operator item read (two), link write
   semantics (two), bounded projections (two). Single-world demands were
   rejected or deferred by rule.

   The final pass is the exception, and it is recorded rather than smoothed
   over: the operator ruled the remaining register closed, which moved six
   findings only one world had filed (C-3, C-5, O-8, R-4, R-5, PUB-7). Each is
   labelled `one-world-operator-ruled` in §22. The bar still stands as the
   standing rule; what changed is that it is now demonstrably a rule with a
   known exception rather than an unbroken record — which is a weaker claim and
   the true one.
3. **Difference is the other signal.** Where worlds disagreed — what a `kind`
   is, which continuations exist, how to order work, what an interface looks
   like — the protocol was right to have no opinion. The five interfaces look
   nothing alike *on purpose*; that they share every verb is the point.
4. **The constraints survived maximum pressure.** No calendar held in the two
   most date-shaped worlds (certs, embargoes, ship dates) because clocks live
   in clients and periodic work is recurring *creation*. Surface-never-acts
   held through expiry, drift, and recovery. Questions-never-park held from the
   world that discovered it to the world that inherited it.
5. **Cheapness compounds.** World five cost a vocabulary and a binding. That is
   the adoption claim, demonstrated rather than asserted: the reference
   surface, the reference watcher, and the conformance kit do the work once so
   the next world does not repeat it.

## Where to start

- Building a **surface**? `owp-code/conformance/` first — make it pass.
- Building an **operator experience**? Read two that disagree: the console and
  the dossier. Then build a third that looks like neither.
- Building a **creator client**? `owp-ops/src/watcher.ts` — own your cursor and
  your clock, and take a scoped grant rather than an operator token.
- Adopting for a **new domain**? `docs/06-programming-with-owp.md`, then write
  your `types/registry.md` before you write code.
