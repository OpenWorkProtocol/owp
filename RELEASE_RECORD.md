# Open Work Protocol 1.0-rc2 release record

Publication date: **2026-08-08**
Canonical release: **`OpenWorkProtocol/owp@v1.0-rc2`**

## Published repositories

| Repository | Release | License |
|---|---|---|
| `OpenWorkProtocol/owp` | `v1.0-rc2` | MIT |
| `OpenWorkProtocol/owp-code` | `v0.1.0` | MIT |
| `OpenWorkProtocol/owp-desk` | `v0.1.0` | MIT |
| `OpenWorkProtocol/owp-ops` | `v0.1.0` | MIT |
| `OpenWorkProtocol/owp-publish` | `v0.1.0` | MIT |
| `OpenWorkProtocol/owp-research` | `v0.1.0` | MIT |

The repositories were validated before public visibility was enabled. Hosted
continuous integration subsequently passed on each release commit and tag.
Fresh-clone validation reproduced the requirement inventory and passed all
documented tests, schema checks, and dependency audits.

## Repository controls

Each repository uses a protected `main` branch with strict required status
checks, linear history, administrator enforcement, and force-push and deletion
protection. Workflow actions require full commit identifiers. Secret scanning,
push protection, dependency alerts and security updates, and private
vulnerability reporting are enabled.

## Website publication

The release website is deployed from its private Forgejo source repository to
Cloudflare Pages.

- Canonical URL: `https://openworkprotocol.io/`
- Pages endpoint: `https://owpio-web-ed49c385.pages.dev/`
- Release evidence: `https://openworkprotocol.io/release/`

The canonical URL and release routes returned HTTP 200 with RC2 content during
final verification.

## Claim boundary

All runnable examples share the released reference implementation. The release
therefore establishes reference conformance and domain portability, not
independent implementation interoperability or production certification.

Project contact: `info@openworkprotocol.io`
