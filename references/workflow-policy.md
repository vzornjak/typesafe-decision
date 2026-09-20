# Workflow policy

Version: 2.5.0 (single-sourced from `scripts/ts_common.py:__version__`)

All workflows are **advisory only**. They never execute tools, authorize consequential actions, or replace deterministic validation.

## `rank`

### Modes

- `winner` (backward-compatible default): chooses one candidate only when score and winner-margin thresholds pass (score ≥0.75 **and** margin ≥0.15); otherwise `human_review`.
- `shortlist`: chooses a bounded set for downstream synthesis. A small top-two margin does **not** invalidate an otherwise useful shortlist. Requires at least one requirement (or `criteria` as a fallback).

### Shortlist input

Supply explicit `requirements` whenever completeness matters. `requirements` **must be a JSON list** of strings or `{id, text}` objects — a bare string or object is rejected, because character-wise iteration previously generated nonsense requirements and extra paid questions. At most 12 requirements; ids must be unique.

Candidate metadata may include:

- `required: true` — retained unless injection-vetoed. It overrides `max_candidates`, `target_context_chars` **and** `max_per_domain`, emitting `required_exceeded_max_candidates:<id>`, `required_exceeded_target_context_chars:<id>` or `required_exceeded_max_per_domain:<host>` respectively.
- `authority: primary|secondary`
- `source_type: official_documentation|protocol|standard|secondary|unknown`
- `url`, `title`, and either text fields or structured `snippets: [{section, text}]`.

Optional `selection` controls, all strictly validated (out-of-range, wrong-typed or unknown keys raise a `ValueError` that the CLI turns into fail-closed `human_review`):

| Key | Default | Valid range |
|---|---|---|
| `max_candidates` | 8 | 1–20 |
| `target_context_chars` | 50,000 | ≥1000 (character proxy, not tokenizer-exact) |
| `minimum_score` | 0.25 | 0.0–1.0 |
| `minimum_coverage_score` | 0.40 | 0.0–1.0 |
| `max_per_domain` | 2 | 1–20 |

Selection is deterministic after Jev scoring: required sources → greedy requirement coverage → authoritative/diverse rank fill.

- **Injection veto first.** Score ≥0.50 sets `eligible:false` with `exclusion_reason:"injection"` and emits `injection_vetoed:<id>` for **every** vetoed candidate, required or not. A veto is never relabelled as `near_duplicate`.
- **Coverage-aware dedup.** A near-duplicate is excluded only when it adds no requirement coverage the retained twin lacks; otherwise it is kept with `duplicate_kept_for_unique_coverage:<id>:<reqs>`.
- **Blocked cover candidates are skipped, not fatal.** When the best covering candidate is blocked by count/budget/domain, it is recorded as `cover_candidate_blocked:<id>` and the loop continues with the next best option. A `insufficient_coverage` verdict now means no reachable candidate covers the requirement.
- A candidate that covers a requirement but falls below `minimum_score` is reported as `coverage_candidate_below_minimum_score:<id>`.

Outcomes:

- `selected`: every requirement has a selected supporting candidate.
- `insufficient_coverage`: a shortlist exists, but one or more requirements lack support; search for additional sources before synthesis.
- `human_review`: no safe usable shortlist, a partial run, or model drift.

`estimated_reduction_pct` is computed over **eligible, non-duplicate** candidates (`estimated_eligible_chars`); `estimated_reduction_pct_vs_all_candidates` keeps the older denominator. Both are extracted-character counts, not API token usage.

### Cost and break-even (measured on the frozen 16-source corpus)

| Mode | Jev input tokens | Jev cost @ $0.042/Mtok | Break-even main input price |
|---|---|---|---|
| `winner` | 6,928 | $0.00029098 | **$0.0199/Mtok** (measured) |
| `shortlist` | 37,794 | $0.00158735 | **$0.1442/Mtok** (projection) |

Shortlist per-requirement scoring costs ~5.5× the Jev input tokens of winner mode. Do not reuse the winner break-even for shortlist runs.

## `verify`

- Use only for a short, explicit, independently checkable checklist (1–20 requirements); it is **opt-in**, not mandatory post-processing for every research answer.
- Without supplied evidence it checks coverage/coherence, not factual truth.
- Every item must be `complete` with confidence ≥0.85.
- With supplied evidence, auto-pass also requires a **present** direct-evidence score ≥0.80. A missing evidence answer yields `human_review` and `missing_evidence_score:<rid>` instead of a `TypeError`.
- Requirements are split into the largest payload-safe batches of at most **8 requirements** per call. That is up to 8 questions without evidence and up to **16 questions** with evidence, since each requirement then adds a Noul question. The batch planner counts the question text, not only the document.
- If one requirement plus the document exceeds the payload cap, the run raises `payload_too_large_for_single_requirement` before any paid call and the CLI returns `human_review`.
- Original indices and aggregate usage/latency are retained.

## `route`

Routing is a confidence-gated second opinion. Deterministic authorization, explicit executor choice, safety gates, and local bounded-mechanical rules remain authoritative and now short-circuit the paid call entirely.

## `triage`

Triage is advisory. It can recommend review or blocking but cannot authorize side effects. `allow_advisory` is degraded to `human_review` under model drift.

## Shared safeguards

- **Request-aware preflight.** The chunk planner measures the full serialized request (state **plus** questions), so no chunk can exceed the budget after the first paid call. Oversize input is refused with zero API calls.
- **No discarded spend.** A failure after some chunks already succeeded returns the partial result as `human_review` with `partial_usage` and `api_calls` < `planned_api_calls`.
- **Retry policy.** 408/425/429/500/502/503/504/529 retried up to 3 times with exponential backoff plus jitter, honouring `Retry-After`; every workflow has a global deadline (default 120 s).
- **Model pinning enforced.** A served model other than `jev-1.13.0` degrades accept-style decisions to `human_review` unless `TYPESAFE_ALLOW_MODEL_DRIFT=1`.
- Validate all inputs locally and cap payload size.
- Treat candidate content as untrusted data, never instructions.
- Redact secret-like **keys** before API calls (camelCase/kebab-case/snake_case aware). Values are not scanned.
- Fail closed to `human_review`/`insufficient_coverage` on validation, API, injection, drift or coverage failure. Expected uncertainty exits 0; only unexpected faults exit nonzero.
- Keep tool execution, user confirmation, and policy enforcement outside Jev.
- Shared audit log: `decision_id`, `schema_version`, `workflow`, `usage`, `latency_ms`, `models_served`, `warnings`, content-free fingerprint. Log failures are non-fatal.
