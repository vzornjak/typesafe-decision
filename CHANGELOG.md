# Changelog

All notable changes to this project are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/).

Two versions are tracked separately:

- **project version** — `scripts/ts_common.py` → `__version__`
- **log schema version** — `scripts/ts_common.py` → `SCHEMA_VERSION`, bumped only
  when the audit-row shape changes; `report.py` must keep reading older rows.

---

## [Unreleased]

### Added

- **Public repository packaging.** `README.md`, `CONTRIBUTING.md`,
  `SECURITY.md`, this changelog, `.gitignore`, `pyproject.toml` and a GitHub
  Actions workflow (`.github/workflows/ci.yml`).
- **`tests/run_tests.py`** — one entry point running six stages: `py_compile`,
  `selftest`, `regressions`, `fixture_integrity`, `secret_scan` and
  `absolute_path_scan`. Emits a single JSON report; exit 0 only when all pass.
- **`tests/generate_fixtures.py`** — deterministic generator for fully
  synthetic replay fixtures (authored scores, generated prose, `.test`
  hostnames), producing `tests/fixtures/` plus a per-file and aggregate
  SHA-256 manifest.
- **`TYPESAFE_DEFAULT_LOG`** — moves the *default* audit-log path for non-Minis
  deployments. The Minis path remains the built-in default when it is unset;
  `TYPESAFE_DECISION_LOG` and `--log-path` still take precedence.
- **`TYPESAFE_FIXTURES_DIR`** — points the replay harness at a different frozen
  fixture set.
- **`docs/RETRACTION-shortlist-v1.1.md`** — the full P0-6 retraction now ships
  with the code instead of living in an internal note.
- Hygiene gates: a secret scan (API-key shapes, tokens, private key blocks,
  JWTs, hardcoded bearer headers) and an absolute-path scan, both enforced in
  CI.
- Fixture manifest verification now also checks the **aggregate** hash and the
  declared-vs-on-disk file set, so a fixture cannot be added or removed
  silently.

### Changed

- **Tests are now self-contained and portable.** All hard dependencies on
  `/var/minis/workspace/...` are gone. The suite runs from a fresh clone on any
  POSIX host with Python 3.9+.
- **Tests never touch a real production log.** `TYPESAFE_DEFAULT_LOG` is
  repointed at a synthetic temp file *before* `ts_common` is imported, so the
  production-log guard tests (`_is_production_log`, the offline write refusal,
  the symlink/hardlink identity checks) exercise the identical code path
  against a throwaway file.
- **Replay fixtures replaced with synthetic equivalents.** The private
  benchmark corpus is no longer referenced. The synthetic corpus reproduces the
  policy properties the tests assert, including the P0-6 property that the
  documented default `max_per_domain=2` recalls fewer same-domain sources than
  the undocumented `max_per_domain=4` used by the retracted run.
- The upstream-license regression now pins the verbatim upstream MIT bytes by
  SHA-256 and checks that `NOTICE` records the verified upstream commit,
  instead of requiring a local upstream checkout.
- The stray-artifact regression scans the whole repository for argparse
  artifact files instead of one hardcoded working directory.
- `replay_harness.child_env` uses `tempfile.gettempdir()` instead of a
  hardcoded `/tmp`.
- `README.md` and `SKILL.md` now state the unofficial status, the P0-6 PARTIAL
  caveat and the experimental/advisory status of `shortlist` explicitly.
- `NOTICE` updated: the project is described as unofficial and publicly
  distributed under MIT.

### Unchanged

- **119 unique regressions and 25 selftests**, all still passing. No test was
  deleted, weakened or duplicated to reach that count; the suite still treats a
  repeated `(finding, name)` pair as a hard failure.
- Project version **2.5.0**, log schema **4**. No runtime behaviour change other
  than the two new, optional environment variables.
- **P0-6 remains PARTIAL.** The retracted validation stays retracted and no
  replacement evidence exists. `shortlist` remains experimental and advisory.

---

## [2.5.0]

### Added

- Content-free logging hardened: `winner` candidate IDs withheld from the log
  (opaque `decision_ref` plus `winner_id_withheld_from_log`), warnings reduced
  to structured codes with opaque fingerprints, `warnings_total`, non-finite
  `usage` values dropped.
- `record_outcome --note` no longer logged by default — only `note_len` and an
  opaque `note_ref`; `--allow-note-in-log` is an explicit opt-in labelled
  `note_policy: "explicitly_allowed_free_text"`.
- `TYPESAFE_TASK_HMAC_KEY` switches fingerprints and opaque log identifiers from
  SHA-256 to keyed HMAC for shared/multi-tenant deployments.
- Single replaceable write seam `ts_common.log_sink(row, path)`.
- Separate accounting for `api_attempts`, `api_responses_received` and
  `api_calls`, with `partial_usage` / `unaccepted_usage` and the
  `malformed_response_usage_preserved` / `late_response_usage_preserved`
  warnings, so billed-but-unaccepted work is never silently discarded.
- Global per-workflow deadline (`TYPESAFE_WORKFLOW_DEADLINE_SECONDS`).
- Configuration parsed and range-checked inside the protected entrypoint;
  invalid values produce one fail-closed document with
  `reason: "invalid_configuration"` and content-free `config_errors`.
- Size-based log rotation (`TYPESAFE_MAX_LOG_BYTES`, `TYPESAFE_LOG_ROTATE_KEEP`).

### Changed

- Log schema bumped to **4**; `report.py` tolerates legacy rows that predate
  `schema_version`.
- Model-drift gate made mode-aware, so a candidate ID reading `block`, `review`
  or `insufficient_coverage` cannot bypass it; a degraded winner is marked
  `winner_id_degraded: true`.
- Preflight sizes the entire request (state plus questions) before the first
  paid call; oversize or non-finite input is refused with zero API calls.
- `triage` control flags are read from the raw input before scrubbing and must
  be real booleans, so a hard-risk veto never depends on model judgment.
- `TYPESAFE_OFFLINE=1` also refuses writes to the default production log by
  path, symlink target and inode identity.

### Retracted

- The shortlist **v1.1 validation** ("0/12 uncovered", **51.7%** reduction) is
  withdrawn as evidence of quality: evaluation leakage, wrong requirement count
  (11, not 12) and an undocumented `max_per_domain=4`. 51.7% may only be cited
  as an uncontrolled projection. **P0-6 is PARTIAL.**

---

## Earlier versions

Earlier development happened as an internal Minis skill and is not reconstructed
here. This repository's history begins with the public packaging above.
