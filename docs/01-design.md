# Design — data, structure, governance

Deliberately schema-first. The visualization is downstream and may not be a board;
anchoring on kanban would import a human workflow that agents have no reason to want.

> **Packaging note (rev 4):** the durable artifact here is a protocol, not a program —
> see `03-protocol-or-program.md` for the decision and `../spec/owp-1.0-rc2.md` for
> the current revision. This document remains the design rationale behind both;
> the reference implementation is `owp-code` (called "agent-surface" while this
> document was written).
>
> **Where this document and the spec differ, the spec wins.** Known deltas after the
> pass-2/3/4 rulings (`05-spec-demands.md`): links are a typed extensible map, not
> git-shaped; `parked` is a state (explicit, released ownership, handoff required —
> questions alone never park); the protocol has **no calendar** (no due dates,
> `until`, or overdue — external triggers unpark; long-parked is observational);
> sessions bind to exactly one project and there are no global policies; rejection
> carries a mandatory reason and continuation; promotion is one mechanism with two
> targets (proposal | policy). And after pass 5: **there is no lease and no
> expiry** — the §6 table's "lease expired → auto-return" is exactly what the
> surface-computes/clients-mutate invariant forced out; recovery is a client act.

## 1. Problem

An operator directing several coding agents over weeks has no reliable way to know
where anything stands without interrupting it.

The concrete failure: an agent runs for two days across hundreds of commits and several
major features. The only way to learn where it is in the process is to stop it, ask it
to ratify current work, and ask for a summary against the original goals. That is a
back-and-forth costing time and context, and it scales linearly with the number of
agents.

Four existing categories, four different failures:

| Category | Examples | Why it fails here |
|---|---|---|
| Agent built-in to-do | Claude Code / Codex task lists | Invisible when away from the machine; lost on session restart; grows to 15–20 items, ~90% completed, burning context for nothing |
| Project management | GitHub / Forgejo Projects, Jira, Vikunja | Human workflow with agents bolted on; half-baked or absent APIs; carries the weight of a general-purpose tool |
| Agent orchestration | Vibe Kanban, Paneflow, Conductor, Claude Squad | **Development surfaces first** — they launch agents, open panes, host diff review. They assume you are at the machine |
| Documentation | STATUS.md, ADRs, specs, Spec-Driven Development | Append-only. Accumulates and drifts. Fixes "the agent drifts from intent right now", not "the corpus of intent decays over months" |

The documentation failure is worth stating precisely, because it is the one that keeps
biting: **an abandoned approach sits in the top third of STATUS.md and keeps reading as
live.** Nothing records "we started this, hit a dead end, went another way." Append-only
formats cannot express supersession, so position beats currency and the agent
confidently re-litigates a settled decision six weeks later.

## 2. Principles

1. **The operator is an engineering manager, not a reviewer.** They do not need the
   Python library version or the CI pipeline names. They need: what was built, what it
   does, what friction was hit, what the outcome was. The detail is retained for later,
   not surfaced now.
2. **The surface holds only open work — done is an exit, not a place.** Completed work
   writes its outcome and leaves. There is no Done column to review, and therefore no
   place for the surface to accumulate. History is reviewed in the knowledge base and
   git, not on the surface.
3. **Knowledge is edited in place — one copy, like a wiki, not a log.** This is the
   lesson large organisations already learned moving off scattered documents.
4. **Agents read assignments, not boards.** A board is an operator view. An agent asking
   "what is mine and what is blocking it" should not pay for everything else.
5. **Near-time by default.** The operator should never have to stop an agent to find out
   where it is.
6. **Governance is graduated, not mechanical.** Convention first, affordance second,
   detection third, enforcement last — and escalation happens only on *measured* drift,
   never on preference. See §8.
7. **Make boiling the ocean hard.** Large projects succeed by being sliced into
   digestible deliverables. The system should push toward that shape.
8. **Agents emit data, never presentation.** Records are structured (JSON against a
   schema); prose lives inside fields. Every human consumption path goes through a
   renderer — the operator surface, a CLI formatter, or a git forge rendering markdown.
   Nobody's job requires opening a raw file. Agents default to writing markdown files
   because humans built markdown, but raw markdown outside a viewer is just text;
   specifying the data instead lets each consumer get the rendering it needs.
9. **Vocabulary is governance.** "Todo" invites micro-items; "deliverable" invites
   right-sized ones. The words the schema uses steer agent behavior more cheaply than
   any hook, so they are chosen as deliberately as the fields.
10. **Design the schema first.** Agents may work in ways we would not have drawn.

## 3. Architecture: two planes

Everything follows from splitting what is *open* from what is *known*.

### Plane 1 — Working set

Only open work. Small by construction. This is what agents read by default and what the
operator sees. When an item completes it **leaves**.

### Plane 2 — Knowledge base

Living pages, one per topic, **edited in place**. Markdown is acceptable here because
its consumption path is always a renderer (git forge, operator surface). Read only on
demand — "is this still true?", "have we tried this before?" — never by default. Agents
do not browse it while working.

### The transition is the whole design

**Completion is the moment knowledge moves planes.** Closing a deliverable requires a
structured outcome (what was built, friction hit, what is now true, what this
supersedes) and the knowledge page update. The record then leaves the working set.
Altitude translation is enforced here — not by asking anyone to be diligent, but
because this is the one moment the system asks for structure, and it asks cheaply.

Two consequences worth being explicit about:

**Retrieval ranking stops being a problem.** It was only a problem because live and dead
material competed in one pile. The default read set is small and current; the archive is
queried deliberately and rarely.

**Provenance comes free from git.** Pages carry current truth only. `git log` and
`git blame` carry the history — what changed, when, and why. Supersession needs no data
model: the page says what is true now, and the diff says what it replaced. That alone
kills the abandoned-spec failure, and it costs nothing to build.

## 4. The unit of work

The surface unit is the **deliverable** — work at the altitude an engineering manager
tracks. Not a todo, not an epic. One entity, with one level of children, and a
deliberate rule about what never lands at all.

**The promotion rule: work lands on the surface when it crosses a session boundary or
needs operator attention. Everything below that stays agent-local.**

| Work | Where it lives |
|---|---|
| Multi-session feature | Deliverable |
| Work handed to a subagent (needs claim/review/coordination) | Child deliverable (`parent`) |
| A bug found mid-flight that must be dispatched and reviewed | Deliverable (`kind: bug`), dispatched immediately |
| An idea for later, needing operator prioritization | Deliverable in `proposed` state |
| A decision the operator must make | `question` event on the existing deliverable — not a new item |
| An agent's private 12-step checklist for today's session | **Nowhere. Stays in the agent's local todo list and dies with the session** |

The last row is a feature, not a gap. Agent-local todo lists (Claude Code's TodoWrite
and equivalents) are scratch state — 90% cleared, session-scoped, worthless tomorrow.
The surface is *not* a sync target for them. What must survive the session is captured
in the deliverable's worklog and `next_checkpoint` at checkpoint moments, not mirrored
item by item. Clearing a session loses nothing that mattered.

**The worklog is the story of a deliverable.** One feature with a rich worklog beats
fifty micro-stories — this is the Jira lesson inverted. Progress, notes, questions and
answers are events *on* the deliverable; nobody creates a card to record a fact.
Incremental reads (§R2 in the lessons doc) are what make long worklogs cheap: readers
resume from a cursor, never replay.

**Hierarchy is capped at two levels** (deliverable → delegated children). No epics, no
initiatives: the Project's `goal` carries direction, and a project that develops
sub-goals should be split, not stacked. `kind` (feature / bug / chore / infra) is a
flat label for operator filtering — it changes nothing about lifecycle.

## 5. Entities

Minimal on purpose. Additions require justification.

**Project** — `id`, `key` (short prefix, e.g. `AS`), `name`, `goal` (operator altitude,
one paragraph).

**Deliverable** — `ref` (`AS-12`, the *only* identifier anyone speaks), `project`,
`title`, `intent` (one line at operator altitude), `kind`, `state`, `owner_session`,
`parent` (delegation only), `depends_on[]`, `priority`,
`status_line` (one sentence at operator altitude, **edited in place** by the owner at
checkpoint moments — the wiki principle applied at field scale),
`next_checkpoint` (what the owner expects to do next — trajectory, not just position),
`links` (branch, worktree, commits, PRs — the surface doubles as the index over messy
worktrees: every in-flight deliverable names its tree, so "what is this tree for"
always has an answer).

**Session** — agent identity. `id`, `tool` (claude-code / codex / …), `host`, `project`,
`parent_session`, `started_at`, `last_seen`, `current_item`, `status`.
Sessions make subagent fan-out legible: a parent dispatches three subagents and a
reviewer, and can later cross-reference exactly which session did what.

**Event** — `item`, `session`, `kind`, `body`, `created_at`, with a total order the
client can rely on. Kinds: `progress` (cheap, frequent), `note`, `question`, `answer`,
`completed` (carries the required structured outcome fields).

**Policy** — forward-applying steering. `scope` (global / project / item), `text`,
`active`. The manager's directive lives here: *"before deploying to production, get the
pipeline running and test promotion and demotion across the SDLC."* Consulted **at the
decision point**, not buried in a spec read once at kickoff. Also carries cross-agent
constraints: *"you two must not both touch auth."*

**KnowledgePage** — a markdown file in the repo. Topic-scoped, edited in place.

## 6. State model

```
proposed  →  todo  →  in_progress  →  review  →  (done = exit, not a state)
```

- **`proposed`** — agent-suggested, awaiting operator triage. This is where backlog
  candidates from an agent land; accepting promotes to `todo`, rejecting records a
  one-line reason (negative knowledge, nearly free). Creation authority is split by
  urgency: work that must be dispatched *now* (a blocking bug) may be created directly
  into flight by an agent; work for *later* is always a proposal. The operator curates
  the backlog; agents feed it.
- **`blocked` is deliberately not a state.** An item can be progressing while one
  sub-question is open; forcing a column makes agents lie about where they are. Blocked
  is *derived* from an unanswered `question` event.
- **`review`** — retained for now (it earned its place in the dogfood), with the open
  question of whether it collapses into a flag.

Derived, never curated — this is what the operator's attention queue is computed from:

| Flag | Derivation |
|---|---|
| blocked | open `question` with no `answer` |
| stalled | `owner_session.last_seen` stale, or no events for N minutes |
| unreconciled | git shows commits on a linked branch with no corresponding events |
| lease expired | stalled past TTL → item auto-returns to `todo` with a note event |

Nobody has to remember to move a card into a "needs operator" column for the operator
to find out they are needed.

## 7. Reground

The verb that gets an agent and the operator back on the same page — and the adoption
path for the whole system.

An agent dumps its current understanding as structured data:

```
reground {
  completed[]:  work finished but never recorded  → proposed completion records
  in_flight[]:  what it believes it is working on → diffs against existing deliverables
  proposed[]:   backlog candidates                → `proposed` state for triage
}
```

**Reground never silently mutates the surface.** New items land as proposals; claims
about existing items land as diffs in the operator's attention queue ("reground
proposes closing AS-4, updating AS-7's status"). The operator one-taps accept or
reject. Two properties follow:

- A well-synced project produces an empty diff, so **reground toil is itself the drift
  measurement** — if triage feels heavy, governance needs attention, and you found out
  without an incident.
- **Onboarding is free.** Point the skill at the two-day-old agent that has been
  running across hundreds of commits, say "reground", and the surface populates from
  the agent's own understanding. No manual data entry, no stopping the work to ask for
  a summary — the summary request *is* the protocol, once, and then never again.

Use cases: onboarding an existing effort mid-flight, periodic true-up, recovery after
suspected drift, session end.

## 8. Governance: the escalation ladder

Vibe coding is deliberately loose; a system that fights that loses. Enforcement is the
*last* rung, and each escalation must be justified by measured drift, not preference.

1. **Convention** — the protocol lives in the agent definition and skill text, lean and
   at the right moment. Zero cost. Frontier models follow lean instructions well.
2. **Affordance** — make the correct path the cheapest one. Claiming returns your
   assignment in one call; completing pre-fills the outcome template from the worklog.
   Agents drift toward cheap actions; make correct = cheap and most enforcement becomes
   unnecessary.
3. **Detection** — never block, but surface drift. **Git is the ground truth**: commits
   are observed work, events are declared work, and the gap between them is the
   `unreconciled` flag. Reconciliation replaces enforcement — the books balance at
   checkpoints (reground) instead of every transaction being gated.
4. **Enforcement (hooks)** — per-tool, brittle, last resort. Reached for only where a
   specific moment shows material drift the ladder below could not absorb.

The expectation: conventions plus the git-diff regime carry ~95%. The remaining 5%
needs a human regardless of how much machinery exists, so the machinery should not be
built for it.

**What an agent reads by default:** its assignment, open questions on it, and policies
in scope. Not the board. Not the knowledge base.

## 9. Worked example — the three-bug afternoon

The scenario that shaped the requirements, walked through the model:

`AS-14 "Payments retry logic"` is `in_progress`, owned by session `cc-a1f3`.
`status_line: "Retry queue wired; writing idempotency tests."`

Mid-flight, the agent finds three auth bugs that must not wait.

- It creates `AS-15..17` (`kind: bug`) directly into flight — dispatch-now work, not
  proposals — and spawns three subagent sessions with `parent_session: cc-a1f3`.
  Each subagent claims its item; claims are atomic, so no two sessions hold one bug.
- Subagent 2 hits an ambiguity and emits a `question` with two options. `AS-16` now
  *derives* blocked; the subagent parks it and exits. Nothing was moved to a column.
- Subagents 1 and 3 finish: `completed` events with structured outcomes, review by a
  fourth session (`review` state), then the records leave the surface. The knowledge
  page for auth gets its one edit.
- `AS-14` never stopped. Its worklog carries a `note`: "found 3 auth bugs, dispatched."

The operator, remote on a tablet, sees exactly this — computed, not curated:

> **In flight (1):** AS-14 — Retry queue wired; writing idempotency tests. Next:
> tests green, then metrics.
> **Needs you (2):** AS-16 blocked on a question (two options given) · AS-15 in review.

Agent-local checklists are intentionally outside the durable protocol record.

## 10. Non-goals

Additions to this list require justification. Every lean tool that bloated did so one
reasonable feature at a time.

- **Not a development surface.** No panes, no terminals, no launching agents, no diff
  review, no built-in browser. Agents run where they already run.
- **Not an agent runtime.** It coordinates agents; it does not execute them.
- **Not a sync target for agent-local todo lists.** Scratch state stays scratch.
- **Not a general-purpose project tool.** No due dates, calendars, Gantt, sprints,
  story points, time tracking, recurring tasks, epics.
- **Not multi-user.** One operator, N agents. No teams, ACLs, sharing, or invitations —
  an entire dimension of complexity removed rather than deferred.
- **Not a document store.** Nothing append-only. Git is the history.
- **Not a replacement** for git, CI, or pull requests.
