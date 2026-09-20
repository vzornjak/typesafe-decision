# Phase 2 role and custody declaration

Complete this file before `lock-inputs`. Replace every `TBD`; do not include secrets or personal data beyond a public role identifier.

| Role | Actor/process ID | Inputs visible | Outputs produced | Gold visible? |
|---|---|---|---|---|
| Dataset builder | TBD | query design rules, public candidate sources | public tasks and query-derived requirements | No |
| Gold curator | TBD | frozen public tasks and candidate corpus | sealed gold bundle | Yes, after public inputs freeze |
| Experiment runner | TBD | input lock, public tasks, configs, prompts | Jev selections, MAIN answers, usage and timing | No |
| Blind evaluator | TBD | randomized answers, cited source text, frozen rubric | quality/claim/citation labels | Yes only during evaluation |
| Provenance auditor | TBD | manifests, role ledger, runner tree, output lock | pre-unblind audit decision | No gold content required |

## Custody rules

1. During scored execution, sealed gold is outside the runner-visible repository and output directory.
2. The experiment runner cannot be given filenames, fields, environment variables, mounts, or prompts that reveal gold.
3. Every transfer records UTC time, source/destination role, aggregate SHA-256, and purpose in an external custody ledger.
4. `audit-pre-unblind` must pass before gold is mounted/copied for evaluation.
5. A custody violation invalidates the run; it is not repaired by deleting evidence afterward.
