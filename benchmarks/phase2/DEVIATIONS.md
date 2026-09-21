# Phase 2 deviations and custody incidents

## D-001 — curator callback exposed insufficiency task IDs to coordinator

Date: 2026-09-21
Status: **OPEN MITIGATION — MUST BE AUDITED BEFORE UNBLINDING**

### Event

The isolated scored-gold curator completed before any Jev or MAIN scored output existed. Its terminal callback reported aggregate validation evidence and named two tasks with insufficient literal evidence (`p2-score-hr-04`, `p2-score-hr-06`), plus two broad limitations. It did **not** expose required/primary source IDs, requirement-to-source mappings, support spans, contradiction labels, or gold file content.

### Timing and non-response

The candidate source plan, all source amendments, local materialization, and runner-bundle bytes had already been completed before the callback. No query, requirement, candidate URL, candidate text, reuse class, tuned parameter, threshold, or decision gate was changed in response to the callback. The next repository commit only recorded already-produced corpus commitments and runner/lock tooling.

### Risk

The coordinating main process now knows that specific tasks may be evidence-poor. If the same process selected, modified, retried selectively, or interpreted scored arms before output lock, that knowledge could bias execution.

### Mandatory mitigation

1. Scored execution must run in a fresh isolated process/session that receives only `archi.ai`, preregistration/config/prompts, `inputs.lock.json`, runner inputs, and executable code.
2. The isolated runner must not receive this file, curator callback, gold custody path, curation summary, or any gold-derived task status.
3. The runner executes every preregistered task/arm/repetition uniformly and seals all 160 outputs before returning any result interpretation.
4. The coordinator may observe only operational progress (counts, transport failures), not answer quality or task-specific evaluation.
5. Pre-unblind audit must verify output completeness, input hashes, runner-session brief, and absence of gold mounts/environment/path references.
6. If source/task/config bytes changed after curator completion, or if the isolated runner receives gold-derived information, invalidate the holdout.

### Decision impact

This event is not silently waived. Final Phase 2 status cannot be PASS unless an independent provenance audit accepts the isolation evidence. Otherwise the outcome is `INCONCLUSIVE` or `INVALID`, regardless of metrics.
