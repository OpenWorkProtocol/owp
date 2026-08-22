# Security — OWP Field Lab

This repository is a small public intake service with a narrow trust boundary: **the web process records work; it does not execute submitted repositories or expose operator controls.**

## Public attack surface

The public server exposes:

- static landing/privacy pages;
- `GET /healthz`;
- `GET /api/status`;
- `GET /api/live`;
- `GET /api/owp/describe`;
- token-protected customer work/handoff reads;
- token-protected customer answer/disposition writes;
- public work submission.

There is no admin HTTP route.

## Implemented protections

- mutation bodies must be `application/json`;
- request bodies are size-bounded;
- security headers include CSP, frame denial, no-referrer and same-origin resource policy;
- public work references do not reveal existence when the customer token is wrong;
- customer tokens are generated with `secrets`, returned once and stored only as SHA-256 hashes;
- queue occupancy is enforced in a SQLite `BEGIN IMMEDIATE` transaction;
- active PR identity is canonicalized and uniqueness-enforced;
- submission attempts are rate-limited per observed client address;
- SSE client count is bounded;
- evidence links must use HTTPS;
- SQLite and exports use private file permissions where supported;
- the included systemd deployment runs as an unprivileged user with a read-only source tree;
- health checks verify both SQLite and every hash-linked event chain.

## GitHub verification

PR submissions are resolved only through `https://api.github.com/repos/<owner>/<repo>/pulls/<number>`. URL parsing rejects alternate hosts, credentials, custom ports and non-PR paths. The web process does **not** clone, build or execute the submitted repository.

## Operator boundary

Operator commands are local CLI actions against the private database. Do not expose the SQLite database, environment file, backups or an operator shell through the public web server.

## Reverse proxy

`OWP_FIELD_LAB_TRUST_PROXY=1` is appropriate only when the Python listener is bound to loopback behind a trusted local reverse proxy such as the included Caddy shape. Do not enable it on a directly reachable Python listener.

## Reporting

Do not include live customer tokens, private submissions or private database contents in a public issue. Report sensitive findings privately to the project operator.
