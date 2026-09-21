# Phase 2 workspace

This directory implements Section 5 of the repository-root [`archi.ai`](../../archi.ai).

## Current state

**Draft preregistration only. No scored dataset, gold, model output, or Phase 2 result exists yet.**

## Trust boundary

```text
builder input/public bundle ──> experiment runner ──> outputs lock
                                      X
                           sealed gold unavailable

sealed gold + locked outputs ──> evaluator ──> metrics/decision
```

- `public/` is runner-visible and must never contain gold fields.
- `builder-provenance/` records task-construction lineage but contains no gold.
- `private-development/` is gitignored local custody for synthetic development-only gold and Jev outputs; it is never confirmatory evidence.
- Gold is created and stored outside the runner-visible repository while the scored run is active.
- `schemas/gold-task.schema.json` specifies format only; it is not gold data.
- `tools/phase2.py` creates and verifies manifests and enforces the pre-unblind boundary.

## Planned commands

```bash
# Validate draft/frozen public tasks and configuration
python3 benchmarks/phase2/tools/phase2.py validate

# Freeze runner-visible inputs before any scored model call
python3 benchmarks/phase2/tools/phase2.py lock-inputs \
  --actor dataset-builder --note 'Phase 2 v1 input freeze'

# After every expected model/answer artifact exists
python3 benchmarks/phase2/tools/phase2.py lock-outputs \
  --outputs /path/to/isolated/outputs --actor experiment-runner

# Before gold is made available to evaluation
python3 benchmarks/phase2/tools/phase2.py audit-pre-unblind \
  --outputs /path/to/isolated/outputs
```

Commands fail closed while required configuration fields, prompts, tasks, role declarations, or output artifacts are missing.

## Files

- `PREREGISTRATION.md` — research protocol and analysis contract.
- `config/design.json` — sample size, strata, arms, repetitions, randomization.
- `config/execution.json` — models, prompts, versions, prices, retry/deadline freeze.
- `config/decision-gates.json` — confirmatory PASS/FAIL/INCONCLUSIVE thresholds.
- `config/metadata-policy.json` — public/gold field boundary.
- `schemas/` — public input and sealed-gold schemas.
- `public/` — public development tasks plus scored placeholders; when a local `runner-inputs/` bundle exists, scored lock validation uses that bundle instead.
- `builder-provenance/` — no-gold task/source lineage and content-free corpus hash commitments.
- `DEVELOPMENT-RECORD.md` — public summary of synthetic tuning, without curator labels or raw outputs.
- `private-development/` — gitignored local custody; never confirmatory evidence.
- `source-cache/`, `materialized-scored/`, `runner-inputs/` — gitignored local source text and final scored runner input, committed by hash rather than republished.
- `tools/` — local validation, hashing, and leakage-audit utilities.

The old contaminated shortlist experiment is excluded by design and remains only a documented retraction elsewhere in the repository.
