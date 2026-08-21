# Try OWP — self-hostable field-lab template

This directory is a **non-normative deployment template** for running your own
OWP-shaped field experiment. It is derived from the tested public Field Lab but
is deliberately separate from the protocol's conformance claims.

The generated service supports both **open GitHub pull requests** and
**greenfield build ideas**, a bounded private FIFO queue, explicit ACCEPT/PASS,
numbered Attempts, durable questions and customer answers, delivery evidence, a
separately named validation record, APPROVE/STEER/REJECT, hash-linked history,
and portable handoff exports.

**No money is collected, authorized, escrowed, promised, or owed.**

The reference contract includes a **greenfield build idea** path as well as PR intake, a hard ceiling of **20 active work items**, explicit customer **APPROVE / STEER / REJECT**, and a **customer-downloadable token-free handoff JSON** export. It is **not a claim of full Open Work Protocol 1.0 conformance**.

## Recommended fast path

From the parent OWP repository, instantiate rather than editing this template in
place:

```bash
./scripts/new-try-owp.sh ../my-try-owp \
  --operator "Acme Agent Lab" \
  --hostname try.example.com \
  --provider-id provider:acme
cd ../my-try-owp
./scripts/smoke.sh
python3 -m owp_field_lab.server --host 127.0.0.1 --port 8080
```

The bootstrapper renders deployment-specific placeholders, refuses a pre-existing
destination, and runs the complete generated-instance smoke suite by default.

The current instantiated template suite contains **58 tests**.

## Security defaults

- loopback application listener by default;
- no public admin HTTP route;
- tracking links are bearer credentials;
- SQLite state/backups stay private;
- intake never clones/builds/executes submitted repositories;
- named validation is lifecycle evidence, not automatically independent Software
  Work Integrity validation; and
- exact-result validation belongs in a separate disposable validator environment.

The generated deployment includes Caddy and Cloudflare Tunnel examples. Current
Cloudflare guidance recommends remotely-managed tunnels for most deployments;
the local config example is included mainly for testing/advanced use.

Read `SECURITY.md`, `PRIVACY.md`, `docs/DEPLOY.md`, and `docs/OPERATOR.md` in the
generated copy before making it routable.

## OWP relationship

This template is a product/reference surface, **not a normative OWP profile**.
Running it does not prove independent interoperability, validator independence,
or full OWP 1.0 conformance.

Security work in the surrounding RC3 candidate was influenced by
[grogugo](https://github.com/grogugo); see the parent repository
`ACKNOWLEDGMENTS.md` for the exact credit boundary.

The template does not, by itself, provide independent **Software Work Integrity validation**.
