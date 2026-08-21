# Project URLs and public surfaces

Current public surface map for the RC3 development candidate:

| Surface | Canonical URL | Role | Claim boundary |
|---|---|---|---|
| Main website / docs entry point | https://openworkprotocol.org/ | Explain the protocol, security model, status, and implementation paths | May describe RC3 as a development candidate; must not claim independent RC3 interoperability before the release gates close |
| Try OWP Field Lab | https://try.openworkprotocol.org/ | Live workflow field experiment | Not full OWP 1.0 conformance, not a marketplace/payment system, and not full Software Work Integrity validation |
| Canonical spec repository | https://github.com/OpenWorkProtocol/owp | Normative candidate text, schemas, conformance inventory, release evidence, and non-normative Try template | Source of truth for the current spec candidate; template code does not become normative merely by living here |

## URI namespace

Unpublished RC3 profile/schema/attestation identifiers use the
`https://openworkprotocol.org/` namespace. This corrects the candidate's earlier
`.io` draft identifiers before RC3 publication.

`RELEASE_RECORD.md` intentionally retains the `.io` URLs that were recorded for
the historical RC2 publication. Those URLs are historical evidence, not the
current project namespace.

## Product separation

Do not redirect the root website to the Field Lab merely because the Field Lab
is live. The root explains what OWP promises; the Try site tests those ideas in
a deliberately narrower deployment. A later root-domain decision is a product
and governance decision, not a deployment side effect.

## Self-hosted Try OWP

The repo-local `templates/try-owp/` field lab is a distributable example, not a
fourth normative public surface. Forks may use any hostname. They must not imply
that the Open Work Protocol project operates or certifies the fork.
