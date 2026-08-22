# Annex A — the HTTP+JSON binding (normative, 1.0-rc3)

Companion to `owp-1.0-rc3.md` §17. This annex is **normative for deployments
that choose HTTP** and defines their interoperability target. It is not
mandated: the protocol's delivery is the deployment's (§17), and a surface may
carry the verbs any way it likes. A surface that says "OWP over HTTP" means
*this*.

## A.1 Routes

```
POST /v0/<verb>       body = verb arguments (JSON object; {} when none)
GET  /v0/health       liveness; {ok, protocol, auth}
```

`/v0` names the first HTTP binding generation, not the OWP document revision.
Revision selection is the A.5 header, so all compatible 1.x RCs use the same
route family.

- `<verb>` is the §10 name verbatim: `work.next`, `event.append`,
  `surface.describe`, `session.view`, …
- **All verbs POST**, including reads: reads take arguments (cursors, limits,
  scopes), and uniformity keeps generated clients trivial.
- Every verb request MUST carry `Content-Type: application/json` (an optional
  charset parameter is allowed). A surface MUST reject any other or absent
  media type with `VALIDATION`; accepting form-compatible types lets an
  unrelated browser origin drive a loopback surface with ambient authority.
- A surface MUST reject a verb body larger than 1 MiB with `VALIDATION`, before
  parsing or dispatch. Deployments MAY impose a smaller documented limit.
- A path that is verb-shaped but names a verb the surface does not implement
  MUST answer `UNKNOWN_VERB` — **not** a transport 404. A binding that
  conflates "this route did not parse" with "this surface lacks that verb"
  makes discovery unusable, and clients cannot tell a missing feature from a
  typo'd URL.
- Surfaces MAY serve other paths (an operator UI at `/`, static assets); those
  are outside this annex.

## A.2 Actor identity

| Header | Meaning |
|---|---|
| `x-owp-session` | a registered session id — required for session-bound verbs |
| `x-owp-client` | a client identity (operator UI, cron, watcher) for creator/operator actors |
| `authorization: Bearer <token>` | credential; `x-owp-token` is an accepted alternative |

A request MAY carry both a session and a client identity; the session wins for
attribution (§7.4). Every verb call refreshes the session's `last_seen`, so
heartbeats piggyback.

## A.3 Responses

```
200  { "ok": true,  "result": … }
4xx  { "ok": false, "error": { "code": "…", "message": "…", "data": { } } }
```

`result` MAY be `null` — notably `work.next` with nothing eligible, which is a
normal answer and MUST NOT be an error.

## A.4 Error mapping

The §16 codes are protocol; their transport status is this annex's:

| Code | HTTP |
|---|---|
| `VALIDATION` | 400 |
| `UNSUPPORTED_VERSION` | 400, with `data.supported` listing revisions |
| `UNAUTHENTICATED` | 401 |
| `SESSION_REQUIRED` | 401 |
| `FORBIDDEN` | 403 |
| `NOT_FOUND` | 404 |
| `UNKNOWN_VERB` | 404 |
| `CONFLICT` | 409 |
| `STATE` | 422 |
| any other | 400, or 500 for an internal fault |

Clients MUST branch on `error.code`, never on the status alone.

**A failure to reach the surface has no code in this table and no status at
all** (§16). A connection refused, a DNS failure, or a timeout is not an answer,
and a client MUST NOT map it onto one of the codes above — `UNKNOWN_VERB` for a
404 from a load balancer, or `VALIDATION` for a 400 from a proxy, turns a
retryable outage into a terminal error. A proxying operator client that must
report the failure in the §16 envelope SHOULD use a code outside the set and
treat it as retryable; the reference deployments use `SURFACE_UNREACHABLE`, and
a 502 or 504 from an intermediary belongs in the same class.

## A.5 Revision selection

A client MAY pin a revision with `x-owp-protocol: 1.0-rc3`. A surface that does
not implement the pinned revision MUST answer `UNSUPPORTED_VERSION` with
`data.supported`. Absent the header, the surface answers in its default
revision, which `surface.describe` reports. Discovery (§9) is the intended
handshake: call `surface.describe` first, then pin.

## A.6 Replay-safe mutation retries

A client MAY send `Idempotency-Key` on any verb request. The value MUST be 1–128
ASCII characters from `A-Z`, `a-z`, `0-9`, `.`, `_`, `:`, or `-`.

For a given authenticated actor and key, a surface MUST execute the first
request at most once and MUST replay its complete status and response for an
identical retry. The mutation and replay record MUST commit atomically. Reusing
the key with a different verb or arguments MUST return `VALIDATION` without
dispatching the request. Equality is over the parsed verb and canonical JSON
arguments, not insignificant object-key order or whitespace. A surface MUST
retain replay records for at least 24 hours and SHOULD document longer
retention; a client MUST NOT reuse a key within that interval.

A client that retries a mutation after connection failure or timeout MUST send
the same key. Without a key, it MUST reconcile with a read before resubmitting.
Clients SHOULD use bounded exponential backoff with jitter and MUST obey a
local operation deadline or cancellation signal. The protocol does not set one
universal request timeout: operators SHOULD configure one appropriate to the
deployment, and proxies MUST eventually abort an unresponsive upstream rather
than hold connections without bound.

## A.7 Authentication, browser boundary, and grants

Authentication is a binding concern (§18); this annex describes the reference
arrangement, which a deployment MAY replace wholesale:

- **Open mode** — no credentials configured. Authority is inferred: session
  actors are agent-class, bare clients operator-class. Appropriate only where
  the transport itself is the trust boundary: one omitted header buys operator
  authority, so the reference surface binds **loopback only** in open mode and
  exposing it on a routable interface is an explicit opt-out. Loopback alone
  is not a browser security boundary: implementations MUST also enforce A.1's
  JSON-only request rule and SHOULD reject unexpected `Origin` headers.
- **Token mode** — an operator token, an agent token, and any number of **grant
  tokens**, each carrying `{verbs, project?, states?, trigger_prefix?}` (§18).
  An unrecognized credential is `UNAUTHENTICATED`; a recognized credential
  acting outside its grant is `FORBIDDEN`, and the denial is audited.

Bearer credentials are secrets. A token-mode deployment exposed beyond
loopback MUST use authenticated TLS (directly or at a trusted reverse proxy),
MUST NOT place tokens in URLs or logs, and SHOULD issue separate high-entropy
tokens per authority/grant so one can be revoked without rotating every actor.

`surface.describe` MUST report the caller's own authority and grants, so a
client never has to learn its permissions by being refused.

## A.8 Deprecations carried in 1.0

Per §4.5, event payloads carry both `actor` (normative) and `session` (the
deprecated alias). Clients SHOULD read `actor`; surfaces SHOULD emit both until
a revision removes the alias.

## A.9 Conformance

A surface claiming this annex passes the conformance kit
(`owp-code/conformance/run.ts`) pointed at its base URL, which exercises these
routes, codes, and headers over the wire.
