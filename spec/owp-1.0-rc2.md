# Open Work Protocol (OWP) — 1.0-rc2

Status: **release candidate, not a production-readiness claim.** Supersedes
`1.0-rc1` and `DRAFT-owp-0.3.md` (retained for history). RC2 closes findings
from the public-release audit: it adds an explicit cancellation exit, bounded
HTTP request handling, and replay-safe mutation retries. §4 states the intended
1.0 compatibility contract; until 1.0 is released, an RC may still change to
close a demonstrated correctness or safety defect.

**Evidence base and limit.** Five domain examples exercise one shared reference
surface — `owp-code` (a fleet of coding agents), `owp-publish` (an editorial
desk), `owp-research` (steerable long-form reading), `owp-ops` (a host estate),
and `owp-desk` (life admin). They are independent operator experiences, **not
independent protocol implementations**. The conformance matrix traces each
normative requirement to tests, review evidence, or a justified non-applicable
designation. Until an independently authored surface passes the kit, this
project claims reference conformance and domain portability, not demonstrated
independent interoperability. Citations appear inline as `[code]`, `[publish]`,
`[research]`, `[ops]`, `[desk]`, `[all]`.

MUST, MUST NOT, SHOULD, SHOULD NOT, and MAY are to be interpreted as described
by RFC 2119. Lowercase words are explanatory, not normative keywords.

---

# Part I — Foundation

## 1. Purpose

OWP coordinates a human **operator** and the **agent sessions** working for
them, mediated by a **surface**. It exists because those parties run on
different clocks and neither should be forced onto the other's:

> Agents work at machine speed. Operators steer at human speed. OWP is the
> synchronizer — neither side ever waits on the other's clock.

A conforming deployment MUST preserve four properties. They are the protocol's
purpose stated as tests:

**§1.1 — No agent blocks on a human.** Asking a question never stops work
(§12). An agent that genuinely cannot proceed releases the work and takes other
work; it MUST NOT idle holding a claim (§7.5).

**§1.2 — No human is interrupted to be informed.** Everything an operator needs
to steer is a projection they pull when they choose (§15) — never a
notification the work depends on.

**§1.3 — A human decision is cheap to give and expensive to be absent for.**
Every agent question MUST carry options and evidence sufficient to decide from
the card alone (§12.1). The obligation is deliberately asymmetric: assembling
evidence is cheap for machines and expensive for humans.

**§1.4 — Human-speed artifacts do not accumulate at machine speed.** Completed
work leaves the working set (§13); knowledge is edited in place, never appended.
A productive week makes the surface *smaller* `[all]`.

Two principles are purpose-level and unchanged since v0.2:

**The protocol has no calendar.** No due dates, deadlines, estimates, or
scheduled times — anywhere. Work is expressed as sequence and dependency.
Calendar semantics live outside and enter only as external triggers (§8, §10).
*Held under maximum pressure: the two most date-shaped worlds — an issue that
ships Thursday, certificates that expire, backups owed weekly — needed no
dates. Order is structural position and `depends_on`; clocks live in clients,
and periodic work is recurring **creation**, not recurrence* `[publish][ops]`.

**The protocol facilitates; it never enforces.** OWP records policies,
decisions, and their audit trails; evaluation and enforcement belong to agents,
pipelines, and operators. The invariant form:

> **The surface computes and reports. Only clients mutate work state — and
> only clients author content.**

## 2. Scope, and what OWP composes with

OWP does not cover agent↔tool access (**MCP**), agent↔agent delegation
(**A2A**), or in-session interactive UI (**AG-UI**). It composes with all three.

It follows MCP's posture deliberately, because that posture is why MCP spread:

| MCP's choice | OWP's equivalent |
|---|---|
| Defines the contract; ships reference servers, not a product | Defines records, verbs, and projections; ships a reference surface, a reference watcher, and a conformance kit |
| Auth is optional and delegated to transports | Authentication is a binding concern; the spec defines only authority classes (§18) |
| Says nothing about what a client may *do* with a tool | Says what each authority class may *call*, because OWP has asymmetric roles (§5) |
| Never defines the host UI | Never defines the operator experience (§3) — deliberately, and there is no reference UI |
| Lets ecosystems build the interesting parts | Same: the examples are benchmarks, not the product |

**Non-goals** (additions require justification): not a development surface, not
an agent runtime, not a sync target for agent-local todo lists, not a
general-purpose project tool (no calendars, sprints, story points, recurrence),
not multi-user (§5), not a document store, not a retrieval engine (§13.2).

## 3. The line: envelopes and vocabularies

> **The protocol owns the envelope and the lifecycle. The deployment owns the
> vocabulary, the rendering, and the delivery.**

An **envelope** is a structure the surface stores, round-trips, and never
interprets. Where the protocol needs open-endedness it MUST use an envelope
rather than an enumeration:

| Envelope | The spec defines | The deployment defines | Evidence |
|---|---|---|---|
| `links.<type>[]` | typed sets, round-tripped intact, replace-on-write (§7.3) | `git`, `worktree` `[code]`; `artifacts`, `manuscript`, `characters` `[publish]`; `sources` with credibility `[research]`; `hosts` `[ops]`; `documents` `[desk]` | one deliverable carries several families at once |
| `deliverable.kind` | that it exists and is a flat label | feature/bug `[code]`; chapter/scene `[publish]`; study/thread `[research]`; upgrade/verify `[ops]`; claim/errand `[desk]` | five disjoint sets, zero surface awareness |
| `policy.type` | tagged, and **interpreted, never evaluated** | authority, style, character-voice, continuity, window, scope | `character-voice` is unencodable as a condition `[publish]` |
| `rejection.continuation` | that every rejection names one; that `record-only` closes | needs-info/redirect/rework `[code]`; revise/cut/defer-to-author `[publish]`; reframe/dig-deeper `[research]`; rollback `[ops]` | a closed enum read as opaque to the operator |
| `rank_tiebreak` (§11) | the filter, the fixed tiers, and that one tiebreak may be declared | `unblocks-others` `[code][ops]`; `link-number` over manuscript position `[publish]`; none `[research]` | a world *declining* the slot proves it optional |
| `park.trigger` | that a park names its trigger; that prefixes address and scope (§18) | `window:` `[ops]`; `insurer:` `[desk]`; embargoes `[research]` | one grant mechanism, five worlds |
| `evidence[]` entries | that options carry evidence; entries round-trip | claims, citations, source ids | citations must survive `[publish][research]` |
| `project.vocabulary` | the slots (§9) | their values | §20 conformance made machine-readable |

Three corollaries, each learned by being violated:

- **A vocabulary in the spec is a bug unless every world needs it.** v0.2 named
  `git` in a core derivation; a world with no repositories exposed it `[publish]`.
- **An example may extend inside an envelope freely; it MUST NOT grow
  spec-shaped machinery of its own.** What cannot be expressed inside an
  envelope is protocol feedback, not a local hack.
- **Examples are benchmarks, not the design source.** The spec is never
  designed around an example.

## 4. Compatibility and stability

This section is what "1.0" means. It is normative.

**4.1 Frozen at 1.0.** The following MUST NOT change without a major revision:
the four §1 properties; the surface-computes/clients-mutate-and-author
invariant; the §3 envelope discipline; the verb names in §10 and their
semantics; the state machine (§8); the fixed rank tiers (§11); the authority
classes (§18); and the meaning of `record-only`.

**4.2 Additive without a revision bump.** New registered envelope values, new
optional verbs, new optional fields, new observations, and new features
declared through `surface.describe` (§9). A client MUST tolerate unknown
fields and unknown envelope values (§19).

A revision SHOULD publish a **machine-readable schema** alongside this prose
(the reference implementation emits one from its single definition:
`owp-code/schema/`). Where the two disagree, **the prose wins** — the schema is
a convenience for generating types and validating payloads, not a second
source of truth. Envelope *values* are deliberately absent from it: they belong
to the deployment and are discovered through §9, not fixed in a file.

**4.3 Breaking changes.** Removing a verb, narrowing an envelope to an
enumeration, reordering rank tiers, adding a required field, or changing an
error code's meaning are breaking and require a major revision.

**4.4 `[experimental]`.** A section marked experimental MAY change or be
removed in any revision. A surface MUST declare whether it implements one via
`surface.describe().features`, and a client MUST NOT assume it. Exactly one
section is experimental in 1.0: §12.6, upstream questions.

**4.5 Deprecation.** A renamed field ships additively: both names are emitted
for at least one revision, the old one marked deprecated, and removal happens
only at a revision that says so. 1.0 carries exactly one: the event field
`session`, superseded by `actor` (§7.4).

---

# Part II — Model

## 5. Roles

- **Surface** — the server. Holds the working set, serves projections, assigns
  event order, computes derivations. It MUST NOT act on its own initiative.
- **Agent session** — a client; one process/context of one agent tool. **A
  session binds to exactly one project for its entire life.** There are no
  cross-project sessions and no cross-project verbs.
- **Operator client** — renders projections and carries decisions back. An
  operator working several projects switches context *in the client*.
- **Creator clients** — schedulers, watchers, janitors: ordinary clients that
  create proposals, unpark on triggers, release claims, or report observations,
  each per its own policy. **A creator client SHOULD own its own memory as well
  as its own clock**: idempotency ("did I already propose 16.0?") comes from a
  cursor the client keeps, never from querying the surface — a correct creator
  client needs zero read authority `[ops]`.

**One operator, N sessions.** There is no multi-operator model.

**Role routing is experience-side.** Deployments with several humans (an author
and an editor; a reviewer and an approver) express "whose turn" in their
operator client and in `park.trigger` prose. The protocol MUST NOT gain a human
assignee field: it would import the human workflow OWP exists to avoid `[publish]`.

## 6. The project

The project is **the unit of calibration**: policies, knowledge, refs,
vocabulary, and definitions scope to it and never above it.

- What a project *is* belongs to the adopter — a repository, a manuscript, a
  publication, a host estate, a household. The protocol requires only that the
  boundary exists and that everything scopes inside it.
- **There are no global or user-level policies.** Standing rules are restated
  per project.
- Work crosses projects only as a **proposal** into the target project, or by
  **starting a session bound to the target project** (`parent_session` may
  reference a session elsewhere — lineage is just an id).

## 7. Information model

All records are JSON. Prose lives inside fields; agents emit data, never
presentation. Every human consumption path goes through a renderer.

### 7.1 Project

```json
{ "key": "PAY", "name": "payments", "goal": "One paragraph at operator altitude.",
  "rank_tiebreak": { "kind": "unblocks-others" },
  "vocabulary": { "link_types": ["git"], "kinds": ["feature","bug"],
                  "policy_types": ["authority"], "continuations": ["needs-info"] } }
```

`key` prefixes every ref (`PAY-4`). **Refs are the only identifier anyone —
human, agent, or UI — speaks, and MUST render identically everywhere.**
`vocabulary` is the deployment's published envelope values (§9, §20).

### 7.2 Deliverable

```json
{ "ref": "PAY-4", "project": "PAY",
  "title": "Payments retry logic",
  "intent": "One line, operator altitude.",
  "kind": "feature | chapter | upgrade | … (open label)",
  "state": "proposed | todo | in_progress | parked | review   (the working set)",
  "owner_session": "cc-a1f3 | null",
  "parent": "PAY-2 | null",
  "depends_on": ["PAY-1"],
  "pin": 1, "urgency": "blocking | elevated | routine", "priority": 3,
  "status_line": "Retry queue wired; idempotency tests half-green.",
  "next_checkpoint": "Tests green, then wire metrics.",
  "links": { }, "park": { } }
```

- **Voice vs structure.** `status_line` and `next_checkpoint` are the record's
  **voice**: owner-maintained, edited in place, and writable only by the owning
  session. `intent`, `kind`, `depends_on`, `urgency`, `pin`, and `priority` are
  **structure**: restatable by the owner *or* by operator authority (§10).
  Structure may change without replacing the deliverable. `kind` is included
  because it is a deployment-defined label that the surface does not interpret
  (§3); replacement would discard the ref, worklog, and provenance.
- **`state` above is the working set.** An item that leaves it (§8) keeps
  reporting a state, and reads MUST be able to say which: `completed` is §8's
  own exit, a proposal closed `record-only` (§12.3) reports `rejected`, and an
  explicitly withdrawn live item reports `cancelled` (§8). All three are
  terminal — no transition leaves them. They are defined by the protocol so
  every conforming client can parse all valid responses consistently.
- `parent` is delegation only; depth MUST NOT exceed 2.
- `urgency` is **assigned** by an operator or creator client — never computed by
  the surface, never derived from dates.
- There is no `done` state (completion is an exit, §13) and no `blocked` state
  (that is `parked` with cause `decision`, §7.5).

### 7.3 Links

```json
"links": {
  "git":        [ { "branch": "pay/retry-q", "worktree": "wt-pay4" } ],
  "manuscript": [ { "work": "the-novel", "chapter": 17, "position": 17.3 } ],
  "hosts":      [ { "host": "gohan", "service": "forgejo",
                    "observed_version": "16.1", "observed_at": "…" } ],
  "references": [ { "ref": "PAY-2" }, { "policy": "pol-11" } ]
}
```

The envelope is normative; the vocabulary is not. Surfaces **MUST preserve
(round-trip) link types they do not understand.** `references` is the one
registered type, because promotion and provenance depend on it (§12.4).

**Write semantics (normative).** `work.update(ref, {links})` **replaces each
named type's entry array wholesale**; types not named are preserved untouched.
A client patching a multi-entry type therefore supplies the complete set —
which a creator client holds in its own memory (§5), never by reading the
surface. Per-entry merge would require the surface to know an entry's identity
key, which is vocabulary and therefore out; deployments whose entries have
independent writers SHOULD model finer-grained deliverables instead `[ops]`.

### 7.4 Event

```json
{ "seq": 1042, "item": "PAY-4", "actor": "cc-a1f3 | operator | cron-window",
  "kind": "progress | note | question | answer | rejection | unparked | completed | cancelled",
  "body": { }, "at": "…" }
```

- `seq` is a surface-assigned **total order**. Clients MUST NOT order by
  timestamp.
- Reads are cursor-based (`since: seq`) and MAY be bounded by `limit`.
- **`actor`** is a registered session id **or** a client identity. Clients MUST
  be able to distinguish the two; a session id resolves through `session.view`
  (§15) and a client identity does not. *(`session` is emitted as a deprecated
  alias for one revision — §4.5.)*
- **The surface MUST NOT author events whose body is prose.** State transitions
  are recorded as state. A surface appends exactly three kinds on its own:
  `unparked` (§7.5, body is data), `completed` (§13, body is the record), and
  `cancelled` (§8, body is the client's required reason).
  Narration is a client's business. *An editorial desk, where notes are the
  product, cannot distinguish machine narration from an editor's note* `[publish]`.

### 7.5 Parked

**`in_progress` means actively held by a session in this moment; parked means
at the ready or awaiting a decision — and never held.**

```json
"park": { "cause": "decision | external", "question": 1042,
  "trigger": "answer to Q#1042 | window:sun-0300 gohan | insurer:claim-4821",
  "handoff": { "why": "…", "state_so_far": "…",
               "resume_point": "cutover step 3; data already rsynced",
               "on_release": "verify checksums, then cut over" } }
```

1. **Parking releases ownership.** `owner_session` clears.
2. **Parking MUST include the handoff payload** — all four fields.
3. **Any agent may resume after release.** The original session has no claim.
4. `question` names the gating question for `cause: decision`; if present, only
   a decision on *that* question releases the park. **The question MUST be open
   on this item** — a surface rejects a park naming one that is not (`STATE`),
   and a decision releases parks on its own item only (§12.2).
5. Release: cause `decision` releases when the question is **decided** — an
   answer *or* a rejection of it (§12.2), so a redirected question never
   strands the work parked on it. Cause `external` releases via `work.unpark`,
   by ref or by **trigger prefix** (§10). The surface holds no clock and does
   not know what a trigger means.
6. The release MUST emit an `unparked` event carrying the park payload, so the
   handoff survives into the resuming session's assignment packet.
7. Released items re-enter `todo` at elevated assignment rank (§11).
8. Inactivity observations are suppressed while parked; elapsed-parked time is
   reported as a fact.

### 7.6 Policy

```json
{ "id": "pol-11", "scope": "PAY | PAY-4", "type": "style | authority | …",
  "text": "Never 'simply' — don't trivialize difficulty.",
  "provenance": { "event": 981, "item": "REL-8" }, "active": true }
```

**Interpreted, never evaluated.** `type` is an organizational tag the protocol
attaches no semantics to; there is no condition language. Agents interpret text
at the decision point; pipelines enforce; the worklog is the audit trail. Scope
is project or deliverable; **no global scope exists.**

### 7.7 CompletionRecord

```json
{ "outcome": "Operator-altitude paragraph.", "friction": [], "now_true": [],
  "supersedes": [], "rejected": [ { "what": "…", "reason": "…" } ],
  "knowledge_edits": ["payments.md"] }
```

`outcome` MUST be present; the rest default to empty.

## 8. State and observations

```
proposed → todo → in_progress ⇄ parked → (decided/unparked → todo, elevated)
   ↓             ↓        ↓
rejected       cancelled  review → completed
```

**Three exits, all terminal.** `completed` is reached through review (§13);
`rejected` is a proposal closed with the `record-only` continuation (§12.3),
kept as negative knowledge rather than deleted; `cancelled` is an explicit
withdrawal from any working state. Nothing transitions out of an exit, and no
verb acts on an item in one — which is why a grant's `states` scope (§18)
names working states only.

Cancellation is a client decision, never expiry or surface policy:

- `work.cancel(ref, reason)` MUST require operator authority or a grant naming
  the verb, MUST require a non-empty reason, and MUST append a `cancelled`
  event attributed to the caller before the item leaves the working set.
- A surface MUST refuse a non-completed exit (`cancelled` or `rejected`) with
  `STATE` while any non-exited item directly depends on the target. The client
  cancels or rewires downstream work first; silently stranding it would violate
  the chooser's dependency contract. For the same reason, `work.create` and
  `work.update` MUST refuse `depends_on` entries already `cancelled` or
  `rejected`; only a live target or `completed` exit can ever satisfy the edge.
- Cancellation MUST clear ownership, park and pending completion data. A
  holder's `current_item` MUST also clear. A second cancellation is `STATE`.
- Cancellation is not deletion. `work.view` MUST continue to return the record,
  reasoned event, and terminal state.

Derived, never curated:

| Observation | Rule |
|---|---|
| inactive | elapsed since the owner's last heartbeat or event (in_progress only) |
| long-parked | elapsed parked |
| unreconciled | a linked entry's `observed_at` is newer than the item's last worklog event |

`unreconciled` is envelope-shaped: a **watcher client** reports what it
observed into any link entry; the surface derives the observation from data it
already holds; a session clears it by writing the worklog forward. **The
surface MUST NOT read the outside world** `[ops]`.

**The surface never acts on an observation.** There is no expiry, no
auto-release, and no protocol-level threshold — what reads as "stalled" is
deployment configuration. Recovery of work held by a dead session is a **client**
action. Elapsed time exists only as reported observations and MUST NOT schedule
or mutate anything.

---

# Part III — Protocol

## 9. Discovery

**`surface.describe()`** is the one bootstrap read. It MUST be callable without
a session. A credentialed binding MAY require a valid credential; if it does,
missing or invalid credentials answer `UNAUTHENTICATED` like any other verb.
It returns an envelope whose slots the spec names and whose values the
deployment fills:

```json
{ "protocol": { "version": "1.0-rc2", "supported": ["1.0-rc2"] },
  "surface":  { "name": "…", "version": "…" },
  "features": { "upstream_questions": true, "grants": true,
                "rank_tiebreak_kinds": ["unblocks-others", "link-number"],
                "knowledge_query": "grep | none | …",
                "projection_cursors": true },
  "authority": { "class": "agent | operator", "grants": [ ],
                 "session": { "id": "…", "project": "…" } | null },
  "verbs": [ "work.next", "…" ],
  "projects": [ { "key": "PAY", "rank_tiebreak": { }, "vocabulary": { } } ] }
```

Requirements:

- A surface MUST report the revisions it supports, and MUST answer
  `UNSUPPORTED_VERSION` (§16) to a client that pins one it does not implement.
  **How a client pins is a binding concern** — a binding MUST provide some
  mechanism and state it; the HTTP annex uses a request header (§A.5). Absent a
  pin, a surface answers in its default revision, which this call reports.
- A surface MUST report an authenticated or open-mode caller's **own**
  authority class and grants. A
  client learning its authority by receiving a `FORBIDDEN` is the failure this
  removes.
- A surface MUST list the verbs it implements, so optional features are
  discoverable rather than probed.
- A conforming deployment MUST publish its vocabulary here (§20). This is
  §3's obligation made machine-readable.
- A surface with many projects MAY report only those the caller may act on, and
  MAY omit `projects` entirely for an unauthenticated caller. Discovery is a
  bootstrap read, not a directory: a client that needs the full portfolio calls
  `portfolio` (§15), which is scoped and bounded.

This is **discovery, not a shell.** It lets unlike clients adapt to an
unfamiliar surface without sharing a skeleton — the reuse a shared UI shell
would have promised, without dictating what an OWP interface *is*.

## 10. Verbs

### Agent-side (require a registered session)

| Verb | Semantics |
|---|---|
| `session.register(tool, host, project, parent?)` | First action; binds the session to one project forever |
| `session.heartbeat()` | Cheap liveness; SHOULD piggyback on every verb |
| `session.end()` | Marks the session ended. MUST NOT release its claims — that is a client decision (§8) |
| `work.next(cursor?)` → assignment \| null | Chooses **and claims** atomically (§11). `null` is a normal answer, never an error |
| `work.claim(ref, cursor?)` → assignment | Atomic and exclusive until released |
| `work.get(ref, cursor?, limit?)` | Own item; worklog since cursor |
| `work.create(item, dispatch)` → ref | `dispatch:true` ⇒ todo; `false` ⇒ `proposed`. Dispatch MUST NOT cross projects |
| `event.append(ref, kind, body)` → seq | progress / note / question / answer / rejection |
| `work.park(ref, park)` | Explicit, always; requires handoff; releases ownership |
| `work.update(ref, {status_line?, next_checkpoint?, intent?, kind?, depends_on?, links?})` | Edit in place. Voice fields are owner-only; structure is owner-or-operator (§7.2) |
| `work.complete(ref, record, finalize?)` | → `review` (§13) |
| `work.release(ref, note?)` | Releases a claim → `todo`; a session releases only its own |
| `policy.applicable(ref)` → policies | All active policies in scope; MUST be consulted before irreversible actions |
| `knowledge.query(q)` | Deliberate and rare; never a default read (§13.2) |
| `reground.submit(payload)` | §14 |
| `sessions({project?})` / `session.view(id)` | **Own project only** — §18 lets an agent resolve session identities, and no further. An out-of-scope **id** answers `NOT_FOUND` (§15); naming another **project** outright is `FORBIDDEN`, since project keys are not secret (§9) |
| `surface.describe()` | §9 — every actor may ask what it is talking to |

### Operator / creator-client side

| Verb | Semantics |
|---|---|
| `attention({project?, limit?, cursor?})` / `portfolio({project?})` / `work.view(ref, cursor?, limit?)` | The projections (§15) |
| `sessions({project?})` / `session.view(id)` | The fleet projection; observations only. Also reachable by agent authority, scoped to the caller's own project (§18) |
| `answer(ref, question, choice, text?)` | Resolves a decision; releases a decision-park |
| `reject(ref, reason, continuation, event?)` | Operator-side rejection on a deliverable; releases a park gated on `event` |
| `triage(target, accept\|reject, reason?, continuation?)` | Proposals, review items, reground diffs. Only `record-only` closes |
| `promote(event, proposal\|policy, …)` | One mechanism, two targets, provenance attached (§12.4) |
| `event.append(ref, note\|question, body)` | The operator's non-verdict voice (§12.5) and upstream questions (§12.6) |
| `work.update(ref, {intent?, kind?, depends_on?, links?})` | Structure and links: watchers report, operators steer. Voice stays with the owner |
| `work.unpark(ref \| trigger, note?)` | Releases an external park — by ref, or by **trigger prefix**, releasing every park carrying it |
| `work.cancel(ref, reason)` | Explicit terminal withdrawal from any working state (§8); refuses while live dependents remain |
| `work.release(ref, note?)` | Recovery of any claim (§8) |
| `work.pin(ref, pin)` / `work.reprioritize(ref, {priority?, urgency?})` | Steering |
| `work.create(item, dispatch)` | An operator may commission work directly |
| `policy.set / policy.retire` | Standing rules |
| `project.create(project)` / `project.list()` | Administrative plane |

The **assignment packet** returned by `next`/`claim` is: the deliverable, its
open questions, applicable policies, and worklog-since-cursor. Not the board;
not the knowledge base.

## 11. Assignment — the `work.next` chooser

`work.next` is the most-called verb and MUST be deterministic enough that two
conforming surfaces hand the same session the same work. **`work.next` chooses
AND claims atomically**; a choose-then-claim split races two sessions onto one
item.

1. **Filter (hard, normative):** the session's project only; state `todo`; not
   held; every `depends_on` completed.
2. **Rank (soft, normative order):**

   ```
   pin → urgency → [declared tiebreak] → priority → age → creation ordinal
   ```

`pin` is the operator's ordinal and dominates. `urgency` is
blocking > elevated > routine, with recently-released parks counting as
elevated. The **declared tiebreak** is the deployment's one slot (§3);
surfaces MUST apply a declared tiebreak they understand, MUST ignore one they
do not, and MUST NOT reorder the fixed tiers. **`creation ordinal`** is the
surface's own monotonic order — not a timestamp — and makes the ranking
**total**: batches that become eligible together (a reground landing forty
items, a triage sweep, a park release) would otherwise have no defined order,
which breaks paging and interoperability alike. At volume that batch is the
normal case, not the corner: 150 items created in a few milliseconds tie on
every other key, so this tier decides everything `[code]`.

**A registered tiebreak's shape is fixed, including which value it reads.**
`unblocks-others` counts the items whose `depends_on` names this one.
`link-number` reads the named `field` of the **first entry** of the named link
type (`links[type][0]`), in array order; an item with no such entry, or a
non-numeric value there, sorts **last** regardless of direction.

The first-entry rule provides a deterministic interpretation for the registered
tiebreak. Deployments that require ranking across several link entries should
model finer-grained deliverables instead.

**The ordinal MUST be observable**, or §20 cannot check the tier that carries
§11's interoperability promise. It already is: refs are `KEY-N` with `N`
assigned in creation order within a project (§7.1), and the chooser only ever
ranks within one project — so `N` *is* the ordinal, and any client can verify
the ordering from the refs it was handed. A surface MUST NOT use a different
ordinal than the one its refs expose.

## 12. The decision loop

### 12.1 Questions

An agent `question` body MUST carry `options[]`, and **every option MUST carry
`evidence[]`** — entries are envelopes (§3) and round-trip:

```json
{ "prompt": "Two credible framings conflict — sizing differs 4×.",
  "options": [
    { "id": "A", "label": "Narrow: tooling only", "tradeoff": "cleaner story",
      "evidence": [ { "claim": "comparable to the analyst numbers we are quoted against" } ] },
    { "id": "B", "label": "Broad: incl. services", "evidence": [] } ] }
```

An empty `evidence` array explicitly represents no available evidence; a
missing array is invalid.

**A question never parks an item.** The agent keeps working everything the
answer does not touch; parking is always explicit and only for work that cannot
proceed (§7.5) `[all]`.

**A question body MAY carry `direction`** (`to_operator` | `to_session`). When
it is absent a surface infers the old default — a registered session's question
runs downstream to the operator, anyone else's runs upstream (§12.6) — so
nothing already written changes meaning.

Stating it matters because one bit, *"is the author a registered session?"*,
was deciding two independent things: the evidence obligation and the routing
direction. They are not the same question, and a creator client is the proof
`[publish]`. A watcher is a machine — cheap for it to assemble options and
evidence, so §12.1's obligation should bind it — that needs to ask a **human**,
and it had no way to say so: its class routed its question to a session, and it
had no session. **The obligation stays attached to the author's class; only the
routing moved.** A surface MUST honour a stated `direction` in both places the
routing shows: the attention queue (§15) and the assignment packet (§10).

### 12.2 Decisions

A decision **chooses and/or rejects**. Rejection always carries a `reason`.
Because both are decisions, both resolve the question and both release a park
gated on it.

**A decision is item-local.** The question gating a decision-park MUST be open
on the parked item itself (§7.5 rule 4), and answering it releases parks on
**that item only** — never every park elsewhere that happens to name the same
seq. Both ends were unstated, and two conforming surfaces could read the same
sentences opposite ways, with no test to tell them apart `[publish]`.

**One decision that governs several items is modelled, not messaged.** Mint one
deliverable that *owns* the decision — a continuity call, a design ruling — and
make the items that must bend ordinary work behind it via `depends_on` (§7.2).
The alternative, one answer fanning out across items, would put the surface in
the business of deciding which work a decision touches; that is interpretation,
and §1 forbids it. Keeping decisions item-local is what keeps `attention` and
park release simple enough to implement twice the same way.

### 12.3 Continuations

**Every rejection MUST name its continuation.** The vocabulary is an envelope
with exactly one registered value:

- **`record-only`** — closed for good; the reason survives as negative
  knowledge. **This is the only continuation that closes anything.** Any other
  continuation leaves the target alive and awaiting further work.

### 12.4 Promotion

**One mechanism, two targets.** Any decision artifact — an option, an answer, a
rejection, an editorial note — MAY be promoted into a **proposal** or a
**policy**, with `provenance` naming the originating event and item. The
provenance chain is the point: it is how runbooks, style guides, and
tried-and-rejected lists write themselves `[publish][ops]`.

### 12.5 The operator's voice

An operator or creator client MAY append `note` events to any item. A note is
**context without a verdict**: nothing changes state, and the note rides the
worklog into whichever session works the item next. Client actors are
restricted to `note` and `question`; answers go through `answer`, verdicts
through `reject`/`triage`.

### 12.6 Upstream questions `[experimental]`

An operator **or a creator client** MAY author a `question` on an item.

- It appears in the **assignment packet** of the session that holds or next
  claims the item — never in the attention queue, which is the operator's own.
- The evidence obligation of §12.1 does **not** apply *to a human*: requiring a
  human to assemble options would violate §1.3 in the direction the protocol
  protects. It is not an exemption for everything that is not a session. A
  creator client is a machine, and one that asks the operator SHOULD carry
  options and evidence exactly as a session does. A surface cannot tell the two
  apart — client identity is not a claim about being human — so this is an
  obligation on authors, not a schema a surface can enforce.
- **Direction is stated, not inferred, when the author says so** (§12.1). A
  client with no session that must ask a human sets `direction: to_operator`
  and its question routes to the attention queue; an operator asking the
  holding session may state `to_session` explicitly. Absent the field, the
  author's class decides, as before.
- Agents answer with ordinary `answer` events; answering never blocks their
  other work.
- **An operator client MUST be able to tell the two directions apart**, and a
  surface MUST let it: `work.view`'s `open_questions` entries carry
  `direction`. Routing them correctly into the queue while leaving the item
  read ambiguous is not enough — a deployment rendered its own operator's
  question back to that operator as a fork to decide, and since §12.1 excuses
  humans from assembling options, it arrived as a decision with nothing to
  decide between `[research]`.

Experimental status reflects duration, not direction: three implementations
exercise it, but no deployment has yet run it across months.

## 13. Completion and knowledge

### 13.1 Completion

`work.complete` MUST include a valid CompletionRecord. Two planes meet here, and
this is the only moment the protocol asks for structure — so it asks cheaply.

1. `work.complete(ref, record)` moves the item to `review`, releases ownership,
   and holds the record pending **with the actor that authored it**. Agents
   stop here unless project policy says otherwise — the *client* interprets
   that policy, not the surface.

   Recording the author is what makes §18's delegation invariant *checkable*:
   "no actor may decide its own output" is normative and explicitly the thing
   no deployment can express for itself, yet without an author a surface can
   only guess at it from event history `[desk]`. One field turns a heuristic
   into a rule.
2. The operator accepts → the item exits with a `completed` event carrying the
   record; or rejects with a reason and a continuation → the item returns to
   `todo`, record cleared, reason retained.
3. A client with appropriate authority MAY complete straight to exit where the
   deployment's policy allows it.

### 13.2 The knowledge plane

- **Working set** — only open work; small by construction. Completed work
  **leaves**.
- **Knowledge** — living pages, edited in place, read on demand. Provenance
  comes from the version control the pages live in; supersession needs no data
  model, because the page carries current truth and the diff carries what it
  replaced.

The protocol defines this **contract** and not a retrieval mechanism.
`knowledge.query` is deliberately thin; a surface declares its retrieval
capability through `surface.describe().features.knowledge_query` and MAY
answer `none`. Retrieval strategy — grep, full-text, embeddings — is the
deepest deployment concern there is, and a protocol that specified it would be
specifying a search engine.

## 14. Reground

`{ completed[], in_flight[], proposed[] }`. **Reground never silently mutates.**
Proposals land as `proposed`; claims about existing or finished work land as
operator-triaged diffs. A well-synced project produces an empty diff, so
reground toil *is* the drift measurement. Onboarding a long-running agent is
one call.

## 15. Projections

Projections are how human speed is served without touching machine speed: they
are computed reads, and **nothing an operator does to read changes work state**.

- **`attention({project?, limit?, cursor?})`** → `{rows, cursor, total, totals,
  more}` — open decisions (oldest first) → triage → health (observations only)
  → review. Every row carries: ref, a one-line reason, elapsed age, the single
  action that clears it, the deliverable's **`links`**, **what the row is
  about** (`item`: title, kind, urgency), **the standing rules that govern an
  irreversible action** (`policies`, below), and **a detail payload sufficient
  to decide from the row**. The order is total, so paging neither repeats nor
  skips.

  `item` is here because "sufficient to decide from the row" failed the same
  way in two unrelated worlds: three of the four row kinds named a ref and not
  a title, so a dispatcher could see the customer and the lane but not *which
  load*, and an editor could not tell whether a question sat on chapter 17 or
  on a continuity item minted an hour ago `[desk][publish]`. Both clients
  answered by calling `work.view` on every open row, every poll. A surface
  holds the deliverable at the instant it attaches `links`; withholding the
  three fields beside them sells every operator client an N+1 read.

  Links ride every row because they are the one envelope a deployment has for
  its own nouns: without them a dispatcher cannot see the customer and lane and
  an editor cannot see the manuscript position, which makes "sufficient to
  decide" false in exactly the deployments that filled the envelope
  `[desk][publish][ops]`.

  The envelope is returned **always**, whether or not the caller bounded the
  read. A stable response shape avoids shape-dependent client logic. `total`
  and `more` allow clients to distinguish the returned page from the complete
  scoped result.

  **`totals` breaks the count down by kind** — `{decision, triage, health,
  review}` — over the **whole scoped queue, never the page**. "23" is not an
  answer to the question a first screen exists to answer: three decisions and
  forty in review carry entirely different urgency, and only one of them means
  an agent is waiting on a human `[code]`. There is one unambiguous way to
  derive this without the field, and it is expensive in the wrong place: rows
  arrive in kind order, so every kind ending before the last loaded row is
  exact and everything after it is a floor. The number that matters most at
  volume is review load — the *last* kind — so it is never exact without paging
  the entire queue from a device that wanted one screen. A surface materialises
  or counts the whole scoped queue to answer `total` at all, so the breakdown
  costs it a `GROUP BY` and saves every client a dozen round trips. That
  asymmetry is this section's own test for when withholding a computed value
  makes operator clients unportable.

  **`policies` carries the standing rules for an act that cannot be undone.** A
  row MUST carry the applicable policies (§7.6, same set and order as
  `policy.applicable`) when the action that clears it is irreversible, and the
  field is absent when none apply. §10 makes an agent consult policy before an
  irreversible action and hands it the applicable rules in its assignment
  packet; the operator's own projections handed them nothing, so for the one
  class of decision an estate exists to make safe, the payload this section
  calls "sufficient to decide from the row" was missing the rules the operator
  wrote themselves. The asymmetry runs backwards from §1.3: the machine was
  briefed and the human — slower, more tired, more likely to be on a phone —
  was not `[ops]`. `triage`, `answer` and `unpark` are irreversible; `release`
  is not (the item returns to `todo` and keeps its worklog), and `reconcile` is
  not the reader's act at all.

  **`action` names the act that clears the row — not necessarily an act its
  reader may perform.** A row whose clearing act belongs to another actor is
  **informational**: a client MUST NOT offer it as an operator action and
  SHOULD render it as an observation. `reconcile` is the one such action this
  document defines — §8 says a session clears drift by writing the worklog
  forward, so nothing an operator client offers will clear that row. The danger
  is specific and was shipped: a console that fell through to a `release`
  branch answered a drift row by yanking the item out of a working agent's
  hands `[code]`. Clients branch on `action`; `reason` is prose for a person
  and never a contract.

  **The order MUST be total, and totality is a property of rows, not of
  items.** §11 orders the *work*; this orders the *queue*, and one item can
  raise several rows at one instant — two open questions, two link entries
  reporting drift. A surface MUST therefore order on something that separates
  two rows of the same kind, on the same target, at the same age, and MUST
  carry that discriminator in the cursor.

  This is not a fine point. A surface that orders on (kind, age, target) alone
  has no order *within* a tie, so a cursor naming only those three resolves to
  the head of the tie group on every call: the same row is served forever and
  the rest of the queue is unreachable. The reference implementation shipped
  exactly this and its own conformance check did not catch it — measured at six
  open questions on one item, one distinct row across twenty-one pages
  `[research]`. Paging is the one guarantee this section makes; it fails
  silently, and it fails as an infinite loop rather than as an error.

  **`cursor` MUST be a place, not a position.** It is an **opaque token**
  identifying the last row returned; a surface resumes *after that row* in the
  total order. Clients MUST echo it unchanged, and MUST NOT construct it, parse
  it, or do arithmetic on it.

  An index cursor breaks the guarantee this section makes. Two worlds measured
  it independently: read a page, clear some of it, ask for the next page, and
  every remaining row has shifted — the queue skips exactly as many rows as
  were cleared, and the operator never learns which `[desk][code]`. Clearing
  work is the *normal* use of an attention queue, so an offset is wrong in the
  common case, not the corner case. An opaque token also leaves the surface
  free to change its encoding, which an index never does.
- **`portfolio({project?})`** — per project: working-set size, in-flight items
  with status lines and next checkpoints, parked with cause and trigger,
  review, todo, proposed. Todo entries carry `depends_on` and a derived
  **`blocked`** (any dependency not completed). The surface already computes
  this for §11's hard filter; withholding it made every deployment with staged
  work write the same N+1 loop and invent its own meaning for "blocked"
  `[ops][desk]`. It is an observation (§8) — reported, never acted on.
- **`work.view(ref, cursor?, limit?, order?)`** — the operator-side item read:
  the deliverable, any pending completion record, open questions, and worklog
  since cursor. **Operator/creator authority**: agents read assignments, not
  boards.

  `order` (`oldest` | `newest`, default `oldest`) selects which **end** a
  bounded worklog is taken from; the page itself stays chronological. A bound
  that only reads from the front is the wrong end for this verb's only caller:
  an operator opening an item that has run for a quarter wants what happened
  today, and both an operator console and a load board answered by fetching the
  whole log and discarding the front of it `[desk][code]`.

  Each entry in `open_questions` carries **`direction`** (`to_operator` |
  `to_session`). §12.6 makes the routing normative — an operator's question
  appears in the holding session's assignment packet, never in the operator's
  own queue — but this array showed both directions with nothing to tell them
  apart, and a deployment shipped the consequence: the analyst's own question
  came back to them as a fork to decide, with no options, because §12.6 excuses
  humans from the evidence obligation `[research]`. A surface already knows
  which is which; the silence was the defect.
- **`sessions({project?})` / `session.view(id)`** — the fleet: tool, host,
  project, lineage, current item, status, and elapsed idle time as a **fact**
  (§8), never a threshold and never an action.

  These are the two reads **agent authority also reaches**, confined to the
  caller's own project (§18). §7.4 requires every client to tell a session id
  from a client identity, and a session already sees peer ids in
  `owner_session`, so refusing the resolution outright makes that a requirement no
  agent can obey. A surface answers an out-of-scope **id** with `NOT_FOUND`,
  never `FORBIDDEN`: a refusal that distinguishes the two confirms that a
  session the caller may not resolve exists. Naming another **project** is a
  different question and is refused plainly (`FORBIDDEN`) — project keys are
  already public through `surface.describe` (§9); which sessions are inside one
  is what the scope protects.

## 16. Errors

A surface MUST answer failures with these codes. Clients branch on them, so
they are protocol, not binding detail. Transport mapping belongs to the binding
annex (§17).

| Code | Meaning | Required client behaviour |
|---|---|---|
| `VALIDATION` | args or body failed the schema | terminal; fix and resubmit |
| `UNSUPPORTED_VERSION` | pinned revision not implemented | retry using a revision from `describe` |
| `UNKNOWN_VERB` | verb not implemented by this surface | terminal; consult `surface.describe` |
| `UNAUTHENTICATED` | no valid credential | terminal until credentials change |
| `SESSION_REQUIRED` | session-bound verb without a session | register, then retry |
| `FORBIDDEN` | authority, grant, or project-boundary violation | **MUST NOT retry**; audited (§18) |
| `NOT_FOUND` | unknown ref, session, event, or policy | terminal |
| `CONFLICT` | the item is already held | re-read or call `work.next` again |
| `STATE` | legal target, wrong state | re-read before acting |

A surface MAY add codes; a client MUST treat an unrecognized code as terminal.

**Transport failure is not one of these codes, and is not itself terminal.** Every
code above describes a surface that *answered*. A client that could not reach a
surface at all has no answer to relay, and MUST NOT invent a code in this set
for it — the rule above would then make the one condition every client should
retry the one condition it gives up on. This does **not** authorize a blind
retry of a mutation: the client MUST use its binding's replay protection with
the same operation key, or reconcile by reading before deciding whether to
resubmit. A client SHOULD use bounded exponential backoff with jitter and MUST
stop retrying when its local operation deadline or cancellation signal fires.
A proxying operator client (§17) that
must report the failure in this envelope SHOULD use a code outside the set and
treat it as retryable; the reference deployments use `SURFACE_UNREACHABLE`.

Explicit handling is required because clients previously discarded this
distinction `[publish]`. A deployment whose knowledge plane and
manuscript live on its own side can keep answering with the surface down and
say exactly which half is out — *"the book is fine; only the questions live on
the other side"* — and it can only say that if "unreachable" is distinguishable
from "the surface said no".

---

# Part IV — Deployment

## 17. Bindings and delivery

**Delivery is the deployment's, not the protocol's.** One deployment runs a
standing HTTP surface for a remote operator; another keeps a local database and
a CLI; another emits into an existing tracker. The protocol mandates none of it.

- **HTTP+JSON is the normative binding annex** — [`annex-http-1.0-rc2.md`](annex-http-1.0-rc2.md):
  `POST /v0/<verb>`, actor identity in headers, `{ok, result}` /
  `{ok:false, error:{code, message}}`, the §16 codes mapped to statuses, and
  revision pinning and replay protection. It defines the interoperability
  target for independent implementations; current evidence covers the shared
  reference implementation only. A deployment may carry the verbs another way.
- **CLI, MCP tools, and in-tool skills are adapters**, not foundations. An MCP
  adapter is legitimate for runtimes whose only extension point is MCP; it does
  not change the contract.
- **Agent bindings are per-example.** The instruction set that makes sessions
  behave is experience: same verbs, different discipline, different words.
- Where a session finds its surface is a deployment convention (an environment
  variable, a committed config file, a default local database).

## 18. Security — authority, authentication, audit

Three concerns; the protocol owns exactly one.

- **Authentication — delegated entirely.** Static tokens, OAuth 2.1, mTLS, or
  environment trust for local transports: the spec specifies none of it,
  exactly as MCP delegates auth to its transports.
- **Authorization — the protocol's part**, because OWP has asymmetric roles.
  Two classes are normative:
  - **Agent authority**: sessions, work, events, own-claim release, discovery.
    MUST NOT triage, promote, set or retire policy, cancel work, unpark others' triggers,
    release others' claims, or delete. **`work.release` is agent authority only
    for the caller's own claim**; releasing another session's claim requires
    operator authority or a grant — which is what makes the janitor grant
    (`{verbs:["work.release"]}`) mean something rather than restate a power the
    class already had `[code]`. This binds the **class**, not the session: an
    agent-authority client that registered no session holds no claim of its
    own, so it needs the grant like anyone else. A surface that tests "is this
    a different session?" instead of "does this actor own this claim?" leaves
    the whole estate open to any credential that simply omits a header — which
    the reference implementation did `[code]`.
    An agent MAY resolve session identities **within its own project**
    (§15) — §7.4 requires every client to tell a session id from a client
    identity, and a session already sees peer ids in `owner_session`, so the
    resolution leaks nothing and the alternative is a requirement no agent can obey.
  - **Operator authority**: every verb.
- **Grants.** A grant is agent authority **plus named verbs under an optional
  scope**: `{verbs, project?, states?, trigger_prefix?}`. A window cron holds
  `{verbs:["work.unpark"], trigger_prefix:"window:"}`; a reviewer holds
  `{verbs:["triage"], project:"PAY", states:["review"]}`; a janitor holds
  `{verbs:["work.release"]}`.

  Two rules make the model coherent, and both were learned by getting them
  wrong `[ops][desk]`:

  - **A grant confers *operator-level* use of the named verbs within its
    scope** — including verbs the agent class may already call in a narrower
    way. Otherwise a grant naming `work.update` would mean nothing, since
    agents already call it. A grant never reaches the record's *voice*
    (`status_line`/`next_checkpoint`), which belongs to the owning session.
  - **Grants compose: union across grants, intersection within one.** A client
    holding `{work.unpark, "window:"}` and `{work.unpark, "lock:"}` owns both
    prefixes. A surface that resolves only the first grant naming a verb
    silently voids the rest. "Intersection within one" is the half that is
    easy to half-implement: **every field a grant names MUST hold**, on every
    path the verb can be reached by. A surface that checked `trigger_prefix`
    and ignored `project` left both things grants exist to bound — a janitor
    and a cron — unbounded `[code]`.
- **The delegation invariant (normative):**

  > **No actor may decide its own output.** A grant holder MUST NOT triage an
  > item whose pending completion record it authored, MUST NOT accept an item
  > it proposed, and MUST NOT answer or reject a question it asked.

  This is what makes delegation safe, and no deployment can express it for
  itself `[code]`. Three properties of it are load-bearing:

  - **It binds the act, not the verb.** A decision that resolves a question and
    releases its park is the same decision however it is spelled — the `answer`
    verb, a rejection, or an appended event of kind `answer`. A surface that
    guards one door and leaves the others open has made the invariant a
    question of which call the actor chose, which is no invariant at all. The
    reference implementation guarded exactly one door `[code]`.
  - **Proposals are output.** A watcher's entire job is producing proposals; a
    grant that can both propose and triage is an unsupervised loop that admits
    its own finds with nobody in it `[research]`.
  - **Authorship is recorded, never inferred.** A surface enforcing this MUST
    know who authored the completion record and who proposed the item. Deriving
    it from event history is guesswork that fails on exactly the items with
    complicated histories `[desk][research]`.

  A surface that cannot determine authorship for a given item MUST NOT
  substitute a guess: the invariant does not apply when the required
  authorship fact was not recorded.
- **Audit.** Surfaces SHOULD log every verb call with its actor, **including
  denials**.

## 19. Extensions and registered names

- **Registered names** are the values whose semantics this document explicitly
  defines: the link type `references`; the continuation `record-only`; and the
  tiebreak kinds `unblocks-others` and `link-number`. Example-local link types
  such as `git`, `hosts`, `sources`, and `artifacts` are vocabulary examples,
  not registered protocol names. Registered shapes are stable per §4, and a
  **shape includes which
  value the name reads** — a stable name over an unstated reading is not a
  registration, it is two implementations waiting to disagree. `link-number` is
  pinned in §11 for exactly that reason.
- **All other names are the deployment's.** Two deployments MAY use the same
  name for different shapes; they do not interoperate on that name, which is
  the expected consequence of local vocabulary.
- **Must-preserve, must-ignore.** A surface MUST round-trip envelope values it
  does not understand and MUST NOT reject them. A client MUST ignore unknown
  fields and unknown envelope values rather than fail.
- **No-calendar reserved names.** The field names `due`, `deadline`,
  `due_date`, and `expected_by` are reserved so the §1 no-calendar invariant
  cannot be reintroduced accidentally as a deployment extension. When one is
  supplied on a protocol record, a surface MUST either reject the record or
  ignore the field. It MUST NOT store, return, rank, transition, schedule, or
  otherwise interpret the value as protocol semantics. This rule is about
  fields, not open envelope values: deployments remain free to use temporal
  words inside their own links, triggers, policies, and prose.
- A deployment publishes its vocabulary through `surface.describe` (§9) and
  SHOULD document it in prose beside its code.

---

# Part V — Conformance

## 20. Conformance

- **Surface** — every §10 verb it declares; total-order events; atomic
  claim-on-next; the §11 chooser including declared tiebreaks and the total
  ordering; §8 observations without acting on them; typed-link round-trip and
  replace-on-write; no surface-authored prose; the §16 error codes; §9
  discovery.
- **Operator client** — attention, portfolio, work.view, sessions, answer,
  reject, triage with continuations, promote, note, unpark, cancel, release,
  steering.
- **Minimal agent** — register, heartbeat, next/claim, progress + question
  events, status_line update, complete.
- **Full agent** — + create/dispatch, park/handoff, rejection + continuation,
  policy.applicable, reground, cursors, release, structure restatement.
- **Creator client** — create and/or unpark and/or release and/or report
  observations, per its granted authority, owning its own memory and clock.

**A conforming deployment MUST publish its vocabulary** through §9.

**The conformance kit.** A runnable suite exercises these obligations over the
wire, through the binding, touching no internals; each check cites
the section it enforces. An implementation is conformant when the kit passes
against it. It ships in the reference implementation
(`owp-code/conformance/`) and is the intended starting point for anyone
building a surface.

### 20.1 Build order for a new surface

The following implementation order permits incremental conformance validation.
Each stage produces an independently testable subset of the surface.

1. **Records and identity** — projects, deliverables, refs (`KEY-N`, assigned in
   creation order — §11 depends on it), and the event log with its
   surface-assigned total order.
2. **The claim** — `session.register`, `work.next`, `work.claim`, `work.release`.
   Claim acquisition must be atomic before concurrent mutation is introduced.
3. **The chooser** — the §11 hard filter, then the fixed tiers. Declared
   tiebreaks and total ordering.
4. **The loop** — events, questions with evidence, decisions, continuations,
   parks with handoffs, completion and review.
5. **The projections** — `attention` (bounded, with the keyset cursor),
   `portfolio`, `work.view`, and `sessions`.
6. **Discovery and errors** — `surface.describe` and the §16 codes.
7. **Authority** — the two classes, then grants. A single-user deployment can
   use loopback open mode; routable or delegated deployments require an
   authenticated binding that preserves the authority distinction.

A partial implementation may be useful for local development but is not a
conforming OWP surface until all applicable requirements in §20 are satisfied.

## 21. Revision history

RC2 supersedes RC1. It adds terminal cancellation, replay-safe HTTP mutation,
bounded request handling, loopback browser protections, explicit shutdown,
and clarifications to extension, authority, recovery, and compatibility
semantics. Detailed compatibility and migration information is maintained in
[`CHANGELOG.md`](../CHANGELOG.md) and
[`docs/10-impact-of-1.0.md`](../docs/10-impact-of-1.0.md).
