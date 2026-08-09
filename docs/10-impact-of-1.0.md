# Impact analysis — moving to 1.0-rc2

What changed, who it affects, and what to do about it. Written for someone who
built against v0.3 and for someone starting fresh, because a compatibility
promise (§4) is only worth anything if a revision is honest
about where it bent.

## RC2 delta

RC2 supersedes RC1 and is intentionally not wire-compatible with it. A surface
now reports only `1.0-rc2`; clients that pin RC1 receive
`UNSUPPORTED_VERSION`. The required core adds `work.cancel`, the state/event
enums add terminal `cancelled`, and the HTTP annex adds JSON-only requests, a
1 MiB body bound, replay-safe mutation keys, and bounded client/proxy waits.
These changes close correctness and browser-to-loopback safety findings while
the document is still a release candidate. They would require a major revision
after 1.0 final.

Migration is explicit: regenerate types from the RC2 schema, add cancellation
handling, send `Content-Type: application/json`, use `Idempotency-Key` for a
mutation that may be retried, and branch on `UNSUPPORTED_VERSION`. Do not claim
RC1 support unless the deployment actually preserves the RC1 verb/state shapes.

The remainder records the earlier 0.3 → RC1 impact and remains useful history.

## The headline

**1.0-rc1 was not backward compatible with 0.3, and the surface no longer claims
it is.** Three changes broke shape rather than adding to it. The
release-candidate status is what makes that permissible — §4.3 says a change
like this needs a major revision, and rc1 is the last moment such a change can
land cheaply. After 1.0 final, none of the three would be allowed.

The correction that matters most is not any single change: it is that
`SUPPORTED_PROTOCOL_VERSIONS` was declaring `0.3` while the surface could no
longer serve it. Discovery (§9) exists so a client can trust what a surface says
about itself; a surface that lies in that call is worse than one that offers no
discovery at all.

## Breaking (three)

| Change | Was | Is | Who feels it |
|---|---|---|---|
| **`attention` return shape** | a bare array when unbounded, an envelope when paged | **always** `{rows, cursor, total, more}` | every operator client |
| **`attention` cursor** | an integer index into the queue | an **opaque keyset token**; clients must echo it, never construct it | any client that paged |
| **`work.view` authority** | callable by agent authority | operator/creator only | agents that read items they did not hold |

**Why each was worth breaking.** The polymorphic return made every client branch
on response *shape* — cheap for the first client, a tax on all of them. The
index cursor broke a guarantee the spec itself printed: two worlds measured
that clearing rows between pages skipped exactly as many as were cleared, and
clearing is the *normal* use of an attention queue. And `work.view` on the agent
side contradicted the design principle that agents read assignments, not boards.

**What to do.** Read `.rows`. Echo the cursor you were given, or omit it for the
first page. If an agent needed `work.view`, it was reading a board — use the
assignment packet, or make it an operator/creator client with a grant.

## Additive (safe to ignore until you want them)

- `surface.describe` — revisions, features, **your own authority and grants**,
  and the deployment's vocabulary. New clients should call it first.
- `work.update` accepts `intent` and `depends_on`; `work.reprioritize` accepts
  `urgency`. Structure is restatable by the owner *or* operator.
- `sessions()` / `session.view(id)` — the fleet projection.
- Attention rows carry `links`; `portfolio().todo` carries `depends_on` and a
  derived `blocked`.
- Grants became `{verbs, project?, states?, trigger_prefix?}`; the v0.3 spelling
  (`unpark_triggers`) is still accepted and normalized.
- Events carry `actor`; `session` remains as a **deprecated alias** for one
  revision (§4.5) — the compatibility promise applied to itself.
- A machine-readable schema ships with the revision; the prose still wins.

## Behavioural changes that are not shape changes

These will not break a client that ignores them, but they change what a correct
surface does:

- **The chooser is total.** The final tier is the creation ordinal, observable
  as the ref's sequence within a project. Batches that become eligible together
  now have a defined order — which is what makes paging safe at all.
- **The surface authors no prose.** Park, review submission, and note-less
  release write no events. A client that counted narration events will count
  fewer; a client that *displayed* them was displaying the surface's voice.
- **Grants compose** (union across grants, intersection within one) and confer
  operator-level use of their named verbs. A client holding two grants for one
  verb previously lost all but the first.
- **No actor may decide its own output**, now enforced exactly: the pending
  completion record names its author, rather than the surface inferring
  authorship from event history.

## What this cost the five worlds

Every world adopted the change in one pass, and the total edit was mechanical:
read `.rows`, drop numeric cursors, and invert the tests that had *documented*
the defects. Three suites contained tests asserting the broken behaviour on
purpose — "the cursor is a POSITION, not a place", "paging SKIPS under churn",
"a grant naming work.update does not help" — and fixing the protocol turned each
into a failing test that now asserts the resolution instead.

That is the loop working: an example documents a defect as a failing
expectation, the spec absorbs it, and the same test becomes the regression.

State at the end of that turn: **194 tests across five worlds, 33 conformance
obligations over the wire, zero surface changes required by any world's domain
logic.** (The third turn, below, took both counts up.)

## The third turn — what the final pass changed

The pass that produced this section ran five product owners over their own
worlds and one adversarial reviewer over everything. It changed the protocol
seven times and the reference implementation five. **None of the protocol
changes are breaking**; all are additive under §4.2 or are enforcement of
rules the text already carried.

### Additive (§4.2) — safe to ignore until you want them

| Change | Worlds | What a client gains |
|---|---|---|
| attention rows carry `item` (title, kind, urgency) | `[desk][publish]` | stop calling `work.view` per row per poll just to name the row |
| `work.view(order: 'oldest' \| 'newest')` | `[desk][code]` | bound a quarter-old worklog from the end you are reading |
| `open_questions[].direction` | `[research]` | tell your own upstream question from one addressed to you |

### Enforcement — no shape change, but a conformant surface now refuses more

These will not break a *client*; they will break a **surface** that was
permissive, and they may break an agent that was exploiting the permission.

- **The delegation invariant binds the act, not the verb.** Answering,
  rejecting, and appending an `answer` event are one decision, and all three
  are now guarded. An agent that answered its own question through
  `event.append` was relying on a hole.
- **Proposals are output.** A grant holder can no longer accept an item it
  proposed. A watcher configured with both `work.create` and `triage` was
  running an unsupervised loop; it now needs a second actor, which was always
  the intent.
- **`work.release` binds the class, not the session.** An agent-authority
  client with no session now needs a grant naming `work.release`. This is the
  change most likely to break a real deployment's janitor — and it is the
  point: that janitor previously had unbounded power over every project.
- **Grant scope is a conjunction on every path.** A grant naming both
  `project` and `trigger_prefix` now has both enforced on unpark. A cron whose
  scope was wider than intended will notice.
- **The queue's order is total across rows.** A surface ordering attention on
  (kind, age, target) alone must add a discriminator and carry it in the
  cursor, or paging never terminates when rows tie.

### What this cost

Nothing, across five worlds and 228 tests *as they stood at that turn* (244 and
46 obligations after the fourth) — except two reproductions that had
been written to document the defects. The kit grew to **36 obligations**: three
new ones pin the holes shut (sessionless release, the invariant by whichever
door, and paging a deliberate tie). owp-research's R-3 test asserted that a
grant holder *could* accept its own proposal; owp-code's C-4 test asserted that
a sessionless agent token *could* release anything. Both turned red the moment
the fix landed and were inverted into regressions in the same pass, which is
the third time this loop has run exactly that way.

One thing worth recording: the first cut of the R-2 fix was itself wrong. The
per-row discriminator was a string, so `q10` sorted before `q5` — the tenth
question on an item ahead of the fifth. owp-research's own strain test caught
it within a minute of the fix landing. That is the same lexicographic trap §11
hit one turn earlier, and it is the clearest evidence available that the worlds
are not simply agreeing with their author.

## The fourth turn — the open register emptied

rc1 was cut with ten findings filed, reproduced and unruled in §22. The operator
ruled all ten rather than ship 1.0 with an open register. **None is breaking.**
Eight moved the text, two were ruled out of the protocol, and every one of the
eight is a field on an envelope you already parse.

### Additive (§4.2) — safe to ignore until you want them

| Change | World | What a client gains |
|---|---|---|
| `attention().totals` — `{decision, triage, health, review}` over the whole scoped queue | `[code]` C-5 | a headline above the list without paging to the end of it |
| `work.update({kind})` — `kind` is structure, restatable by owner or operator | `[research]` R-4 | relabel a borrowed creator client's output without destroying the ref and its worklog |
| question bodies carry `direction` (`to_operator` \| `to_session`) | `[publish]` PUB-7 | a creator client with no session can ask a human; absent the field, routing is exactly what it was |
| attention rows carry `policies` when the clearing act is irreversible | `[ops]` O-8 | the standing rules on the card, for the acts that cannot be taken back |
| agent authority reaches `sessions` / `session.view` in its own project | `[code]` C-3 | resolve a peer session id without operator credentials; out of scope is `NOT_FOUND` |

### Precision — no new capability, but a surface may have been guessing

These bind **surfaces**, not clients. A permissive surface may now be
non-conformant; a client that assumed the stricter reading was already right.

- **The exit states are named.** `completed` and `rejected` are terminal states
  a read may return, alongside the five working states. A surface publishing an
  enum without them sells clients a type their own valid responses fail to
  parse — which the reference implementation did.
- **`link-number` reads `links[type][0]`**, unpositioned sorts last. Two
  conforming surfaces could previously hand two sessions different work, which
  is the one outcome §11 exists to prevent.
- **A gating question is item-local.** A park naming a question not open on
  that item is refused (`STATE`), and a decision releases parks on its own item
  only. Model a decision governing several items as an owning deliverable with
  the rest behind it via `depends_on`.
- **`action` is not always the reader's act.** A row whose clearing act belongs
  elsewhere is informational — clients must not offer it as an operator action.
  `reconcile` is the one such action in the spec.
- **Transport failure is outside §16's code set and never terminal.** A proxy
  reporting "I could not reach the surface" uses a code outside the set and
  retries; the reference deployments use `SURFACE_UNREACHABLE`.

### Ruled out of the protocol

- **D-5** `[desk]` — a first page costs more as the queue behind it grows. Real
  and measured, but §15 already permits a surface to seek from its keyset
  cursor; nothing in the text obliges anyone to materialise a queue. It is an
  owp-code implementation cost. C-5 changes its shape, not its verdict: per-kind
  counts are a `COUNT … GROUP BY`, not a materialisation.
- **O-9** `[ops]` — a queue is not a wall. Folding and grouping are the
  deployment's rendering (§3). The transferable half is guidance, now in §15 and
  `docs/06`: branch on `action`, never on `reason`.

### What this cost, and the part that should bother you

No domain example broke during that RC1 ruling pass. The RC2 release suite now
has 252 tests, green after migration. The conformance
kit grew from 38 obligations to **50**, so that nearly every
sentence this turn made normative is checked over the wire against any surface
rather than asserted in prose. That is the test of whether a ruling was real: a
precision nobody can run is an opinion with a section number.

**Two of the ten are not checked, and cannot be by this kit.** C-6 (a row whose
`action` belongs to another actor is informational, and a client SHOULD render
it as such) and PUB-11 (transport failure is outside the code set and never
terminal) are obligations on **clients**. A surface conformance kit probes a
surface; neither sentence constrains one. They are held instead by tests in the
worlds that filed them — owp-code's console asserts it renders a `reconcile`
row with no verb, owp-publish's room distinguishes an unreachable surface
and keeps serving the manuscript — which is weaker evidence than an obligation
any implementer can run, and is named here rather than counted as if it were
the same thing. A client-side conformance kit is the honest answer and does not
exist.

The part worth naming is the bar. **Five of the eight moved the specification on
one world's evidence**, which is not what §22 and `docs/09` advertise. They were
ruled in by the operator. `docs/09` now documents that third door, the four
conditions these five met (additive, at most a field on an existing envelope,
at most a value the surface already computed and discarded, and a demonstrated
expensive workaround — C-6 took the null case of the middle two, adding no
field and no value), and the caveat no rule supplies: one operator ruling over
five worlds they also own is not two independent adopters. If you think one of
the five was wrong, §22 names it, its world, and its argument — which is the
whole reason for keeping the register.

## Risk register — what could still bite

- **No independent implementation.** The conformance kit is designed to catch a
  second surface's mistakes, but nobody outside this project has run it. Until
  someone does, "conformant" means "conformant with the kit we also wrote."
  Sharpened by the final pass: the kit's own cursor obligation computed the set
  of skipped rows and then asserted nothing about it, so it would have passed
  against the very defect it was written to condemn — and the authority section
  returned silently when no agent token was set, which is the mode the
  quickstart documents. Both are fixed, and skips are now counted separately
  from passes, but the lesson stands: a kit written by the same hand as the
  surface is a weak check until someone else runs it.
- **The keyset cursor is unproven at real scale.** It is correct under churn in
  tests; it has not run against a queue of tens of thousands of rows with
  concurrent writers. It was also, until this pass, an infinite loop whenever
  two rows tied on (kind, age, target) — filed as owp-research R-2, fixed, and
  now covered by a conformance obligation that builds a tie on purpose.
- **No verifiable human identity.** `actor` is a client-supplied string and
  authority is a shared token, so no decision is attributable to a person. This
  bounds OWP out of regulated work today and is named in §22.
- **No liveness guarantee on the human side.** The protocol will never contact
  anyone. A decision-park sits until a client is opened; reaching a human is
  delivery, and delivery is the deployment's.
- **`[experimental]` §12.6** (upstream questions) is implemented in three
  worlds but has never run for months. Building on it is allowed and may cost
  you a migration.
- **Single-operator** remains the constraint most likely to force a real
  adopter to fork rather than extend. It is named in §22, not hidden.
