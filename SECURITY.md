# Security policy

The supported protocol target is the current release candidate named in
`README.md`. Superseded drafts and development snapshots receive no security
updates.

Do not place credentials, personal data, exploit details, or live deployment
addresses in a public issue. Use GitHub private vulnerability reporting when it
is enabled for the affected OpenWorkProtocol repository. If that channel is not
available, open a minimal issue asking a maintainer for a private reporting
channel and disclose no vulnerability details there.

Include the affected repository and revision, threat model, reproduction,
impact, and the smallest safe test case. Maintainers will acknowledge receipt,
coordinate a fix and disclosure window, and state which releases are affected.
No response-time SLA is promised by this volunteer release candidate.

The reference surface is not a security boundary by itself. Open mode is for
loopback use. Routable deployments require authentication, TLS, protected
operator clients, scoped credentials, request limits, and secret handling as
specified by Annex A and the repository deployment guide.

## Software Work Integrity Profile threat boundary

A provider or execution worker is untrusted with respect to its own delivery
claims. For profile-covered software work, do not validate from the provider's
working directory and do not accept a provider-supplied `tests: PASS`, branch
tip, PR head, or SHA-shaped string as proof.

The independent validator should run in a disposable sandbox with no ambient
user credentials, obtain source through a validator-controlled path, verify the
Attempt-bound base commit/tree, recompute the result tree and diff, enforce
scope/negative policy, and run deterministic acceptance against the exact
result subject.

Inability to obtain or execute required validation evidence is
`INDETERMINATE`, not `VALID`. Revisions/handoffs must begin from the previous
validator-attested result so an unverified provider branch tip cannot become the
next provider's trusted starting state.


## Try OWP Field Lab boundary

The public Field Lab at `https://try.openworkprotocol.org/` is a separate
experiment. Its intake service must not clone, build, or execute submitted
untrusted repositories in the public web process. A named validation record in
the Field Lab is evidence of lifecycle separation, not automatically evidence
of full Software Work Integrity conformance.

If the Field Lab adopts the RC3 profile, exact-base/result verification and
acceptance commands belong in a validator-controlled disposable environment,
not in the intake server or the provider's workspace. Customer tracking links,
GitHub tokens, Cloudflare tunnel credentials, SQLite state, and backups are
secrets/private deployment state.

## Acknowledgment

The exact-base/untrusted-worker security analysis was influenced by a verification
question raised by [grogugo](https://github.com/grogugo). See
[ACKNOWLEDGMENTS.md](ACKNOWLEDGMENTS.md).


## Self-hosted Try OWP template

`templates/try-owp/` is intentionally deployable, but it is not a safe place to
execute arbitrary submitted repositories. Keep its listener on loopback behind
a trusted TLS proxy/tunnel, keep admin operations on the host CLI, protect the
SQLite database/backups and claim links, and place any future build/test
execution in a separate disposable validator sandbox.

Forks should preserve the distinction between a named validation record and a
full independent Software Work Integrity attestation.
