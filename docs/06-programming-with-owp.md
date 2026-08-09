# Programming with OWP — what you build when you adopt the protocol

Spec 1.0-rc2 says what OWP *is*. This document says what is left for you, and
it exists because the boundary is the single most contested thing in the
project's history: nearly every design argument reduced to *"is this the
protocol, or is this owp-code having an opinion?"*

Five runnable domain experiences now answer it with one shared reference
implementation. `owp-code` runs a fleet
of coding agents across repositories; `owp-publish` runs an editorial desk for
news, documentation, and a novel; `owp-research` runs steerable long-form
research; `owp-ops` runs a container estate; `owp-desk` runs a freight back
office at volume. They share one surface, and no later world needed **any
changes** to the surface the coding world produced — the four places publishing
strained became spec v0.3 changes, not local patches, and research's single new
strain (a steered study's *intent* moves, and nothing can restate it — R-1) was
filed as an operator ruling rather than patched anywhere.

## The rule

> **The protocol owns the envelope and the lifecycle. You own the vocabulary,
> the rendering, and the delivery.**

If you cannot express something inside an envelope, you have found protocol
feedback — file it, do not work around it. That inversion is what keeps a
protocol from becoming one product's API.

## What you get, and never build

| The protocol gives you | So you never build |
|---|---|
| Deliverables, sessions, events with a total order, parks, policies, completion records | a work schema, an event log, a locking scheme |
| Atomic claim-on-`next` with a **total** normative chooser | assignment logic, a race between two agents, or an order that repeats under paging |
| Bounded, scoped projections: attention, portfolio, item read, fleet | "what needs me?" — computed, never curated; and no pagination of your own |
| Questions with mandatory evidence; decisions that choose and/or reject | a review workflow, an approval state machine |
| Promotion with provenance | a style guide, a runbook, or a decision log maintained by hand |
| Parks with handoffs | resumability; any agent can pick up any paused work |
| Authority classes, verb grants, and *no actor may decide its own output* | a permission model per client — and the delegation bug you would have shipped |
| `surface.describe` | a hand-fitted client per deployment |
| A normative error model | guessing which failures are retryable |
| **A conformance kit** | your own answer to "is my surface right?" |

## What you build — five layers

### 1. Your vocabulary

Fill the envelopes with the nouns your world actually has. Publish it; it is
part of your conformance statement (spec §20).

| Envelope | owp-code | owp-publish |
|---|---|---|
| `links.<type>` | `git`, `worktree` | `artifacts`, `manuscript`, `characters` |
| `kind` | feature, bug, chore, infra | chapter, scene, article, page, release-notes |
| `policy.type` | authority, review-gate | style, character-voice, structure, continuity |
| `continuation` | needs-info, redirect, rework | revise, cut, defer-to-author |
| rank tiebreak | `unblocks-others` | `manuscript.position` ascending |

Two rules learned from doing it twice: **name the type after the job, not the
tool** (`artifacts`, not `google-docs`), and **do not partition what should
compose** — a documentation deliverable carries `git` *and* `artifacts` at once,
doing different jobs.

### 2. Your operator experience

The spec defines projections, not screens. Everything about how a human meets
the work is yours — and the examples deliberately look nothing alike:

- **owp-code's console** — an operations dashboard: dark, cards, triage
  actions. The operator is an engineering manager scanning for what is blocked.
- **owp-publish's desk** — paper: each piece is a page with its editorial
  thread, and the button in the place of honour is *make this note a rule*.
- **owp-research's briefing room** — a dossier: the study reads as a living
  brief, and decisions are made *inside the document*, where their context is.
- **owp-ops's estate board** — a terminal wall: dense monospace rows, driven
  by keyboard, everything visible at once.
- **the CLI** — no screen at all; `attention` renders as text.

All five call the same verbs. None has a privileged path — anything a UI can
do, any client can do — which keeps every experience honest as an instrument
for refining the protocol: if something feels missing on screen, it is a
missing projection or verb, not a missing widget.

**There is deliberately no reference operator UI** (operator ruling). A
published shell would become the de facto "OWP interface", adopters would
conflate shell with spec, and the protocol would quietly become one client's
API — gravitational collapse through the front door. The project shows what an
OWP interface *could be*, never what it *is*: the diversity of the examples is
the showcase, and the reason it is even possible is design principle 8 —
every drop of semantics stays out of the rendering layer.

**Design guidance that survived contact with both:** put on the card everything
needed to decide from the card (the same obligation the protocol puts on
question options); show the wire vocabulary somewhere for the operator who
wants it; never make the operator open a second view to answer a first
question.

**Branch on `action`, never on `reason`.** `action` is the field the spec makes
normative — *the single act that clears this row* — and `reason` is prose
written for a person. An estate board classified rows with
`/unreconciled/.test(reason)` and would have broken silently the day a surface
reworded a sentence `[ops]`. Two consequences worth knowing before you build a
queue:

- **Not every action is yours to offer.** §15 says an `action` names the act
  that clears the row, not necessarily one the reader may perform: a drift row
  clears when the session holding the item writes its worklog forward, so an
  operator client renders it as an observation with no button. A console that
  let that row fall through to its `release` branch answered drift by yanking
  the item out of a working agent's hands `[code]`.
- **A queue is not a wall.** One item can raise two rows that are both true,
  and `review` sorts behind every health row. On a queue that is correct; on a
  board it reads as a duplicate and buries the band that needs a human. Folding,
  grouping and per-kind layout are yours — that is what `totals` is for, and it
  is the deliberate consequence of the protocol refusing to define the operator
  experience `[ops]`.

### 3. Your agent binding

The instructions that make sessions behave: when to register, when to ask
versus decide, what to write in a status line, when to park, what a completion
record should say in your world. This is rung one of the governance ladder —
convention before affordance before detection before enforcement — and it is
per-example, never per-protocol.

Two of them, side by side: the bindings share a spine and diverge exactly where
the work does.

- Both: register → `next` → progress discipline → ask with evidence → park with
  handoff → complete with a record → stop at review.
- Code: record the branch and worktree; consult policy before irreversible
  actions; dispatch blocking bugs immediately.
- Publish: read the style and character-voice rules *before drafting*; register
  every draft revision as an artifact; never quietly change an established
  fact — that is a question.

### 3b. Publish your vocabulary through discovery

Everything in layer 1 goes into `project.create({vocabulary})`, and
`surface.describe()` serves it. That one call is what lets a client it has
never met render your reject dialog, your create form, and your link types
correctly. §20 makes publishing it part of deployment conformance — the
cheapest interoperability you will ever buy.

Note what this is *not*: a shared UI. Discovery lets unlike clients adapt to an
unfamiliar surface; a shell would dictate what an OWP interface *is*. The
project ships the first and refuses the second, deliberately.

### 4. Your delivery

Where the surface runs, how clients reach it, how they authenticate. The
protocol mandates none of it (spec §17, §18). A standing HTTP surface for a
remote operator, a local database and a CLI, tokens or OAuth or environment
trust — all conforming. Both examples ship different answers: owp-code's CLI
runs direct against a local database *or* over HTTP; owp-publish's desk is a
separate server that proxies to whatever surface the deployment runs.

### 5. Your creator clients

Anything that needs a clock or watches the world is a client, because the
surface has neither. Schedulers that create proposals, watchers that unpark on
an external trigger, janitors that release claims held by dead sessions,
artifact watchers that report `unreconciled`. Each acts on its own authority
and policy — which is what keeps the surface honest about never acting on an
observation.

You likely don't build this from scratch either: **the reference watcher**
(owp-ops, `src/watcher.ts`) is the generic shape — observe, then propose /
create / unpark / report, keeping its own cursor and its own clock, needing
zero read authority. owp-desk adopted it as an import and pointed it at a
mailbox; point it at your world's feed and write checks.

It composes **no vocabulary of its own**: the `kind`, `title`, `intent`,
`links` and `priority` of every deliverable it creates come from the
observation you hand it, and the refs it minted come back keyed by that
observation's identity so you never have to match on a title. It was not
always so — owp-publish and owp-desk filed that independently as PUB-9 / D-1,
and the answer was to fix the artifact rather than the protocol (§22, and
question 1 below applied to a shared *client* instead of to the spec).

## How to know which side you are on

Four questions, in order. They are the ones that actually settled the arguments:

1. **Would a different world need this word?** `git` failed this and left the
   spec; `depends_on` passed it and stayed.
2. **Can it ride an existing envelope?** If yes, it is yours — extend and move
   on. A closed enum that two worlds want to fill differently is a bug in the
   spec, not in your world.
3. **Does the protocol's own invariant demand it?** "The surface computes and
   reports; only clients mutate" forced auto-expiry out, then forced
   surface-authored prose out. Invariants are load-bearing; consistency with
   them is a spec argument even when only one world noticed.
4. **Would omitting it make operator clients unportable?** If every deployment
   must invent the same missing capability, it is protocol. Two worlds
   independently inventing an operator item read is what made `work.view`
   normative.

## Prove it: the conformance kit

`owp-code/conformance/run.ts` runs 50 obligations against any surface **over the
wire**, through the binding, touching no internals. Each check cites the spec
section it enforces, so a failure is a sentence you can look up:

```sh
node conformance/run.ts https://your-surface --operator-token "$OP" --agent-token "$AGENT"
```

Start here if you are building a surface. It is also how the reference
implementation stays honest — the unit tests test the code, this tests the
*contract* — and it has already caught real drift: a binding answering
`NOT_FOUND` where the spec requires `UNKNOWN_VERB`, and a surface advertising a
protocol revision it had outgrown.

## The pattern in one paragraph

Adopt OWP the way you would adopt MCP: take the contract, build the interesting
part. The protocol's job is to keep two clocks from tangling — to let agents
run flat out while a human steers at the pace humans actually steer, without
either one waiting on the other. Everything downstream of that — what your work
is called, how it looks on a screen, where it runs, what your agents are told —
is yours, and the protocol is doing its job precisely when it has no opinion
about it.
