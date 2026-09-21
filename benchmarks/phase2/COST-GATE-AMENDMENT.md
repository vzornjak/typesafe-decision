# Phase 2 cost-gate supplement — amendment A-001

Status: **approved by user; unscored; must be hash-locked before execution**

This supplement replaces only Section 10(5) of the originally locked `PREREGISTRATION.md` and the corresponding `config/decision-gates.json` cost field. Their original bytes remain frozen in the historical input lock. All non-cost gates and data-exclusion rules remain unchanged.

## Confirmatory question

For the 16 scored tasks, compare the preregistered `C_shortlist_default` arm against `A_no_rank`. Use the observed provider-reported input/output token counts, including all counted Jev requests and MAIN requests, and apply the pre-existing `config/execution.json` public list-price snapshot. Report mean/total task-paired modeled savings in USD and the cost ratio. A positive modeled savings is required; a zero or negative saving fails. Do not use the tuned D arm to rescue C.

## Cost formula

- Jev: `(J_input × 0.042 + J_output × 0) / 1,000,000` USD.
- MAIN: `(M_standard_input × 5.0 + M_cached_read_input × 0.5 + M_output × 25.0) / 1,000,000` USD.
- Cache-creation/write tokens have **no frozen price** in the historical price snapshot. If nonzero, fail closed as `INCONCLUSIVE` pending a prospective price amendment and new untouched holdout. If zero, do not invent a cost.
- MAIN provider-reported `input_tokens` must be interpreted according to its documented cache-token accounting; subtract cached-read tokens from standard input *only if* the provider explicitly says the reported input count includes them. Otherwise treat separate usage buckets as additive, with an explicit accounting note. The calculation implementation locks this interpretation before scoring.
- If any potentially billed attempt has unknown usage, classify the modeled-cost criterion as `INCONCLUSIVE`; never replace unknown with 0 or infer missing telemetry from text length.
- Output text quality, source coverage, and unsupported-claim metrics are independent of this cost calculation.

## Claim boundary

A resulting USD amount is **modeled public API list-price cost**, not actual account debit, OAuth plan charge, or a vendor invoice. Publish raw token counts and the frozen URLs/date of each price. If the OAuth subscription did not meter the request per API token, report its actual incremental charge as unknown rather than conflating it with modeled cost.

## Provenance and rollback

Authorization: user's explicit message on 2026-09-21: “Da, koristi modeliranu cijenu prema javnom cjeniku kao Phase 2 gate.” Root `archi.ai` amendment A-001 governs. This supplement does not rewrite `inputs.lock.json`; its own bytes, code, and price interpretation must be included in a supplementary runner lock before paid scored calls. Reverting the gate requires a prospective approved amendment, not a post-hoc reinterpretation of this holdout.
