# Repository layout

```text
.
├── archi.ai                        Canonical architecture, roadmap, gates and DoD
├── SKILL.md                         Agent-facing skill contract
├── README.md                        Public overview, use and safety model
├── CHANGELOG.md                     Version and packaging history
├── CONTRIBUTING.md                  Contribution and evidence rules
├── SECURITY.md                      Vulnerability and privacy policy
├── LICENSE                          Project MIT license
├── NOTICE                           Upstream attribution and trademark notice
├── pyproject.toml                   Package metadata and test command
├── benchmarks/
│   └── phase2/                     Blind shortlist evaluation protocol, schemas and lock tools
├── scripts/
│   ├── ts_common.py                 Shared config, transport, retry, drift, logging
│   ├── decision_workflows.py        rank, verify and triage workflows
│   ├── route_task.py                executor routing workflow
│   ├── replay_harness.py            deterministic stub/replay infrastructure
│   ├── selftest.py                  25 legacy contract tests
│   ├── tests_phase1.py              119 unique P0/P1/hardening regressions
│   ├── record_outcome.py            append a decision outcome
│   └── report.py                    aggregate content-free audit rows
├── references/
│   ├── routing-policy.md            deterministic routing policy
│   ├── workflow-policy.md           rank/verify/triage policy
│   ├── official-SKILL.md            attributed upstream reference copy
│   └── official-LICENSE             verbatim upstream license copy
├── tests/
│   ├── run_tests.py                 canonical six-stage offline gate
│   ├── generate_fixtures.py         deterministic synthetic fixture generator
│   └── fixtures/                    generated, hash-pinned public test data
├── docs/
│   ├── RETRACTION-shortlist-v1.1.md P0-6 disclosure
│   ├── RELEASE-AUDIT.md             exact release evidence and exclusions
│   ├── REPOSITORY-LAYOUT.md         this document
│   └── PUBLISH-CHECKLIST.md         maintainer publish procedure
└── .github/workflows/ci.yml         offline CI on Python 3.9–3.13
```

## Runtime boundary

`archi.ai` governs the repository's architecture, phase order, execution constraints, gates, and Definition of Done. Durable changes to those rules must update it rather than creating a parallel roadmap.

Runtime behavior lives in `scripts/`. It has no third-party Python dependencies. `ts_common.py` is the shared trust boundary: configuration, the single network transport seam, retry/deadline accounting, model-drift handling, content-free logging, and exit-code conventions.

`SKILL.md` tells an agent when and how to use those scripts. `references/` contains policy detail and the attributed upstream reference, but not private local state.

## Test boundary

`tests/run_tests.py` is the only release gate maintainers and CI need to invoke. It runs compilation, the 25 selftests, all 119 unique regressions, Phase 2 protocol contract tests, synthetic fixture integrity, secret scanning, and absolute-path dependency scanning.

`tests/fixtures/` is generated data, not evaluation evidence. Its provenance is `origin=synthetic`; its scores are authored to reproduce policy properties. Regenerate only through `tests/generate_fixtures.py` and commit the updated manifest.

## Data deliberately not represented

There is no production log, user conversation, real benchmark corpus, API credential, real API transcript, session identifier, or agent-coordination evidence anywhere in this repository. Public tests use temporary files and synthetic fixtures only.
