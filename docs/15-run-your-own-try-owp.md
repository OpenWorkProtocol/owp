# Run your own Try OWP field lab

The specification repository includes a **non-normative, self-hostable Try OWP
template** at [`templates/try-owp/`](../templates/try-owp/). It is based on the
same Field Lab slice used for the current public experiment: GitHub PR
intake **and greenfield build ideas**, durable Attempts/questions/evidence,
customer disposition, and portable handoff.

The template exists so a curious operator can experience OWP-shaped work without
first implementing the protocol or sending work to the hosted Field Lab.

## Fastest safe path

```bash
git clone https://github.com/OpenWorkProtocol/owp
cd owp
./scripts/new-try-owp.sh ../my-try-owp \
  --operator "Acme Agent Lab" \
  --hostname try.example.com \
  --provider-id provider:acme
cd ../my-try-owp
python3 -m owp_field_lab.server --host 127.0.0.1 --port 8080
```

The bootstrapper refuses an existing destination, renders deployment-specific
operator/hostname/provider values, verifies no template tokens remain, and runs
the generated instance's smoke suite by default.

For local-only evaluation the defaults are enough:

```bash
./scripts/new-try-owp.sh ../my-try-owp
```

Use `--no-test` only when you deliberately want to defer validation.

## What the generated deployment contains

- open GitHub PR verification and snapshotting;
- greenfield build-idea intake that does not invent a repository;
- private FIFO queue with a hard 20-active-work ceiling;
- explicit operator ACCEPT/PASS;
- numbered Attempts and PR-head refresh before an Attempt starts;
- durable questions/options/evidence and customer answers;
- delivery evidence and a separately named validation record;
- customer APPROVE / STEER / REJECT;
- SHA-256 hash-linked event history;
- token-protected private customer tracking;
- token-free portable handoff export;
- backups and integrity verification;
- no remote admin HTTP route; and
- no payment collection.

The embedded source currently passes **58 tests** in the template suite,
including the original Field Lab lifecycle/security cases plus a check that a
custom provider actor is written into durable events.

## What it does **not** prove

Running the template does not make the deployment OWP 1.0 conformant, does not
prove independent interoperability, does not make the operator a trusted
validator, and does not safely execute submitted code.

The public intake service must remain separate from any build/test sandbox.
Software Work Integrity validation belongs in an independently controlled,
disposable validator environment. If required exact-result proof cannot be
obtained safely, the correct profile result is `INDETERMINATE`, not a fabricated
`VALID`.

## Public ingress options

The safe shape is always:

```text
Internet -> trusted HTTPS ingress -> 127.0.0.1:8080 -> Field Lab -> private SQLite
```

The generated copy includes:

- `deploy/Caddyfile.example` for a conventional TLS reverse proxy; and
- `deploy/cloudflared-config.yml.example` for locally-managed Cloudflare Tunnel
  testing/advanced use.

Cloudflare's current documentation recommends **remotely-managed tunnels for
most deployments**. For that path, create a published application mapping your
hostname to `http://127.0.0.1:8080` and keep the tunnel token out of the repo and
shareable logs.

References:

- https://developers.cloudflare.com/tunnel/setup/
- https://developers.cloudflare.com/tunnel/advanced/local-management/configuration-file/

## Secrets and authority

Never publish:

- the SQLite database or backups;
- `GITHUB_TOKEN`;
- Cloudflare tunnel tokens/credential JSON;
- full customer tracking links; or
- private operator exports.

The tracking link is a bearer credential. Anyone with it can act as that
customer for that work item.

## Why this remains a template, not core protocol

OWP defines portable lifecycle/coordination semantics. A specific intake UI,
private queue, value-signal experiment, SQLite database, Caddy config, or
Cloudflare Tunnel is deployment/product behavior. Keeping this directory
non-normative prevents a convenient demo from silently becoming the standard.

The hosted experiment remains at **https://try.openworkprotocol.org/**. The
protocol/docs home remains **https://openworkprotocol.org/**.

## Security inspiration

The surrounding RC3 Software Work Integrity work was influenced by
[grogugo](https://github.com/grogugo), whose expected-base/untrusted-worker
question helped clarify OWP's distinction between provider claims and independent
verification. See [`ACKNOWLEDGMENTS.md`](../ACKNOWLEDGMENTS.md).
