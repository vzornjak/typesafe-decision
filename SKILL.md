---
name: typesafe-decision
version: 2.5.0
description: Use TypeSafe Jev as a low-cost advisory decision layer for ambiguous task routing, reranking 2–20 research/search candidates, checking an output against explicit requirements, or warning about action risk. Trigger for repeated structured judgments over shared context; skip obvious tasks, factual proof, arithmetic, authorization, and small cases where direct review is cheaper.
---

# TypeSafe Decision Layer

Use Jev as a typed sensor. Local code and the main agent retain control, safety, execution, and final judgment.

Scope: this skill was built and validated for Minis. It is stdlib-only and runs on any POSIX host with Python 3.9+; set `TYPESAFE_DEFAULT_LOG` to move the default audit-log path off the Minis location. Hosts other than Minis are covered by CI but not continuously validated in production.

## Choose a workflow

1. **rank** — primary use. Use after collecting plausible candidates when detailed review of all is expensive. The code accepts 2–20 candidates; below ~5 the round trip usually costs more than direct review, so prefer 5–20 in practice.
2. **verify** — use when an output has an explicit checklist (1–20 requirements). Without supplied evidence it checks coverage/coherence only, not truth. Long documents automatically use payload-safe requirement batches.
3. **route** — use only when executor choice is genuinely ambiguous. Treat `main_review` as abstention.
4. **triage** — optional warning signal. It never grants authorization.

Skip Jev when:

- the answer/action is already obvious;
- there are fewer than 5 rank candidates unless each is expensive to inspect;
- deterministic code can decide exactly;
- the task needs arithmetic, counting, dates, proof of truth, or final safety approval;
- adding an API round trip costs more than direct review.

## Rank

Use `winner` only to choose one candidate. For research/RAG source reduction, use `shortlist`: global rank alone does not guarantee that every subquestion is covered.

```bash
python3 scripts/decision_workflows.py rank --input rank.json --pretty
```

Winner input remains backward compatible:

```json
{"query":"What best answers X?","criteria":["recent","primary source"],"candidates":[{"id":"c1","title":"...","snippet":"..."},{"id":"c2","title":"...","snippet":"..."}]}
```

Research shortlist input:

```json
{
  "mode":"shortlist",
  "query":"Research question",
  "requirements":[{"id":"setup","text":"Setup steps"},{"id":"encryption","text":"Encryption properties"}],
  "selection":{"max_candidates":8,"target_context_chars":50000,"minimum_score":0.25,"minimum_coverage_score":0.40,"max_per_domain":2},
  "candidates":[
    {"id":"c1","title":"...","url":"https://...","authority":"primary","source_type":"official_documentation","snippets":[{"section":"Setup","text":"..."}]},
    {"id":"c2","title":"...","url":"https://...","authority":"primary","source_type":"protocol","required":true,"snippets":[{"section":"Encryption","text":"..."}]}
  ]
}
```

`shortlist` evaluates per-requirement support, then deterministically selects for coverage, authority, diversity and budget. Hard limits enforced by code: 2–20 candidates, at most 12 shortlist requirements, `selection` values validated to `max_candidates` 1–20, `target_context_chars` ≥1000, `minimum_score` and `minimum_coverage_score` in [0,1], `max_per_domain` 1–20. Unknown `selection` keys are rejected.

`required:true` protects a source from pruning and **overrides all three limits** (`max_candidates`, `target_context_chars`, `max_per_domain`), each with its own warning. It never overrides the injection veto.

### Reading the result

- Use `selected` only when `decision` is `selected`.
- **Always read `warnings` before using `selected`.** Notable values: `injection_vetoed:<id>`, `cover_candidate_blocked:<id>`, `duplicate_kept_for_unique_coverage:<id>`, `coverage_candidate_below_minimum_score:<id>`, `required_exceeded_*`, `near_duplicates_excluded:<n>`, `model_drift:*`, `partial_run_aborted:*`.
- Per-candidate fields you may need: `ranking[].eligible`, `ranking[].exclusion_reason` (`injection` | `near_duplicate`), and the top-level `duplicate_of` map.
- On `insufficient_coverage`, retrieve more evidence for `uncovered_requirements`; do not silently generate an incomplete answer.
- `estimated_reduction_pct` is computed over **eligible, non-duplicate** candidates. `estimated_reduction_pct_vs_all_candidates` is the older, more flattering number. Both are character estimates, not API token accounting.

### Cost

Per-requirement scoring costs roughly 5× the Jev input tokens of the old global `winner` rank (measured: 6,928 vs 37,794 input tokens on the same 16 sources). Break-even on main-model input price therefore differs per mode:

| Mode | Jev input tokens | Break-even main input price |
|---|---|---|
| `winner` | 6,928 (measured) | $0.0199/Mtok (measured) |
| `shortlist` | 37,794 (measured) | $0.1442/Mtok (projection) |

Both remain deeply positive for frontier models, but do not quote the winner figure for shortlist runs.

## Verify

```bash
python3 scripts/decision_workflows.py verify --input verify.json --pretty
```

Input:

```json
{"request":"...","requirements":["Includes rollback","Names tests"],"candidate_output":"...","evidence":"optional compact evidence"}
```

Use verify selectively, not as mandatory post-processing after rank. It is appropriate only when the checklist is short, explicit and semantically judgeable; the real research A/B test found no useful discrimination from blanket verify calls.

Requirements share the largest payload-safe batches of **at most 8 requirements per call**. Without evidence that is up to 8 questions; with supplied evidence each requirement adds a second Noul question, so a full batch sends up to **16 questions**. Both the state and the question text count against the local payload budget.

Auto-pass requires every requirement to be `complete` with confidence ≥0.85; when evidence is supplied, the direct-evidence score must also be present and ≥0.80. A missing evidence answer produces `human_review` plus `missing_evidence_score:<rid>`, never a crash. A pass without evidence means coverage only, never factual verification.

## Route

```bash
python3 scripts/route_task.py --task '...'
printf '%s' '{"task":"...","context":{"summary":"minimal context"}}' | python3 scripts/route_task.py --stdin-json
```

Read `policy.recommended_executor`. Confidence below 0.60 on any Jev label returns `main_review`. Trusted context may contain:

- `explicit_executor`: explicit user choice (`main|sub|general|max`)
- `confirmation_required` and `user_authorized`
- `bounded_mechanical_task`: locally established mechanical, bounded, low-risk, glance-verifiable work; never infer it merely from keywords
- `summary`: minimal non-sensitive context

A deterministic gate short-circuits the API call entirely (no spend); set `TYPESAFE_ROUTE_GATE_TELEMETRY=1` if you still want Jev telemetry alongside the gate.

## Triage

```bash
python3 scripts/decision_workflows.py triage --input triage.json --pretty
```

Run deterministic safety and confirmation policy first. Use triage only as an extra warning. `authorization` is always `false`.

## CLI and exit-code contract

- stdout is always exactly one JSON document.
- **Exit 0** for success *and* for expected uncertainty: validation errors, missing API key, timeouts, HTTP errors, retry exhaustion, injection vetoes, missing coverage, log-write failures. The result is fail-closed (`human_review` / `main_review` / `insufficient_coverage`).
- **Exit 2** for CLI misuse (unknown flags), emitted by argparse.
- **Exit 3** for an unexpected internal fault (a bug), still after printing a JSON document where possible.
- A log-write failure never changes the decision; it appears as `log_error` (workflows) or `meta.log_error` (route).

## Observability

All four workflows share `decision_id`, `schema_version`, log schema and the audit log (default `/var/minis/shared/typesafe-decision/decisions.jsonl` — the Minis deployment path; move the default with `TYPESAFE_DEFAULT_LOG` on other hosts, override per run with `TYPESAFE_DECISION_LOG`, disable with `--no-log`, redirect with `--log-path`).

Each row carries `workflow`, `version`, `mode`, `decision`, counts, `api_calls`/`api_attempts`/`api_responses_received`, `usage`, `latency_ms`, `model_requested`/`models_served`, `model_drift`, sanitized `warnings`, and a content-free `input_sha256` (route stores `task_sha256`). Log files are created `0600`, appended under an advisory lock, rotated at `TYPESAFE_MAX_LOG_BYTES` (default 5 MB, keeping `TYPESAFE_LOG_ROTATE_KEEP` generations, default 3), and `python3 scripts/report.py` groups by workflow while tolerating legacy rows that predate `schema_version`.

**What is and is not content-free (scope of the claim, v2.5.0):**

- `decision` is always a value from a fixed policy vocabulary. In `winner` mode the candidate ID is **not** logged; the row carries `decision:"winner"` plus an opaque `decision_ref` (SHA-256, or HMAC when `TYPESAFE_TASK_HMAC_KEY` is set) and the warning `winner_id_withheld_from_log`. The full ID stays in the stdout result under `winner_id`.
- `warnings` are reduced to structured codes: an unrecognised code collapses to `unknown_warning`, arbitrary payloads (candidate/requirement IDs, domains) become opaque fingerprints, and only numeric counts, model names and exception-type prefixes survive verbatim. `warnings_total` records how many were produced.
- `usage` keeps only finite numbers; non-finite values are dropped rather than propagated.
- `record_outcome --note` is **not** written to the log by default: only `note_len` and an opaque `note_ref` are stored, and the note is echoed back on stdout. `--allow-note-in-log` is an explicit opt-in, and rows written that way are labelled `note_policy:"explicitly_allowed_free_text"`.
- The single write seam is `ts_common.log_sink(row, path)`. Replace that attribute to ship rows to another sink; `write_log` dispatches through it, so one seam covers every client.
- Accepted residual exposure: workflow names, policy statuses, counts, model names, timings, exception-type names and fingerprints. Free text from a caller only ever reaches the log through the explicit `--allow-note-in-log` opt-in.

## Reliability

- `429/529/5xx/408/425` are retried up to `TYPESAFE_RETRY_ATTEMPTS` (default 3) with exponential backoff plus jitter, honouring `Retry-After`. `4xx` other than those is not retried.
- Each workflow has a global deadline (`TYPESAFE_WORKFLOW_DEADLINE_SECONDS`, default 120 s) so a chunked run cannot retry indefinitely.
- Preflight sizes the **entire** request (state plus questions) before the first paid call. Oversize input is refused with zero API calls. NaN/Infinity anywhere in the input is rejected in the same preflight, so a non-finite value can never surface after a paid call.
- Deployment configuration (`TYPESAFE_RETRY_*`, `TYPESAFE_REQUEST_TIMEOUT`, `TYPESAFE_WORKFLOW_DEADLINE_SECONDS`, `TYPESAFE_MAX_STATE_CHARS`, `TYPESAFE_ROUTER_CONFIDENCE`/`_PARALLEL`, `TYPESAFE_SYSTEMONE_URL`) is parsed and range-checked **inside** the protected entrypoint. A malformed or out-of-range value produces one fail-closed JSON document with `reason:"invalid_configuration"` and content-free `config_errors`, never a traceback.
- If a later chunk fails after earlier chunks were already paid for, the partial result is returned with `decision:"human_review"`, `partial_usage`, `api_calls` < `planned_api_calls`, and a `partial_run_aborted:*` warning. Paid work is never silently discarded.
- Attempts, received responses and accepted chunks are accounted separately (`api_attempts`, `api_responses_received`, `api_calls`). A response that was received and billed but **not** accepted — a malformed `answers`/`usage` shape, or a success arriving after the deadline — still contributes its known usage to `partial_usage`/`unaccepted_usage`, with a `malformed_response_usage_preserved` or `late_response_usage_preserved` warning.
- Injection vetoes are surfaced in `warnings` on **every** path, including partial results, and the `exclusion_reason:"injection"` provenance on the ranking row is never relabelled.
- Model pinning is enforced: if the served model differs from `jev-1.13.0`, `pass`/`selected`/`allow_advisory` and **any** winner are degraded to `human_review` with `model_drift:true`. The gate is mode-aware, so a candidate ID that happens to read `block`, `review` or `insufficient_coverage` cannot bypass it; a degraded winner is marked `winner_id_degraded:true`. Set `TYPESAFE_ALLOW_MODEL_DRIFT=1` to accept drift explicitly (still warned).

## Privacy and failure behavior

- Never send secrets, credentials, full conversation history, or unnecessary personal/private content.
- Inputs are recursively scrubbed **by key name only** — snake_case, kebab-case and camelCase variants of key/token/secret/password/auth/bearer/cookie/credential/otp/pin/session names are redacted. **Values are never scanned**, so a secret pasted into a `note` string is transmitted. Caller-side minimization is mandatory, not optional.
- `triage` control flags (`deletes_data`, `moves_money`, `publishes`, `deploys`, `changes_credentials`, `security_change`, `user_authorized`) are read from the **raw** input *before* scrubbing, and must be real booleans — a string or number is refused with zero API calls. The redacted copy is built separately and is the only thing that leaves the process, so a hard-risk veto never depends on the model's judgement.
- State is capped locally; rank automatically chunks candidates against the real payload size.
- Every workflow fails closed to `human_review` (or `insufficient_coverage`) on malformed input, malformed API envelope, missing key, timeout, API error, bad configuration, or drift.
- Task fingerprints are SHA-256 by default; set `TYPESAFE_TASK_HMAC_KEY` in shared/multi-tenant environments so fingerprints cannot be brute-forced across tenants. The same key switches the opaque log identifiers (`decision_ref`, `note_ref`, sanitized warning payloads) to keyed HMAC.
- `TYPESAFE_OFFLINE=1` hard-blocks network egress (even with a key present) and refuses writes to the default production log. Scope of that guarantee: the refusal covers the path, a symlink to it, and a hardlink sharing its inode. It is a guard against accidental test writes, **not** a defence against a process that deliberately opens the file directly or replaces it. All tests run with it set.
- The API URL and log path come from the environment/CLI, never from model output or untrusted task text.
- Business and EU deployments: Jev calls send request state to a third party. A DPA and a GDPR lawful-basis assessment are required before sending any personal data.
- Do not invoke multiple Jev workflows automatically on every task. One suitable workflow is the default; chain `rank → detailed review → verify` only for high-value research deliverables.

## Accepted deviations from the phase-1 plan

Recorded explicitly rather than implied as done (status at v2.5.0):

- **Local secret detector for values — not implemented.** Scrubbing remains key-name based; the documentation above states this plainly. Caller-side minimization stays mandatory.
- **Log rotation — implemented, size-based only.** `TYPESAFE_MAX_LOG_BYTES` / `TYPESAFE_LOG_ROTATE_KEEP`. Time/date-based rotation and compression are out of scope for this phase.
- **Pluggable log sink — implemented as a single replaceable function** (`ts_common.log_sink`), not as a registry of named backends. That broader interface is deferred.
- **Replay provenance — frozen SYNTHETIC fixtures with runtime hash verification.** `tests/fixtures/MANIFEST.sha256.json` is checked (per-file and aggregate) before every replay and the replayer refuses modified inputs. The cassettes are reconstructed from aggregated ranking rows, **not** raw HTTP transcripts; capturing real transcripts needs a live run and is therefore phase 2. The fixtures in this repository are generated by `tests/generate_fixtures.py` and contain no real corpus, transcript or log.
- **Cost model — calibration, not independent validation.** Two frozen points; treated as a projection.
- **Clean re-evaluation of shortlist quality — phase 2.** The contaminated v1.1 validation stays retracted (see *Evaluation status*).
- **Network-egress measurement.** Tests assert that the offline transport raises and that stubs answer every request; `offline:true` is a configuration fact, not an independent packet-level measurement.

## Evaluation status

Routing remains advisory: the real 50-request holdout supported only confidence-gated use. Rank and verify need their own labeled outcome datasets before any broader auto-accept behavior.

**Retracted:** the earlier shortlist v1.1 validation claiming "0/12 uncovered" and **51.7%** character reduction is withdrawn as evidence of quality. The requirements sent to Jev were the gold checklist itself (evaluation leakage), the real requirement count was 11 not 12, and the run used `max_per_domain=4` while the documented default is 2. Treat 51.7% as an uncontrolled **projection**, not a measurement. A clean re-evaluation is required before any quality claim.

## Files

- `README.md` — public overview, install, safety model and audit status
- `LICENSE`, `NOTICE` — MIT license and upstream attribution
- `docs/RETRACTION-shortlist-v1.1.md` — the P0-6 retraction in full
- `references/routing-policy.md` — routing and safety policy
- `references/workflow-policy.md` — rank/verify/triage contracts and thresholds
- `references/official-SKILL.md`, `references/official-LICENSE` — verbatim upstream copies (MIT)
- `scripts/ts_common.py` — shared version, budget, scrub, transport, retry, drift gate, logging
- `scripts/route_task.py` — route client
- `scripts/decision_workflows.py` — rank/verify/triage client
- `scripts/replay_harness.py` — offline stub/replay transports and virtual clock
- `scripts/report.py`, `scripts/record_outcome.py` — audit aggregation and outcome capture
- `scripts/selftest.py` — legacy behaviour contract (25 tests)
- `scripts/tests_phase1.py` — regression tests for every audited P0/P1 finding (119 tests)
- `tests/run_tests.py` — one command: compile, selftest, regressions, fixture integrity, hygiene scans
- `tests/generate_fixtures.py`, `tests/fixtures/` — deterministic synthetic fixtures and their SHA-256 manifest
