# TypeSafe decision layer policy v2.5.0

Version is single-sourced from `scripts/ts_common.py:__version__` (2.5.0) and emitted in every output and log row.

## Status

Shadow/advisory only. Jev recommends; the main assistant and deterministic safety policy decide. No Jev result authorizes execution, spending, deletion, disclosure, account changes, or physical actions.

## Executor choice

- `main`: short work, conversation nuance, ≤1–2 routine tool calls, or confirmation needed.
- `sub`: mechanical, bounded, low-risk, glance-verifiable work.
- `general`: open-ended multi-round tool exploration.
- `max`: deep reasoning, difficult implementation/verification, high ambiguity, or costly error.

The executor `Choice` is the only Jev answer allowed to select an executor. Confidence `<0.60` on **any** Jev choice, including `main`, abstains to `main_review`. The 50-request real holdout showed low-confidence `main` was not safer than other low-confidence labels.

Deterministic gates short-circuit the paid Jev call entirely unless `TYPESAFE_ROUTE_GATE_TELEMETRY=1`. A trusted caller may set `context.bounded_mechanical_task=true` only after locally establishing that a task is mechanical, clearly bounded, low-risk, and glance-verifiable. This deterministic rule routes to `sub` after confirmation checks and before Jev. Never derive it from untrusted task keywords alone.

`delegation_value`, `complexity`, `consequence`, and `parallelizable` are telemetry. They must not override executor Choice because separate Jev judgments can be jagged and need not obey cross-question invariants. `consequence >=2` only raises `risk_review_recommended`.

Parallelism is recommended only when `parallelizable >=0.85` and the accepted executor is neither `main` nor `main_review`.

## Deterministic precedence

1. Explicit user executor choice, supplied by the trusted caller as `context.explicit_executor`.
2. Missing confirmation for an action known to require it: `main_review`.
3. Trusted local bounded/mechanical classification: `sub`.
4. Jev Choice plus confidence abstention applied to every label.
5. Main assistant safety and tool policies always remain authoritative.

Never infer authorization from task text. Trusted controls are consumed locally and not sent to TypeSafe.

## Privacy

Send only the minimal task and optional compact summary. Never send API keys, passwords, tokens, private keys, unnecessary personal data, full chat history, or confidential files. Logs store a task fingerprint (SHA-256, or keyed HMAC when `TYPESAFE_TASK_HMAC_KEY` is set), typed outputs, model/version, latency, usage, policy version and outcomes—not task text.

## Additional shadow workflows

Authoritative thresholds and contracts live in `references/workflow-policy.md`; the stale summary that previously sat here (verify confidence 0.65, rank confidence 0.65 plus clear-winner Noul 0.60) was wrong — Noul answers carry no confidence field, and the real gates are verify `complete` + confidence ≥0.85 (plus evidence ≥0.80 when supplied), rank winner score ≥0.75 with margin ≥0.15.

- `verify`: verdict plus coverage telemetry; cannot prove factual correctness without supplied evidence.
- `rank`: 2–20 stable candidate IDs; `winner` or `shortlist`.
- `triage`: warning-only. It never authorizes an action.

These workflows stay shadow-only until each has a labeled dataset and acceptance criteria. Do not combine separate primitive probabilities into arithmetic risk scores unless calibrated on local data.

Pilot measurability: since v2.4.0 all four workflows write the same audit schema (`decision_id`, `workflow`, `usage`, `latency_ms`, `models_served`, `warnings`), so rank/verify/triage pilots are now countable, not just route.

## Pilot acceptance

Keep router advisory until at least 100 diverse real decisions with recorded reference executor and eventual task outcome. Report raw Choice accuracy, policy coverage, selective accuracy, confusion matrix, confidence bins, language slice, adversarial slice, stability, latency and cost. Synthetic benchmark success is routing accuracy only; never mark task execution success unless the task was actually completed and checked.
