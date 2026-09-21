# Development tuning record

Status: **FROZEN — DEVELOPMENT ONLY — NOT CONFIRMATORY EVIDENCE**

Four synthetic tasks were generated before any development Jev output existed: one task per domain, two Croatian and two English. An isolated curator process labeled literal support spans without seeing model output. Those curator files and raw model outputs remain in gitignored local custody.

## Execution

- Jev model: `jev-1.13.0`
- tasks: 4
- repetitions per task: 3
- Jev workflow runs: 12
- API calls: 36
- input tokens: 53,712
- output tokens: 17,016 (free under the frozen TypeSafe price)
- estimated Jev list-price cost: `$0.00225590`
- production decision log: not used; temporary log only

The selected candidate **sets** were identical across all three repetitions for every task (mean pairwise Jaccard `1.0`); ordering varied. The shipped default recovered all synthetic development required sources in all 12 runs.

## Frozen tuning rule

A deterministic grid of 162 configurations was evaluated from the already recorded Jev score vectors. Selection priority was preregistered in the tuning script:

1. maximize mean requirement coverage;
2. maximize mean required-source recall;
3. minimize selected candidate count;
4. deterministic configuration tie-break.

Chosen tuned arm:

```json
{
  "max_candidates": 5,
  "target_context_chars": 4000,
  "minimum_score": 0.25,
  "minimum_coverage_score": 0.4,
  "max_per_domain": 1
}
```

Development result: mean requirement coverage `1.0`, mean required-source recall `1.0`, mean selected candidates `4.5`.

These values only prove that the harness and tuning procedure function on deliberately separable synthetic data. They do not establish real-world quality and cannot rescue a failing confirmatory default arm.
