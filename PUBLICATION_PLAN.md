# OWP 1.0-rc2 public publication plan

Status: **staged locally; no remote push, visibility change, tag, release, or
website deployment has been executed.**

## Publication set

The GitHub organization already contains six private, empty repositories, so
no repository creation is required:

1. `OpenWorkProtocol/owp` — specification, HTTP annex, requirement inventory,
   conformance matrix, readiness report, governance, and license.
2. `OpenWorkProtocol/owp-code` — reference implementation and conformance kit.
3. `OpenWorkProtocol/owp-desk` — freight example.
4. `OpenWorkProtocol/owp-ops` — infrastructure example.
5. `OpenWorkProtocol/owp-publish` — editorial example.
6. `OpenWorkProtocol/owp-research` — research example.

Each staged repository has one root commit on `main`, an MIT `LICENSE`, public
security and contribution guidance, pinned CI actions, correct cross-repository
references, and no development checkout state.

The website remains in its existing private Forgejo repository because a push
to `main` deploys the static end product to Cloudflare Pages. Its Tailwind
Plus-derived source is described separately in `LICENSE.md`; it is not folded
into the MIT protocol publication set.

## Execution order

1. **Private GitHub push:** push each staged `main` branch while all six
   repositories are still private.
2. **Private verification:** require GitHub Actions to pass, confirm GitHub
   recognizes each MIT license and security policy, and perform authenticated
   fresh clones followed by the documented validation commands.
3. **Repository settings:** set descriptions, `https://openworkprotocol.io`
   homepages (example anchors where applicable), topics, issue/security
   settings, default branch, and branch protection/rulesets.
4. **Public visibility:** make the repositories public in dependency order:
   `owp`, `owp-code`, then the four domain examples.
5. **Tags and releases:** create `v1.0-rc2` on `owp`; create `v0.1.0` on each
   runnable artifact to match its package version. GitHub release notes must
   repeat the RC/non-production/shared-implementation limitations and link the
   readiness report.
6. **Website deployment:** after every GitHub link is public and returns 200,
   push the staged `owpio-web` commit to Forgejo `main`, which runs the pinned
   static build/audit and Cloudflare Pages deployment.
7. **Post-publication verification:** check repository/license/security links,
   release assets and tags, website routes, sitemap/robots, external links,
   clean-clone commands, and the public visibility/metadata APIs.

## Stop/rollback rules

- Any failed private CI or clean-clone check stops before visibility changes.
- Do not force-push after publication. Correct a public defect with an explicit
  follow-up commit and withdraw the affected GitHub release if its claim is no
  longer supportable.
- A website failure is rolled back by reverting the Forgejo deployment commit;
  repository publication does not depend on the website deployment succeeding.
- `openworkprotocol.io` currently has no observable public DNS resolution from
  the release environment. Treat custom-domain activation as a separate DNS
  gate; the Pages deployment alone does not prove the canonical hostname works.
