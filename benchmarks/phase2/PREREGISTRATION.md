# Phase 2 — Preregistered Blind Shortlist Evaluation

Status: **DRAFT — NOT YET LOCKED**

Authority: [`../../archi.ai`](../../archi.ai), Section 5. If this protocol conflicts with `archi.ai`, `archi.ai` wins and this document must be amended before execution.

## 1. Research question

Does coverage-aware Jev shortlist selection reduce actual MAIN-model context cost while preserving evidence coverage and end-to-end answer quality, compared with no ranking and winner top-k, on a new bilingual Minis research workload?

This evaluation exists to resolve P0-6. The retracted 51.7% projection is not a prior result and is not used for design, tuning, power, or success criteria.

## 2. Scope and claims

The scored holdout contains **16 tasks**: 8 Croatian and 8 English. It is balanced across four preregistered research domains and two complexity strata. A separate **4-task development set** may be used only to test the harness and freeze the tuned arm. Development tasks and their gold are excluded from all scored metrics.

Claims are limited to this workload, candidate-set range, model versions, and cost snapshot. Phase 2 cannot establish autonomous safety, factual truth in arbitrary domains, or portability to other hosts.

## 3. Role separation

Three roles are logically separated:

1. **Dataset builder** freezes user-like queries, query-derived requirements, candidate documents, and candidate metadata without seeing scored gold.
2. **Gold curator** labels required/primary sources, requirement-to-source support, claim rubric, and known contradictions. The curator must not inspect Jev or MAIN outputs.
3. **Experiment runner** receives the frozen public input bundle and configuration, but not gold. It runs all arms and seals outputs. Gold is copied into the evaluation environment only after `outputs.lock.json` exists.

A person or process may perform more than one role only in separate sessions with an auditable file boundary. No role may alter a frozen upstream artifact. The provenance ledger records actor/process, UTC time, input hashes, and output hashes.

## 4. Dataset construction

### 4.1 Scored strata

| Dimension | Allocation |
|---|---:|
| Croatian | 8 |
| English | 8 |
| Four domains | 4 tasks each |
| Moderate: 2–3 independent requirements | 8 |
| Complex: 4–6 independent requirements | 8 |

The four domains are frozen before task authoring: software/technical documentation, public policy/regulation, science/health evidence, and consumer/product comparison. Tasks must be informational and non-personal; no private, paywalled, credentialed, or user-derived corpus is allowed in the public benchmark.

Each scored task has 10–16 candidate documents, including relevant, redundant, partially relevant, and irrelevant candidates. At least one task per language/domain combination must contain a near-duplicate pair. Candidate IDs and order are deterministic and content-neutral.

### 4.2 Requirements

Requirements are derived solely from the user query before the builder sees gold labels. Each task has 2–6 requirements with stable opaque IDs. Requirements may not contain source IDs, expected citations, answer text, gold labels, or hints unavailable to a normal workflow.

### 4.3 Candidate metadata

Allowed pre-gold metadata: URL, title, host/domain, publication date if directly observable, content text, and mechanically derived length. `required`, `primary`, `authority`, and `source_type` labels used for scoring or protection are gold-side fields unless a deterministic rule frozen in `config/metadata-policy.json` derives them without consulting outcomes.

## 5. Frozen experimental arms

All arms receive identical query, requirements, candidate documents, answer prompt, MAIN model, and token/output budget.

1. **A — no-rank:** all candidates in deterministic corpus order, subject only to the same MAIN hard context ceiling. If the full corpus cannot fit, the task is invalid and must be replaced before lock; no post-lock truncation policy is permitted.
2. **B — winner-top-k:** Jev global winner/rank scores; select top `k=8`, with deterministic score/ID tie-break.
3. **C — shortlist-default:** shipped v2.5.0 defaults (`max_candidates=8`, `target_context_chars=50000`, `minimum_score=0.25`, `minimum_coverage_score=0.40`, `max_per_domain=2`).
4. **D — shortlist-tuned:** one configuration selected on the 4-task development set and written to `config/tuned-arm.json` before the scored holdout is run. No scored result may influence it.

Jev-dependent arms B–D run **three repetitions**. A runs once because selection is deterministic. Every selection run generates an actual MAIN answer, producing 10 answer artifacts per task and 160 scored answers total.

Candidate presentation order is deterministically permuted per task/repetition from the preregistered seed schedule. Arm labels are hidden from answer-quality evaluators.

## 6. Models and execution freeze

Before lock, `config/execution.json` records:

- requested and served Jev model contract;
- MAIN model ID and provider;
- temperature, seed support, max output tokens, and system/user prompt hashes;
- TypeSafe and MAIN price snapshot with units and retrieval date;
- software commit and policy/schema versions;
- retry/deadline settings;
- target context/token accounting method.

A served Jev model mismatch invokes the existing drift gate. A MAIN model change after lock invalidates comparability and requires a new run identifier; mixed MAIN models are not pooled.

No production algorithm change is allowed between lock and scored completion. Operational bug fixes require aborting the run, documenting the defect, versioning the protocol, and creating a fresh untouched holdout if the fix could affect outcomes.

## 7. Primary metrics

Calculated per task first, then aggregated with paired task-level statistics:

- requirement coverage recall;
- required-source recall and primary-source recall;
- unsupported-claim rate;
- citation precision;
- contradiction/error rate;
- blinded end-to-end answer quality;
- MAIN input and total tokens;
- Jev input tokens, calls, latency, and cost;
- total end-to-end cost and latency;
- abstention/`human_review` rate;
- Kendall tau where score vectors are comparable;
- top-k Jaccard/overlap across repetitions;
- per-candidate score variance across repetitions.

`no-rank` is the baseline for coverage, quality, MAIN tokens, and total cost. Winner is a secondary comparator. Default shortlist is the confirmatory shortlist arm. Tuned shortlist is reported separately and cannot rescue a failing default confirmatory claim unless `archi.ai` is amended for a future untouched evaluation.

## 8. Quality evaluation

Evaluators receive query, answer, and cited source text, but not arm, repetition, selection trace, token/cost data, or other arms' answers. Answer order is randomized.

The frozen rubric scores: requirement completion, factual support, contradiction, citation correctness, and overall usefulness. Exact citation/claim labels use the gold curator's source spans. Where human adjudication is used, disagreements are preserved and resolved under the frozen adjudication rule; raw labels are retained.

## 9. Statistical analysis

- Report task-level values, medians/means as appropriate, and paired bootstrap 95% confidence intervals over tasks.
- Do not treat 160 answers as 160 independent tasks; repetitions are nested within 16 tasks.
- Report HR/EN, domain, and complexity slices descriptively; no unsupported subgroup superiority claims.
- Missing/failed runs are failures/abstentions under the frozen missingness policy, not silently dropped.
- No optional stopping. All 16 valid scored tasks must complete unless the whole run is declared invalid.
- If intervals are too wide to establish the quality gate, the outcome is **INCONCLUSIVE**, not PASS.

## 10. Phase 2 decision gate

Default shortlist C passes only if all conditions hold:

1. leakage/provenance audit passes;
2. mean task-level requirement coverage is at least 95% of no-rank baseline, and no hidden exclusion changes the denominator;
3. required-source recall is 100%;
4. blinded quality shows no practically meaningful degradation under the frozen margin in `config/decision-gates.json`;
5. actual total-cost break-even is positive on the frozen MAIN price snapshot;
6. results, failures, and limits are reproducible and published as measurements rather than projections.

Any failed mandatory condition yields FAIL. Insufficient precision, evaluator failure, material protocol ambiguity, model comparability loss, or incomplete valid tasks yields INCONCLUSIVE.

## 11. Leakage audit and unblinding

Before scored execution, run `python3 benchmarks/phase2/tools/phase2.py lock-inputs`. Before gold is accessible to evaluation, run `audit-pre-unblind`; it verifies:

- frozen manifest hashes;
- no gold fields/filenames in runner-visible inputs;
- no scored output timestamp predates input lock;
- all expected arm/repetition outputs exist;
- source commit/config/model metadata are fixed;
- output lock exists and matches every output byte.

Only then may `evaluate --gold <sealed-path>` read gold. Gold is never copied into `public/` or runner input directories before output lock.

## 12. Amendments and deviations

Before input lock, changes require a dated amendment entry and new protocol/config hashes. After input lock, no confirmatory threshold, arm, metric, exclusion, or tuned parameter may change. Deviations are reported; they do not silently become protocol. Exploratory analyses are labeled exploratory and cannot change PASS/FAIL/INCONCLUSIVE.

## 13. Stop conditions

Stop and invalidate the run on confirmed leakage, non-isolated gold access, wrong candidate corpus, mixed MAIN models, material prompt mismatch, production algorithm change, or corrupted provenance. API/transient failures follow frozen retry rules; unresolved failures count under missingness policy.

## 14. Current state

This document is a draft until all JSON configuration files, schemas, prompts, role assignments, and public inputs are complete and `lock-inputs` emits the immutable preregistration manifest. No Phase 2 result may be claimed before that lock.
