# OWP Field Lab privacy and data use

The OWP Field Lab is a no-charge public workflow experiment operated by __OWP_OPERATOR_NAME__.

## Collected per submission

All submissions include:

- requested outcome;
- exact USD value signal;
- provider/customer lifecycle decisions;
- evidence links;
- a one-way SHA-256 hash of the private customer claim token.

GitHub PR submissions also include the public PR URL and GitHub-returned metadata, including the head SHA and size snapshot.

Idea submissions include the idea title and any optional HTTPS context URL supplied by the customer.

The field lab does not request or collect card, wallet, bank or other payment credentials.

## Public data

The public service exposes aggregate queue capacity and generic service/protocol information. It does not publish individual queue entries, requested outcomes, value signals or private work threads.

## How data may be used

The intake form requires explicit acknowledgement that submitted source metadata, requested outcomes, value signals and lifecycle outcomes may be retained and analyzed to evaluate and improve the field lab, OWP workflows, and __OWP_OPERATOR_NAME__'s operating process.

A private JSONL export intentionally pairs the request with the value signal and lifecycle result for analysis. A lower-detail CSV omits the requested outcome. The service does not automatically publish collected submissions as a public dataset.

## Customer tracking token

The browser receives a high-entropy claim token once. The service stores only its SHA-256 hash. The token is kept in the tracking URL fragment so browsers do not send it in ordinary HTTP request paths or referrers.

Anyone with the full tracking link can act as the customer for that work item. Treat it like a password.

## Abuse protection

The web process keeps a short-lived in-memory client address key to throttle submission attempts. This limiter state is not persisted in the work database or included in exports. Behind the included trusted local reverse proxy, the service can use the forwarded client address for this limiter.

## Handoff exports

Customer and operator handoff exports contain the portable work record but never the customer claim token or stored token hash.

## Publication

Before publishing any collected field data, the operator should review the specific release for aggregation, redaction or anonymization appropriate to that release.
