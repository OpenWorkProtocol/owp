# Design — data, structure, governance

The design is schema-first. Presentation is downstream and need not be a board;
starting from a Kanban model would assume a human workflow that the protocol does not
require.

> **Packaging note (rev 4):** the durable artifact here is a protocol, not a program —
> see `03-protocol-or-program.md` for the decision and `../spec/owp-1.0-rc3.md` for
> the current revision. This document remains the design rationale behind both;
> the reference implementation is `owp-code` (called "agent-surface" while this
> document was written).
>
> **Where this document and the spec differ, the spec wins.** Subsequent design
> decisions reflected in the current specification changed several early ideas: links
> are a typed extensible map rather than Git-shaped fields; `parked` is an explicit
> released-ownership state with required handoff; questions alone never park work; the
> protocol has **no calendar**; sessions bind to exactly one project; there are no
> global policies; rejection carries a reason and continuation; and promotion uses one
> mechanism with proposal/policy targets. A later revision also removed leases and
> expiry: recovery is a client action rather than a surface timer.

## 1. Problem

An operator directing several coding agents over weeks has no reliable way to know
where anything stands without interrupting it.

A representative failure is a long-running agent spanning many commits and
features while its current status is visible only inside the active session. An
operator then has to interrupt the session to reconstruct progress against the
original goals. Repeating that process across several agents consumes time and
context.

Four existing categories, four different failures:

| Category | Examples | Why it fails here |
|---|---|---|
| Agent built-in to-do | Claude Code / Codex task lists | Usually local to one session; difficult to inspect remotely; transient items can consume context after most are already resolved |
| Project management | GitHub / Forgejo Projects, Jira, Vikunja | Designed primarily for general human project management; workflow and API semantics may not match agent coordination |
| Agent orchestration | Vibe Kanban, Paneflow, Conductor, Claude Squad | **Development surfaces first** — they launch agents, open panes, and host diff review; they are optimized for an operator present in the development environment |
| Documentation | STATUS.md, ADRs, specs, Spec-Driven Development | Append-only. Accumulates and drifts. Fixes "the agent drifts from intent right now", not "the corpus of intent decays over months" |

The recurring documentation failure is stale intent: **an abandoned approach can
remain prominent in STATUS.md and continue to read as current.** Append-only formats do
not represent supersession well, so document position can outweigh recency and cause a
settled decision to be reconsidered later.

## 2. Principles

1. **The operator is an engineering manager, not a reviewer.** They do not need the
   Python library version or the CI pipeline names. They need: what was built, what it
   does, what friction was hit, what the outcome was. The detail is retained for later,
   not surfaced now.
2. **The surface holds only open work — done is an exit, not a place.** Completed work
   writes its outcome and leaves. There is no Done column to review, and therefore no
   place for the surface to accumulate. History is reviewed in the knowledge base and
   git, not on the surface.
3. **Knowledge is edited in place rather than appended as a status log.** Current
   state remains easy to locate while version control preserves history.
4. **Agents read assignments, not boards.** A board is an operator view. An agent asking
   "what is mine and what is blocking it" should not pay for everything else.
5. **Near-time by default.** The operator should never have to stop an agent to find out
   where it is.
6. **Governance is graduated, not mechanical.** Convention first, affordance second,
   detection third, enforcement last — and escalation happens only on *measured* drift,
   never on preference. See §8.
7. **Bias toward bounded deliverables.** Large projects are easier to coordinate when
   decomposed into reviewable units. The system should encourage that shape.
8. **Agents emit data, never presentation.** Records are structured (JSON against a
   schema); prose lives inside fields. Every human consumption path goes through a
   renderer — the operator surface, a CLI formatter, or a git forge rendering markdown.
   Consumers should not need to inspect raw storage files. Structured records allow
   each client to render the same information appropriately for its interface.
9. **Vocabulary is governance.** "Todo" invites micro-items; "deliverable" invites
   right-sized ones. Schema vocabulary influences how clients model work, so terms are chosen as
   deliberately as fields.
10. **Design the schema first.** The schema should not assume one agent workflow.

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

### The key transition

**Completion moves information from the working set into durable knowledge.**
Closing a deliverable requires a structured outcome (what was built, friction
encountered, what is now true, and what it supersedes) plus any required knowledge-page
update. The record then leaves the working set. This boundary is where the system
requires a concise operator-level summary.

Two consequences worth being explicit about:

**Retrieval becomes simpler.** Current work and historical material no longer compete
in one default corpus. The working set stays small and current; historical knowledge is
queried when needed.

**Version control supplies provenance.** Pages carry current truth only. `git log`
and `git blame` carry the history — what changed, when, and why. Supersession needs no
additional protocol model: the page states what is current and the diff records what it
replaced.

## 4. The unit of work

The surface unit is the **deliverable** — work at the level an engineering manager
tracks. It is larger than a session-local checklist item and smaller than a project;
one level of delegated children is supported.

**The promotion rule: work lands on the surface when it crosses a session boundary or
needs operator attention. Everything below that stays agent-local.**

| Work | Where it lives |
|---|---|
| Multi-session feature | Deliverable |
| Work handed to a subagent (needs claim/review/coordination) | Child deliverable (`parent`) |
| A bug found mid-flight that must be dispatched and reviewed | Deliverable (`kind: bug`), dispatched immediately |
| An idea for later, needing operator prioritization | Deliverable in `proposed` state |
| A decision the operator must make | `question` event on the existing deliverable — not a new item |
| An agent's private 12-step checklist for today's session | **Agent-local only; discarded at session end** |

The last row is intentional. Agent-local todo lists (Claude Code's TodoWrite and
equivalents) are transient, session-scoped scratch state. The surface is *not* a sync
target for them. Information that must survive the session is captured in the
deliverable's worklog and `next_checkpoint` at checkpoint moments rather than mirrored
item by item.

**The worklog is the history of a deliverable.** A single deliverable with a detailed
worklog is preferable to many micro-items that only record facts. Progress, notes,
questions, and answers are events *on* the deliverable. Incremental reads let clients
resume from a cursor rather than replaying the full history.

**Hierarchy is capped at two levels** (deliverable → delegated children). No epics, no
initiatives: the Project's `goal` carries direction, and a project that develops
sub-goals should be split, not stacked. `kind` (feature / bug / chore / infra) is a
flat label for operator filtering — it changes nothing about lifecycle.

## 5. Entities

Minimal on purpose. Additions require justification.

**Project** — `id`, `key` (short prefix, e.g. `AS`), `name`, `goal` (operator-level,
one paragraph).

**Deliverable** — `ref` (`AS-12`, the *only* identifier anyone speaks), `project`,
`title`, `intent` (one operator-level line), `kind`, `state`, `owner_session`,
`parent` (delegation only), `depends_on[]`, `priority`,
`status_line` (one operator-level sentence, **edited in place** by the owner at
checkpoint moments — the wiki principle applied at field scale),
`next_checkpoint` (what the owner expects to do next — trajectory, not just position),
`links` (branch, worktree, commits, PRs — the surface also indexes active
worktrees: every in-flight deliverable names its tree, so "what is this tree for"
always has an answer).

**Session** — agent identity. `id`, `tool` (claude-code / codex / …), `host`, `project`,
`parent_session`, `started_at`, `last_seen`, `current_item`, `status`.
Sessions make subagent fan-out legible: a parent dispatches three subagents and a
reviewer, and can later cross-reference exactly which session did what.

**Event** — `item`, `session`, `kind`, `body`, `created_at`, with a total order the
client can rely on. Kinds: `progress` (lightweight, frequent), `note`, `question`, `answer`,
`completed` (carries the required structured outcome fields).

**Policy** — forward-applying steering. `scope` (project / item), `text`,
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
  concise reason. Creation authority is split by
  urgency: work that must be dispatched *now* (a blocking bug) may be created directly
  into flight by an agent; work for *later* is always a proposal. The operator curates
  the backlog; agents feed it.
- **`blocked` is deliberately not a state.** An item can be progressing while one
  sub-question is open; forcing a separate column can misrepresent mixed progress. Blocked
  is *derived* from an unanswered `question` event.
- **`review`** — retained based on reference-use experience, with the open question of
  whether it eventually becomes a derived flag.

Derived, never curated — this is what the operator's attention queue is computed from:

| Flag | Derivation |
|---|---|
| blocked | open `question` with no `answer` |
| stalled | `owner_session.last_seen` stale, or no events for N minutes |
| unreconciled | git shows commits on a linked branch with no corresponding events |

The attention projection derives these conditions; clients do not need to move an
item manually into a separate "needs operator" state.

## 7. Reground

This operation reconciles an agent's current understanding with the durable surface
and also supports onboarding an existing effort.

An agent submits its current understanding as structured data:

```
reground {
  completed[]:  work finished but never recorded  → proposed completion records
  in_flight[]:  what it believes it is working on → diffs against existing deliverables
  proposed[]:   backlog candidates                → `proposed` state for triage
}
```

**Reground never silently mutates the surface.** New items land as proposals; claims
about existing items land as diffs in the operator's attention queue ("reground
proposes closing AS-4, updating AS-7's status"). The operator accepts or rejects each proposed change. Two properties follow:

- A well-synchronized project produces an empty diff, so **reconciliation effort is a
  useful drift signal**. A larger triage diff indicates that governance or reporting
  conventions may need attention.
- **Onboarding uses the same reconciliation mechanism.** A long-running agent can submit
  its current understanding through `reground`, allowing the surface to propose the
  corresponding durable state without a separate manual migration.

Use cases: onboarding an existing effort mid-flight, periodic reconciliation, recovery
after suspected drift, and session end.

## 8. Governance: the escalation ladder

Agent workflows vary in formality. Enforcement is therefore the *last* rung, and each
escalation should be justified by measured drift rather than preference.

1. **Convention** — keep protocol instructions concise and present them at the relevant
   decision point. This is the lowest-complexity coordination mechanism.
2. **Affordance** — make the preferred path the simplest one. Claiming returns the
   assignment in one call; completing can pre-fill the outcome template from the
   worklog. Good defaults reduce the need for additional enforcement.
3. **Detection** — prefer observation over blocking. **Git is the source of truth for
   repository state**: commits are observed work, events are declared work, and the gap
   between them is the `unreconciled` flag. Reconciliation happens at checkpoints
   (`reground`) rather than gating every transaction.
4. **Enforcement (hooks)** — per-tool, brittle, last resort. Reached for only where a
   specific moment shows material drift the ladder below could not absorb.

Use enforcement only where measured drift shows that conventions, affordances, and
reconciliation are insufficient. Human judgment remains appropriate for cases that
cannot be resolved safely through those mechanisms.

**What an agent reads by default:** its assignment, open questions on it, and policies
in scope. Not the board. Not the knowledge base.

## 9. Worked example — delegated bug fixes

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

Additions to this list require justification so the protocol boundary remains narrow.

- **Not a development surface.** No panes, no terminals, no launching agents, no diff
  review, no built-in browser. Agents run where they already run.
- **Not an agent runtime.** It coordinates agents; it does not execute them.
- **Not a sync target for agent-local todo lists.** Scratch state stays scratch.
- **Not a general-purpose project tool.** No due dates, calendars, Gantt, sprints,
  story points, time tracking, recurring tasks, epics.
- **Not multi-user.** One operator, N agents. No teams, ACLs, sharing, or invitations —
  an entire dimension of complexity removed rather than deferred.
- **Not a document store.** Durable knowledge is edited in place; Git carries history.
- **Not a replacement** for git, CI, or pull requests.


## RC3 software-integrity boundary

For software work, the working-set/knowledge separation is not sufficient proof
of what code was actually executed. The optional Software Work Integrity Profile
adds an Attempt-specific immutable source snapshot and independent exact-result
validation. The core coordination surface still records and round-trips state;
it does not become a Git server or trusted build executor.
