# Commerce bindings: x402 v2 and AP2 v0.2 (informative)

Checked 2026-08-21.

References:

- x402 Protocol Version 2:
  https://github.com/x402-foundation/x402/blob/main/specs/x402-specification-v2.md
- Agent Payments Protocol (AP2) v0.2:
  https://github.com/google-agentic-commerce/AP2/blob/main/docs/ap2/specification.md

## x402 v2

x402 v2 separates transport, payment schemes, and core payment types and
provides extension objects on core payment structures. When x402 funds an OWP
software Attempt, an integration should bind the economic event to the
`execution_commitment_digest` in an extension rather than inventing a second
work identity.

Payment success proves the payment event. It does not prove the provider used
the expected Git base or that the returned result was independently tested.

## AP2 v0.2

AP2 secures agent-performed payment transactions through role-specific,
deterministically verified mandates and receipts. OWP does not redefine AP2's
roles, mandates, signature rules, or deterministic verification duties.

When a containing commerce protocol gives a safe extension point, an AP2-backed
OWP purchase should reference the same `execution_commitment_digest` that the
provider/orchestrator will execute. This keeps customer authority/payment and
software-delivery validity related but non-circular and independently provable.
