# RC3 external standards alignment

Research refresh: **2026-08-21**.

RC3 intentionally composes with current external standards instead of copying
their responsibilities into OWP:

| Standard | Current version/context used | OWP relationship |
|---|---|---|
| A2A | 1.0.0 | Task transport, async lifecycle, artifacts, typed extension metadata. A2A task ids remain server-generated. |
| SLSA | 1.2 | Optional source/build provenance and verification evidence. OWP does not assign SLSA levels. |
| in-toto Attestation | v1.2 framework | Preferred validator/test attestation envelope; exact Git commit/tree is the subject. |
| x402 | Protocol v2 | Optional payment rail; bind payment extension data to the OWP execution commitment. |
| AP2 | v0.2 public specification | Optional payment authority/mandate evidence; keep its deterministic role validation intact. |
| ERC-8004 | ERC-8004 | Optional identity/reputation/validation registry evidence; never a substitute for current Attempt validation. |

Git is the primary concrete source-identity substrate used by RC3. RC3 supports
repositories whose object format is SHA-1 or SHA-256 and forbids abbreviated
object ids in normative source/result commitments.


Project-specific profile/schema identifiers in the unpublished RC3 candidate use
`https://openworkprotocol.org/` as their namespace. External standards remain
owned and versioned by their respective projects.

For the security feedback that influenced the exact-base work, see
`../ACKNOWLEDGMENTS.md`.
