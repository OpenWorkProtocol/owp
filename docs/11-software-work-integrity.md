# Software work integrity: the exact-base rule

The optional Software Work Integrity Profile exists for one failure mode that a
normal task tracker cannot solve: a worker can report one Git base, run tests on
another revision, modify the result afterward, and return a SHA and `PASS` status that
are not bound to the source actually tested.

OWP RC3 addresses that gap without turning the core surface into a Git server.

## The five anchors

1. **Definition of Done agreement.** Customer, provider, orchestrator, and an
   independent OWP validator all accept the same contract digest before work.
2. **Attempt source commitment.** Every Attempt fixes the exact repository,
   Git object format, base commit, and base tree before execution.
3. **Untrusted delivery claim.** The provider may report result commit/tree and
   evidence, but those remain claims.
4. **Independent reconstruction.** A separate validator obtains source,
   confirms base/tree/ancestry/diff, checks scope, creates a clean checkout of
   the exact result, and runs the effective Definition of Done there.
5. **Attested handoff.** Revisions and provider changes start from the previous
   validator-attested result—not from a provider's branch tip or summary.

Flow summary:

```text
agreed outcome + exact Attempt input
             -> provider execution
             -> provider claim
             -> independent reconstruction/tests
             -> validator-attested exact result
             -> customer disposition
             -> next Attempt inherits only validated state
```

A payment receipt, Git signature, CI badge, event-ledger entry, or reputation
record can support the evidence graph. None is allowed to stand in for the
independent exact-result check.

See `spec/annex-software-work-integrity-1.0-rc3.md` for normative requirements.
