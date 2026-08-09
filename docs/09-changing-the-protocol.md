# Changing the protocol

OWP reached 1.0 by refusing most proposals. This document says how it refused
them, so that anyone can propose a change and know in advance what would make
it succeed. The process is not bureaucracy — it is the reason the spec is small
enough to implement in an afternoon.

## The bar

> **A change enters the protocol when two unrelated worlds need it, or when the
> protocol's own invariants demand it. Everything else is vocabulary.**

Two independent worlds is the operative test because one world's need is
indistinguishable from one world's opinion. Every change that entered through
the front door met it — see *the third door* below for the five that did not:

| Change | Worlds that hit it independently |
|---|---|
| Restatable structure (`intent`, `depends_on`, `urgency`) | research, publish, code, desk |
| The operator item read (`work.view`) | code, publish |
| Link write semantics | ops, research |
| Bounded projections | code, desk |
| `surface.describe` | all five, each publishing a vocabulary by hand |

The invariant clause is the other door, and it is narrower: consistency with
*the surface computes and reports; only clients mutate and author* forced out
lease expiry, then forced out surface-authored prose — each noticed by a single
world, but argued from a rule the whole protocol already carried.

## The third door, and why it is dangerous

There is a third door, and pretending otherwise would make this document a
description of a process nobody followed. **The operator can rule a change in.**
Closing 1.0-rc1's register used it five times: `totals` on the attention queue,
restatable `kind`, `direction` on questions, `policies` on irreversible rows,
and the precision that an `action` is not always the reader's (spec §22 lists
them with their filing worlds).

This is the door that ends specifications. Every proposal in *What gets
rejected* below was somebody's real need, argued in good faith, and a door
labelled *the operator was convinced* admits all of them. It is written down
here rather than left implicit because an undocumented exception is how a bar
becomes decorative: readers stop checking proposals against the rule and start
checking them against the last thing that got in.

What kept it from being an escape hatch, and what a future proposal has to
match — all four, not a majority:

1. **Additive under §4.2.** No existing client breaks and a surface that
   implements none of them still conforms. If it needs a revision bump, the
   two-world bar is not optional.
2. **At most a field on an existing envelope.** Four of the five are exactly
   that; the fifth — the `action` precision — added no field at all. None
   added a verb, a record type or a concept. A proposal that needs one of
   those is asking for the front door.
3. **Already computed, and thrown away — or nothing at all.** Each of the four
   that added a field hands a client a value the surface held at the moment it
   answered. The fifth adds no value and no field: it is this condition's null
   case, and strictly safer than the others, because a precision that hands a
   client nothing cannot make a surface compute something new. Nothing asks
   the surface to interpret, evaluate, schedule, or act — the four standing
   refusals below are what the operator cannot rule away, because they are the
   design.
4. **An expensive workaround, demonstrated.** Not "we would prefer this":
   round trips measured, or provenance destroyed, or a human left less briefed
   than the machine for an act that cannot be undone.

And one honest caveat that no rule can supply: a single operator ruling on a
corpus of five worlds they also own is not the same evidence as two independent
adopters. The five changes are enumerated in §22 precisely so that an adopter
who thinks one of them was wrong knows where to push.

## The four questions

Ask them in order. Most proposals stop at the second.

1. **Would a different world need this word?** `git` failed this and left the
   spec; `depends_on` passed it and stayed.
2. **Can it ride an existing envelope?** If yes, it is yours — extend and move
   on. A closed enum that two worlds want to fill differently is a bug in the
   spec, not in your world.
3. **Does an existing invariant demand it?** Invariants are load-bearing;
   consistency with them is a protocol argument even when only one world
   noticed the inconsistency.
4. **Would omitting it make clients unportable?** If every deployment must
   invent the same missing capability, it is protocol.

## What gets rejected, reliably

- **Domain records.** Customers, characters, containers, sources. These are
  vocabulary — `links` plus the knowledge plane carry them. A protocol that
  grows a customer table has lost the plot.
- **Anything with a clock.** Due dates, SLAs, recurrence, expiry, scheduled
  release. Clocks live in clients; calendars enter as triggers; periodic work
  is recurring *creation*. This has survived certificates, embargoes, shipping
  dates, and maintenance windows.
- **Anything that evaluates.** Condition languages for policies, capability
  matching in the chooser, computed urgency. The surface interprets nothing:
  agents interpret, pipelines enforce, the worklog audits.
- **Anything that makes the surface act.** Auto-release, auto-escalation,
  notifications, timers. Recovery and reaction are client acts.
- **More hierarchy.** Depth is capped at two on purpose. Scale is answered with
  dependencies and project boundaries, not nesting.
- **A reference operator UI.** Standing refusal: a shared shell would become
  the de facto "OWP interface" and the protocol would quietly become one
  client's API. Discovery (§9) delivers the portability a shell promised.

## How to propose

1. **Build the thing your world needs** inside the envelopes, and ship it. If
   it works, you have vocabulary, not a proposal.
2. **If it cannot be expressed**, write the strain down: the narrowest
   statement of what is unexpressible, what you did instead, and why the
   workaround is wrong. A failing test that documents current behaviour is the
   strongest form.
3. **Name the second world.** Which other deployment hits this, and how do you
   know? If you cannot name one, say so — an honest single-world finding is
   filed and waits for its second, which is what happened to R-1 (research
   filed it; publish confirmed it two passes later; only then did it land).
4. **Propose the smallest shape**, preferring an envelope extension to a new
   field, a new field to a new verb, and a new verb to a new record type. 1.0
   added exactly one concept and zero record types.

## Graduating an experimental feature

A section marked `[experimental]` may change or vanish in any revision, and a
surface must declare whether it implements one. To graduate:

- two independent implementations,
- sustained real use (not just tests) — duration is the usual blocker,
- and no open ambiguity in its routing or authority.

§12.6 (upstream questions) sits here now: three implementations exercise it,
but no deployment has run it across months.

## Registering a name

Registered names (`git`, `sources`, `record-only`, `unblocks-others`, …) have
stable shapes per §4. To register one, show it in use in **two** deployments
with the same shape. Until then it is a local name, and local names are a
first-class outcome — two deployments may use the same word differently and
simply not interoperate on it, which is the honest consequence of vocabulary
being local.

## Revisions

Additive changes ship without a revision bump and are announced through
`surface.describe().features`. Breaking changes (§4.3) require a major
revision, and a renamed field ships additively with the old name deprecated for
at least one revision — as `session` → `actor` did in 1.0.
