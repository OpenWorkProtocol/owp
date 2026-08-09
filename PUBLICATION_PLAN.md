# OWP 1.0-rc2 public publication plan and execution record

Status: **published and publicly verified on 2026-08-08 (America/New_York).**

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

## Execution record

- All six repositories were pushed privately, validated, and then made public
  in the order above. GitHub recognizes each repository's MIT license.
- Fresh-clone validation reproduced all 145 normative entries and passed all
  252 tests, the reference implementation type/schema checks, and dependency
  audits with no known vulnerabilities.
- GitHub-hosted CI passed on every release commit and again on every tag. The
  canonical release is `owp@v1.0-rc2`; each runnable repository is released at
  `v0.1.0` and explicitly states the shared-implementation limitation.
- Main-branch protection requires strict CI and linear history, applies to
  administrators, and prevents force pushes and deletion. Actions must use
  full commit SHAs. Secret scanning, push protection, Dependabot alerts and
  security updates, and private vulnerability reporting are enabled.
- `https://owpio-web-ed49c385.pages.dev/` and
  `https://openworkprotocol.io/` both serve the RC2 site. The custom domain,
  `/release/`, `/protocol/`, and `/examples/` returned HTTP 200 during final
  verification.

## Stop/rollback rules

- Any failed private CI or clean-clone check stops before visibility changes.
- Do not force-push after publication. Correct a public defect with an explicit
  follow-up commit and withdraw the affected GitHub release if its claim is no
  longer supportable.
- A website failure is rolled back by reverting the Forgejo deployment commit;
  repository publication does not depend on the website deployment succeeding.
- If the custom domain is moved or recreated, its Cloudflare Pages target is
  `owpio-web-ed49c385.pages.dev`. DNS and email routing remain deployment-owner
  controls and are not asserted by the protocol conformance evidence.
