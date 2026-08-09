<p align="center">
  <img src="assets/brand/owp-icon-black.svg" width="112" alt="Open Work Protocol">
</p>

# Open Work Protocol

Open Work Protocol (OWP) defines a durable coordination contract between agent
fleets and human operators. It standardizes work lifecycle, assignment,
questions, decisions, completion, recovery, authority, and bounded operator
projections while leaving domain vocabulary and user interfaces to each
deployment.

## Release status

The current release is **Open Work Protocol 1.0-rc2**, a public release
candidate.

- Normative requirements inventoried: **145**
- Authenticated wire-conformance obligations: **50/50**
- Automated tests across the reference implementation and examples: **252/252**
- Known Blocker or High-severity release findings: **0**

The five runnable repositories share one reference implementation. The release
establishes reference conformance and portability across the represented
domains. Independent implementation interoperability has not yet been
demonstrated.

## Normative documents

- [Core specification](spec/owp-1.0-rc2.md)
- [HTTP and JSON binding](spec/annex-http-1.0-rc2.md)
- [Normative requirement inventory](REQUIREMENTS.json)
- [Conformance matrix](CONFORMANCE_MATRIX.md)

The core specification is binding-independent. Annex A is normative for
implementations that select the HTTP and JSON binding.

## Release documentation

- [Release readiness assessment](RELEASE_READINESS.md)
- [Release record](RELEASE_RECORD.md)
- [Revision history](CHANGELOG.md)
- [Migration guide](docs/10-impact-of-1.0.md)
- [Protocol change policy](docs/09-changing-the-protocol.md)
- [Implementation guide](docs/06-programming-with-owp.md)
- [Example coverage](docs/08-the-five-worlds.md)

## Implementations and examples

| Repository | Purpose | Tests |
|---|---|---:|
| [`owp-code`](https://github.com/OpenWorkProtocol/owp-code) | Reference surface, schema, CLI, operator console, and conformance suite | 94 |
| [`owp-desk`](https://github.com/OpenWorkProtocol/owp-desk) | Freight back-office example | 24 |
| [`owp-ops`](https://github.com/OpenWorkProtocol/owp-ops) | Infrastructure operations example and reference watcher | 43 |
| [`owp-publish`](https://github.com/OpenWorkProtocol/owp-publish) | Editorial workflow example | 56 |
| [`owp-research`](https://github.com/OpenWorkProtocol/owp-research) | Research workflow example | 35 |

Each example is independently installable from its repository. Installation,
acceptance, cleanup, and troubleshooting procedures are documented in the
repository's `docs/deploy.md`.

## Protocol boundary

OWP is not an agent runtime, scheduler, workflow language, document store,
retrieval system, development environment, or reference user interface. The
protocol defines shared envelopes and invariants. Deployments define their
domain records, presentation, delivery, scheduling, and automation.

## Conformance

Candidate surfaces can be evaluated with the conformance suite in
[`owp-code`](https://github.com/OpenWorkProtocol/owp-code):

```sh
git clone https://github.com/OpenWorkProtocol/owp-code
cd owp-code
npm ci
npm test
npm run conformance -- http://127.0.0.1:7117 \
  --operator-token "$OWP_OPERATOR_TOKEN" \
  --agent-token "$OWP_AGENT_TOKEN"
```

Conformance results from the shared reference implementation are not evidence
of interoperability between independent implementations.

## Security

Open mode is limited to loopback evaluation. Routable deployments require TLS,
authentication, protected operator clients, scoped credentials, request
limits, and deployment-specific identity lifecycle controls. Vulnerabilities
should be reported according to [SECURITY.md](SECURITY.md).

## Project

- Website: [openworkprotocol.io](https://openworkprotocol.io)
- GitHub organization: [OpenWorkProtocol](https://github.com/OpenWorkProtocol)
- Contact: [info@openworkprotocol.io](mailto:info@openworkprotocol.io)
- License: [MIT](LICENSE)
