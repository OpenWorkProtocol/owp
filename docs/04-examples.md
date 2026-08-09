# OWP launch examples — the headliner candidates

Status: **historical — all five are built.** This document chose the lineup and set
the admission test; it is kept for the reasoning, not as current state. What each
world actually became is in [`08-the-five-worlds.md`](08-the-five-worlds.md), and the
worlds themselves are the five sibling repositories.

The one thing here that outlived the decision is the **admission test** below (four
conditions an OWP example must pass). It is still the filter — it is what keeps the
protocol from claiming territory MCP, A2A, or a plain queue already serve.

Original status: launch lineup decided 2026-07-27. Refs E1, E2, E5, E7 resolved by the
operator; E3/E4 resolved as fast-follows. Naming: F10 resolved — **OWP,
openworkprotocol.io acquired.**

## Decisions (operator, 2026-07-27)

- **E1 — confirmed.** owp-code is the headliner and reference implementation.
- **E2 — confirmed.** owp-ops is launch PoC #2 with **zenet as its proving ground**.
  Validated by a real incident: the operator's forgejo ran v14 while v16 was current,
  discovered only when an agent requested a repo-scoped deploy key — a feature added
  in v15. The operator had even built a tool in this space (DockerDeck) but version
  awareness wasn't its job; the fix meant dropping everything to babysit an
  agent-orchestrated upgrade. Under owp-ops a release watcher would have *proposed*
  the upgrade at machine time — noticed, proposed, approved, executed, and the new
  features documented — before the missing capability ever blocked work. Patching at
  machine time beats reacting after the fact, for vulnerabilities most of all.
- **E5 — promoted.** owp-publish is **launch PoC #3, gated on #1 and #2 proving
  out.** Beyond newsletters/docs, the operator names a distinctive use case: the
  editorial desk for **book authoring** — style and voice defined as policies down to
  per-character calibration, chapters and scenes worked non-linearly as deliverables,
  continuity questions surfaced by the desk, character/world pages as living
  knowledge. Not a writing tool: an *editor* that keeps a many-threaded manuscript
  coherent.
- **E7 — resolved by the above.** Launch = spec + reference surface + owp-code +
  owp-ops + owp-publish (gated). owp-research (E3) and owp-desk (E4) become
  fast-follows.

## Why this document exists

MCP's launch worked because the protocol shipped with examples that needed no
explanation: filesystem, git, fetch. Filesystem was the one that took off — not
because it was clever, but because everyone instantly understood the before/after.
OWP needs the same: a handful of benchmarks where a thing that already exists gets
*visibly, obviously better* under the protocol. This is the candidate lineup.

**The test for a good OWP example** (all four must hold):

1. The work outlives a session — days, not prompts.
2. The worker can *keep working* when a question is open (or park one item and take
   another). If every question halts everything, AG-UI's synchronous loop suffices.
3. The human's judgment is cheap to give but expensive to be absent for — options,
   spend approvals, taste, risk calls.
4. The outcomes compound — what was decided/tried/rejected matters months later.

**Anti-examples** (fail the test, use something else): a chat turn (AG-UI), a single
tool call (MCP), one refactor inside one session (agent-local todos), fully
automatable pipelines with no judgment moments (cron/CI). Naming what OWP is *not
for* is part of being a credible protocol.

**Prior art that proves the pattern:** Renovate/Dependabot — machine-speed workers,
human-speed review queue, beloved for exactly that crossing, and hard-locked to one
work type (dependency bumps). OWP is that interaction model, generalized.

---

## 1. owp-code — run an engineering org of agents `[the filesystem moment]`

The origin story; the whole storyboard. Fleet of coding agents across projects and
worktrees; the operator as engineering manager, remote, steering from a tablet.

- **Today:** STATUS.md exhaust, invisible in-session todos, interrogating a two-day
  agent to learn where it is.
- **With OWP:** the 7:40am triage — two decisions, one approval, zero interruptions.
- **Primitives exercised:** all of them. This is the conformance workout.
- **Why nothing does it:** the orchestration tools are cockpits; the trackers have
  no concept of a session, lease, or altitude.

## 2. owp-ops — the self-maintaining homelab / infra estate `[dogfoods day one]`

Maintenance agents across a server estate: version upgrades, cert rotation, backup
verification, service migrations between hosts.

- **Today:** cron + logs read after the fact, Renovate for deps only, or an agent
  session you babysit.
- **With OWP:** the 3am upgrade agent hits a breaking config change on one host. It
  doesn't fail the run and doesn't guess — it parks that host with a question
  (*"forgejo 16 drops this key: migrate config or pin? options attached"*), upgrades
  the other four, and the question is on your phone at breakfast. Policies carry the
  standing rules: *never reboot gohan during trading hours; no destructive step
  without sign-off.* Leases catch the migration agent that died halfway.
- **Primitives:** questions-without-stopping, policy-at-decision-point, leases,
  completion→knowledge (the friction log IS the runbook next upgrade).
- **Why it matters strategically:** immediately dogfoodable on the zenet estate, and
  it proves OWP is not a coding-agent accessory.

## 3. owp-research — deep research you can steer mid-flight

Research agents running hours or days: market analysis, literature review, due
diligence, competitive landscape.

- **Today:** fire-and-forget. A 40-page report arrives; the framing was wrong; the
  whole run is wasted. Steering requires sitting in the loop.
- **With OWP:** research threads are deliverables with status lines (*"14 sources
  read; two credible framings conflict"*). The fork becomes a question answered at
  lunch — redirecting six hours of machine-speed reading *before* they're spent.
  Scope policies (*exclude paywalled; primary sources for anything quantitative*)
  apply at decision points. Tried-and-rejected framings land in knowledge, so next
  quarter's run doesn't re-litigate them.
- **Primitives:** question/answer as steering, policy-as-scope, status_line,
  knowledge supersession.

## 4. owp-desk — an operations desk for your life `[the civilian example]`

The insurance claim, three contractor quotes, the travel rebooking, the warranty
RMA — multi-day, bursty, waiting-heavy processes an agent can work at machine speed.

- **Today:** either you do it, or an assistant-bot asks you to confirm every step —
  which is just the work with extra steps.
- **With OWP:** the agent works forms, emails, and hold queues; every
  spend/commit/personal-data moment is a question with options; **policy is spending
  authority** (*under $50, just do it; over, ask with options*). Three quotes arrive
  as one card with tradeoffs; you answer from the couch; the booking happens at
  machine speed.
- **Primitives:** dispatch-now items, questions-with-options, policy-as-authority.
- **Why it matters strategically:** the example a non-engineer understands in one
  sentence. Policy-as-spending-cap is instantly legible governance.

## 5. owp-publish — the editorial desk

Content pipelines: docs sites, newsletters, changelogs, release notes.

- **Today:** an agent drafts in one session; your style feedback evaporates with the
  session; the next draft re-litigates voice from zero.
- **With OWP:** pieces move through `review` as a real editorial state; every
  correction you make can be promoted to a policy applied at decision points (*never
  "simply"; active voice; Oxford comma*); completion records make the style guide a
  living document that maintains itself. The correction you made in March is still
  steering drafts in July, un-reprompted.
- **Primitives:** review as first-class, policy-as-style, knowledge-as-living-guide.

---

## Further afield (named, not launched)

Lab/instrument automation (overnight experiments, PI steering), long-running quant
research campaigns, compliance/back-office ops. Real, but not launch material.

## Launch shape `[decided]`

Mirror MCP: **spec + reference surface + three working examples.**

1. **owp-code** — the reference implementation; proves depth (all primitives).
2. **owp-ops** — proves generality beyond coding; dogfoods on zenet immediately.
3. **owp-publish** — gated on 1–2 proving out; proves the protocol leaves
   engineering entirely (editorial desk, including book authoring).

Fast-follows: **owp-research**, **owp-desk**. Two examples deep and identical in
shape is a demo; three across different worlds is a protocol.

## Feedback refs

- **E1** owp-code as headliner framing
- **E2** owp-ops as second launch PoC (and zenet as its estate)
- **E3** owp-research — worth launch slot or fast-follow?
- **E4** owp-desk — civilian example: launch, or keep the launch technical?
- **E5** owp-publish — include or park?
- **E6** the four-part test + anti-examples list
- **E7** launch shape: spec + surface + three examples
