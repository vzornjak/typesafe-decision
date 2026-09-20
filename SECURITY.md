# Security Policy

## Scope and threat model

`typesafe-decision` is an **advisory** layer. It is explicitly **not** a safety
control and **not** an authorization mechanism. Your deterministic policy
remains authoritative, and `triage` always returns `authorization: false`.

This policy covers the code in this repository. Vulnerabilities in the TypeSafe
API itself belong to TypeSafe AI — see <https://typesafe.ai>. This project is
unofficial and has no ability to fix upstream issues.

### In scope

- Secret or content leakage into the audit log, stdout, or the API payload
  beyond the documented exposure.
- A path that lets untrusted candidate/task text influence the API URL, the log
  path, or the configuration.
- A prompt-injection path that bypasses the injection veto or relabels its
  provenance.
- A model answer that upgrades a fail-closed outcome (`human_review`,
  `main_review`, `insufficient_coverage`) into a confident one.
- A model-drift bypass: a non-pinned model producing an un-degraded
  `pass`/`selected`/`allow_advisory`/winner.
- A hard-risk triage veto that can be flipped by model judgment or by a
  non-boolean control flag.
- Audit log files created with permissions weaker than `0600`, or log writes
  that escape the documented path handling.
- `TYPESAFE_OFFLINE=1` failing to block network egress.

### Out of scope

- The absence of a **value-level** secret detector. Scrubbing is documented as
  **key-name based only**; values are never scanned. A secret pasted into a
  free-text field *will* be transmitted. This is a documented limitation, and
  caller-side minimization is mandatory.
- `TYPESAFE_OFFLINE` not stopping a process that deliberately opens the log
  file directly. The guard covers path, symlink and hardlink identity for
  accidental test writes only; this scope limit is documented.
- The quality, accuracy or calibration of model judgments. Every output is
  advisory. Bad rankings are not vulnerabilities.
- Missing evaluation evidence (see the P0-6 PARTIAL disclosure in the README).
  That is a known, disclosed gap, not a security issue.
- Anything requiring an attacker who already has write access to the code, the
  environment variables, or the log file.

## Reporting a vulnerability

**Do not open a public issue.**

Use GitHub's private vulnerability reporting on this repository
(*Security* → *Report a vulnerability*). If that is unavailable, open a public
issue containing **only** the sentence "requesting a private security contact"
and no technical detail.

Please include:

- affected file(s) and version (`scripts/ts_common.py` → `__version__`),
- a minimal reproduction — ideally as a test in the style of
  `scripts/tests_phase1.py`, using synthetic data only,
- the impact you believe it has, and which guarantee it breaks,
- any suggested fix.

**Never include real secrets, real API keys, real logs or personal data in a
report.** Redact them, or describe the shape instead.

### What to expect

This is a small, unfunded, unofficial project maintained on a best-effort
basis. There is no SLA. Realistically:

- acknowledgement: within about 7 days,
- initial assessment: within about 30 days,
- fix or public disclosure of the limitation: as soon as practical.

If a report describes something already documented as a limitation, it will be
closed as out of scope with a pointer to the relevant documentation.

Coordinated disclosure is appreciated. If you plan to publish, please give a
reasonable window first.

## Handling secrets in this project

- `TYPESAFE_API_KEY` and `TYPESAFE_TASK_HMAC_KEY` come from the environment
  only. Never commit them, never write them into a fixture, never paste them in
  an issue.
- `tests/run_tests.py` runs a secret scan (API-key shapes, tokens, private key
  blocks, JWTs, hardcoded bearer headers) over every tracked text file, and CI
  fails on a hit.
- The test suite's final gate asserts that no secret-looking value appears in
  any log file the suite produced.
- In shared or multi-tenant deployments, set `TYPESAFE_TASK_HMAC_KEY` so log
  fingerprints cannot be brute-forced across tenants.

## Privacy

The audit log is designed to be content-free: fixed-vocabulary decisions,
counts, timings, model names, sanitized warning codes and opaque fingerprints.
Task text, candidate content and requirement text are never written. In `winner`
mode even the winning candidate ID is withheld from the log.

The single documented exception is `record_outcome --allow-note-in-log`, an
explicit opt-in that labels the row
`note_policy: "explicitly_allowed_free_text"`.

Business and EU deployments: Jev calls transmit request state to a third party.
A DPA and a GDPR lawful-basis assessment are required before sending any
personal data.
