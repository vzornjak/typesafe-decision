# typesafe-decision

An **unofficial**, advisory decision layer that uses [TypeSafe](https://typesafe.ai)'s
Jev model as a *typed sensor* for repeated structured judgments — candidate
reranking, requirement checking, executor routing and action-risk triage.

Local, deterministic code keeps control, safety, execution and the final
judgment. The model only ever produces advisory signals.

> **Not affiliated with, endorsed by, or supported by TypeSafe AI.**
> This is an independent third-party integration built for the
> [Minis](https://apps.apple.com/app/id6748124053) agent environment and
> released as-is. "TypeSafe", "Jev", "Noul" and "Choice" are used descriptively
> to identify the upstream API and its primitives. For the official skill and
> documentation see [Upstream & attribution](#upstream--attribution).

---

## Canonical project plan

[`archi.ai`](archi.ai) is the repository's binding architecture, phased roadmap,
execution policy, and Definition of Done. Read it before proposing work or
interpreting project status. Durable changes to scope, sequencing, safety rules,
or phase gates must update `archi.ai` in the same commit; do not create a
competing roadmap.

## Status

| | |
|---|---|
| Version | **2.5.0** (log schema **4**) |
| Maturity | **Experimental / advisory.** Not a safety control, not an authorization mechanism. |
| Tests | **119** unique regressions + **25** legacy contract selftests, fully offline |
| Audit | P0-1 … P0-5 closed, **P0-6 PARTIAL** (see below), P1-1 … P1-9 closed |
| Built for | Minis on iOS (iSH/Alpine, Python 3.11+). Portable to any POSIX host with Python 3.9+. |
| Network | One egress point, `TYPESAFE_OFFLINE=1` hard-blocks it |
| License | MIT (see `LICENSE`, `NOTICE`) |

### P0-6 is PARTIAL — read this before quoting any number

The earlier "shortlist v1.1 validation" claiming **0/12 uncovered requirements**
and **51.7% context reduction** is **RETRACTED**. It suffered from evaluation
leakage (the requirements sent to the model *were* the gold checklist), an
incorrect requirement count (11, not 12), and an undocumented non-default
parameter (`max_per_domain=4` while the shipped default is `2`).

**51.7% may only be cited as an uncontrolled projection, never as a
measurement.** Full detail: [`docs/RETRACTION-shortlist-v1.1.md`](docs/RETRACTION-shortlist-v1.1.md).

P0-6 is **PARTIAL**, not closed: the false claim is retracted and the retraction
is enforced by regression tests, but **no valid replacement evidence exists**.
Until a clean re-evaluation is done, `shortlist` stays experimental and
advisory. Rank and verify have no labeled outcome datasets at all; routing was
only ever supported for confidence-gated advisory use by a 50-request holdout.

---

## What it does

Four workflows, one shared contract (`decision_id`, `schema_version`, exit
codes, audit log):

| Workflow | Use it when | Never use it for |
|---|---|---|
| **rank** (`winner` / `shortlist`) | You have 2–20 plausible candidates and reviewing all of them is expensive. Prefer 5–20. | Deciding truth. Small sets where direct reading is cheaper. |
| **verify** | An output has a short, explicit, semantically judgeable checklist (1–20 requirements). | Factual verification. Blanket post-processing after every rank. |
| **route** | Executor choice is genuinely ambiguous. `main_review` means *abstain*. | Authorization. Anything a deterministic rule can decide. |
| **triage** | You want an extra warning signal on top of your own safety policy. | Granting permission. `authorization` is always `false`. |

**Skip the model entirely** when the answer is obvious, deterministic code can
decide exactly, the task needs arithmetic/counting/dates/proof, or an API round
trip costs more than reading the candidates yourself.

`shortlist` is the interesting mode: it scores **per requirement**, then runs a
deterministic local selection pass for coverage, authority, domain diversity and
character budget. Global relevance rank alone does not guarantee every
subquestion is covered.

---

## Architecture

```
                 caller (agent / script / CI)
                            │
        ┌───────────────────┴────────────────────┐
        │                                        │
  route_task.py                        decision_workflows.py
  (route)                              (rank | verify | triage)
        │                                        │
        └───────────────────┬────────────────────┘
                            │
                      ts_common.py
   version · payload budget · key-name scrubbing · preflight sizing
   single TRANSPORT egress seam · retry/backoff/deadline · model-drift gate
   content-free logging via the single log_sink seam · exit-code contract
                            │
              ┌─────────────┴─────────────┐
              │                           │
      TypeSafe /systemone          decisions.jsonl
      (only egress point)          (0600, locked, rotated)
                                          │
                              report.py · record_outcome.py

  tests: replay_harness.py (StubTransport / ReplayTransport / virtual clock)
         + tests/fixtures/*  (synthetic, hash-pinned, zero network)
```

Design rules that the tests enforce:

- **One egress point.** `ts_common.TRANSPORT`. Nothing else opens a socket.
  Tests replace that single attribute and are therefore hermetic.
- **One write seam.** `ts_common.log_sink(row, path)`. Replace it to ship rows
  elsewhere; every client dispatches through it.
- **Preflight before spend.** The *entire* request (state + questions) is sized
  before the first paid call. Oversize or non-finite input is refused with zero
  API calls.
- **Fail closed.** Malformed input, malformed envelope, missing key, timeout,
  API error, bad configuration or model drift all degrade to `human_review` /
  `main_review` / `insufficient_coverage` — never to a confident answer.
- **Deterministic selection.** The model scores; local code selects. Selection,
  dedup, coverage and budget are pure functions and are unit-tested directly.

---

## Install

No third-party Python dependencies. Standard library only.

```bash
git clone https://github.com/vzornjak/typesafe-decision.git
cd typesafe-decision
python3 -m py_compile scripts/*.py          # syntax gate
python3 scripts/selftest.py                 # 25 legacy contract tests, offline
python3 scripts/tests_phase1.py             # 119 regressions, offline
```

All tests run with `TYPESAFE_OFFLINE=1` and a synthetic temp log. They never
touch a real API, a real log or the network.

To use it against the live API you need an account and key from
[typesafe.ai](https://typesafe.ai):

```bash
export TYPESAFE_API_KEY='...'               # never commit this
```

### Use as a Minis / Claude-style agent skill

`SKILL.md` is the agent-facing instruction file. Drop the repository into your
skills directory (for Minis: `/var/minis/skills/typesafe-decision/`) and the
agent loads `SKILL.md` on demand.

---

## Usage examples

### rank — research shortlist (primary use)

```bash
cat > /tmp/rank.json <<'JSON'
{
  "mode": "shortlist",
  "query": "How do I publish a static site behind a CDN with automatic TLS and a rollback path?",
  "requirements": [
    {"id": "tls",      "text": "Automatic TLS issuance and renewal at the edge"},
    {"id": "purge",    "text": "Cache invalidation after a deploy"},
    {"id": "rollback", "text": "Rolling back to a previous deploy"}
  ],
  "selection": {"max_candidates": 8, "target_context_chars": 50000,
                "minimum_score": 0.25, "minimum_coverage_score": 0.40,
                "max_per_domain": 2},
  "candidates": [
    {"id": "c1", "title": "Edge TLS", "url": "https://docs.example.com/tls",
     "authority": "primary", "source_type": "official_documentation",
     "snippets": [{"section": "TLS", "text": "..."}]},
    {"id": "c2", "title": "Deploy rollback", "url": "https://docs.example.com/deploys",
     "authority": "primary", "source_type": "official_documentation", "required": true,
     "snippets": [{"section": "Rollback", "text": "..."}]}
  ]
}
JSON
python3 scripts/decision_workflows.py rank --input /tmp/rank.json --pretty
```

**Reading the result — non-negotiable:**

1. Use `selected` **only** when `decision == "selected"`.
2. **Always read `warnings` first.** Notable codes: `injection_vetoed:<id>`,
   `cover_candidate_blocked:<id>`, `duplicate_kept_for_unique_coverage:<id>`,
   `coverage_candidate_below_minimum_score:<id>`, `required_exceeded_*`,
   `near_duplicates_excluded:<n>`, `model_drift:*`, `partial_run_aborted:*`.
3. On `insufficient_coverage`, go retrieve more evidence for
   `uncovered_requirements`. Do not silently answer from an incomplete set.
4. Per-candidate provenance lives in `ranking[].eligible`,
   `ranking[].exclusion_reason` (`injection` | `near_duplicate`) and the
   top-level `duplicate_of` map.
5. `estimated_reduction_pct` is a **character** estimate over eligible,
   non-duplicate candidates — not API token accounting.

Hard limits enforced by code: 2–20 candidates, ≤12 shortlist requirements,
`max_candidates` 1–20, `target_context_chars` ≥1000, `minimum_score` and
`minimum_coverage_score` in [0,1], `max_per_domain` 1–20. Unknown `selection`
keys are rejected. `required: true` protects a source from pruning and overrides
the three budget limits (each with its own warning) — but **never** the
injection veto.

### rank — winner (pick one)

```bash
printf '%s' '{"query":"What best answers X?","criteria":["recent","primary source"],
 "candidates":[{"id":"c1","title":"...","snippet":"..."},
               {"id":"c2","title":"...","snippet":"..."}]}' \
 | python3 scripts/decision_workflows.py rank --pretty
```

### verify — checklist coverage (not truth)

```bash
printf '%s' '{"request":"Write the migration plan",
 "requirements":["Includes rollback","Names the tests"],
 "candidate_output":"...","evidence":"optional compact evidence"}' \
 | python3 scripts/decision_workflows.py verify --pretty
```

Requirements are batched at **≤8 per call**; with supplied evidence each
requirement adds a second question, so a full batch sends up to 16. Auto-pass
needs every requirement `complete` with confidence ≥0.85, plus a direct-evidence
score ≥0.80 when evidence was supplied. **A pass without evidence means coverage
only, never factual verification.**

### route — ambiguous executor choice

```bash
python3 scripts/route_task.py --task 'Refactor the payment retry logic'
printf '%s' '{"task":"...","context":{"summary":"minimal non-sensitive context"}}' \
 | python3 scripts/route_task.py --stdin-json
```

Read `policy.recommended_executor`. Any Jev label below confidence 0.60 returns
`main_review` (abstain). A deterministic gate short-circuits the API call
entirely for clear cases — **no spend**; set `TYPESAFE_ROUTE_GATE_TELEMETRY=1` if
you still want telemetry alongside the gate.

### triage — extra warning only

```bash
printf '%s' '{"action":"drop the staging database","deletes_data":true,"user_authorized":false}' \
 | python3 scripts/decision_workflows.py triage --pretty
```

Run your deterministic safety policy **first**. `authorization` is always
`false`. Control flags (`deletes_data`, `moves_money`, `publishes`, `deploys`,
`changes_credentials`, `security_change`, `user_authorized`) are read from the
**raw** input before scrubbing and must be real booleans — a string or number is
refused with zero API calls, so a hard-risk veto never depends on model
judgment.

### Audit aggregation

```bash
python3 scripts/report.py --pretty
python3 scripts/record_outcome.py --decision-id <id> --outcome accepted
```

---

## CLI and exit-code contract

- **stdout is always exactly one JSON document.**
- **Exit 0** — success *and* expected uncertainty: validation errors, missing API
  key, timeouts, HTTP errors, retry exhaustion, injection vetoes, missing
  coverage, log-write failures. The result is fail-closed.
- **Exit 2** — CLI misuse (unknown flag), emitted by argparse, still as JSON.
- **Exit 3** — unexpected internal fault (a bug), still after printing JSON where
  possible.

A log-write failure never changes a decision; it surfaces as `log_error`
(workflows) or `meta.log_error` (route).

---

## Environment variables

| Variable | Default | Meaning |
|---|---|---|
| `TYPESAFE_API_KEY` | *(none)* | API key. Missing ⇒ fail-closed `human_review`, exit 0. **Never commit.** |
| `TYPESAFE_SYSTEMONE_URL` | upstream `/systemone` | API endpoint. Never taken from model output or task text. |
| `TYPESAFE_OFFLINE` | unset | `1` hard-blocks network egress even with a key, and refuses writes to the default log. All tests set it. |
| `TYPESAFE_DEFAULT_LOG` | `/var/minis/shared/typesafe-decision/decisions.jsonl` | Moves the **default** audit-log path for non-Minis deployments. Minis default retained when unset. |
| `TYPESAFE_DECISION_LOG` | *(default log)* | Per-run log override. Takes precedence over `TYPESAFE_DEFAULT_LOG`. (`TYPESAFE_ROUTER_LOG` is a legacy alias.) |
| `TYPESAFE_MAX_LOG_BYTES` | `5242880` | Size-based rotation threshold. |
| `TYPESAFE_LOG_ROTATE_KEEP` | `3` | Rotated generations kept. |
| `TYPESAFE_TASK_HMAC_KEY` | *(none)* | Switches fingerprints and opaque log refs from SHA-256 to keyed HMAC. **Set this in shared/multi-tenant deployments.** |
| `TYPESAFE_MAX_STATE_CHARS` | `24000` | Local payload budget (state + questions). |
| `TYPESAFE_REQUEST_TIMEOUT` | `30` s | Per-request timeout. |
| `TYPESAFE_WORKFLOW_DEADLINE_SECONDS` | `120` s | Global per-workflow deadline. |
| `TYPESAFE_RETRY_ATTEMPTS` | `3` | Retries for `408/425/429/5xx`, exponential backoff + jitter, honours `Retry-After`. |
| `TYPESAFE_RETRY_BASE_SECONDS` / `TYPESAFE_RETRY_MAX_SECONDS` | `0.5` / `8.0` | Backoff shape. |
| `TYPESAFE_ALLOW_MODEL_DRIFT` | unset | `1` accepts a served model other than the pinned one (still warned). |
| `TYPESAFE_ROUTER_CONFIDENCE` | `0.60` | Routing abstention threshold. |
| `TYPESAFE_ROUTER_PARALLEL` | — | Parallelism threshold for routing. |
| `TYPESAFE_ROUTE_GATE_TELEMETRY` | unset | `1` still calls Jev for telemetry when the deterministic gate already decided. |
| `TYPESAFE_FIXTURES_DIR` | `tests/fixtures` | Frozen synthetic replay fixtures used by the harness. |

Malformed or out-of-range configuration produces **one fail-closed JSON
document** with `reason:"invalid_configuration"` and content-free
`config_errors` — never a traceback.

---

## Safety and privacy model

**What this is not:** not a safety control, not an authorization mechanism, not
a factual verifier. Every output is advisory. Your deterministic policy stays
authoritative.

**Caller-side minimization is mandatory.** Inputs are scrubbed **by key name
only** — snake_case, kebab-case and camelCase variants of
key/token/secret/password/auth/bearer/cookie/credential/otp/pin/session are
redacted. **Values are never scanned.** A secret pasted into a free-text `note`
*will* be transmitted. Never send credentials, full conversation history, or
unnecessary personal data.

**Prompt injection.** Candidate content is treated as untrusted data. A candidate
scoring ≥0.5 on the injection probe is vetoed, and the veto is surfaced in
`warnings` on **every** path including partial results. `exclusion_reason:
"injection"` is never relabelled, and `required: true` does **not** override it.

**Model pinning.** If the served model differs from `jev-1.13.0`, any
`pass` / `selected` / `allow_advisory` and **any** winner is degraded to
`human_review` with `model_drift:true`. The gate is mode-aware, so a candidate
ID that happens to read `block` or `review` cannot bypass it.

**What the audit log contains** (`0600`, advisory-locked append, rotated):
`workflow`, `version`, `mode`, `decision` (fixed vocabulary), counts,
`api_calls`/`api_attempts`/`api_responses_received`, `usage`, `latency_ms`,
`model_requested`/`models_served`, `model_drift`, sanitized `warnings`,
`warnings_total`, and a content-free `input_sha256` (route: `task_sha256`).

**What it deliberately does not contain:** task text, candidate content,
requirement text, credentials. In `winner` mode even the winning candidate ID is
withheld — the row carries an opaque `decision_ref` plus the warning
`winner_id_withheld_from_log`, while the full ID stays in stdout. Warning
payloads collapse to structured codes and opaque fingerprints; an unrecognised
code becomes `unknown_warning`. `record_outcome --note` stores only `note_len`
and an opaque `note_ref` unless you explicitly pass `--allow-note-in-log`, which
labels the row `note_policy:"explicitly_allowed_free_text"`.

*Accepted residual exposure:* workflow names, policy statuses, counts, model
names, timings, exception-type names, fingerprints.

**Offline guarantee and its limits.** `TYPESAFE_OFFLINE=1` blocks egress and
refuses writes to the default production log — covering the path, a symlink to
it, and a hardlink sharing its inode. It is a guard against accidental test
writes, **not** a defence against a process that deliberately opens the file.

**Business / EU deployments.** Jev calls send request state to a third party. A
DPA and a GDPR lawful-basis assessment are required before any personal data is
sent.

See also [`SECURITY.md`](SECURITY.md).

---

## Tests

```bash
python3 -m py_compile scripts/*.py tests/*.py   # syntax gate
python3 scripts/selftest.py                     # 25 legacy contract tests
python3 scripts/tests_phase1.py --verbose       # 119 audit regressions
python3 tests/run_tests.py                      # all of the above, one command
python3 tests/generate_fixtures.py              # regenerate synthetic fixtures
```

Properties the suite guarantees:

- **Zero network.** `socket.create_connection` is monkeypatched to raise, and
  `TYPESAFE_OFFLINE=1` makes the real transport raise even with a key present.
- **Zero production data.** `TYPESAFE_DEFAULT_LOG` is repointed at a synthetic
  temp file *before* `ts_common` is imported, so even the production-log guard
  tests operate on a throwaway file through the identical code path.
- **No duplicate-test inflation.** A repeated `(finding, name)` pair is a hard
  failure, and the summary reports `tests` vs `unique_tests` separately.
- **Final gates run last**, so they observe the complete side-effect surface:
  no secret-looking value in any log the suite produced, and the default log
  untouched.
- **Hash-pinned replay.** Fixtures are verified against
  `tests/fixtures/MANIFEST.sha256.json` (per-file *and* aggregate) before every
  replay; a tampered fixture raises `FixtureIntegrityError`.

### Fixtures are synthetic

Everything under `tests/fixtures/` is generated by
[`tests/generate_fixtures.py`](tests/generate_fixtures.py): authored scores,
generated prose, `.test` hostnames. No real corpus, no real API transcript, no
production log, no personal data — `provenance.txt` records this explicitly and
a test asserts it. The "gold" labels are **authored**, not human relevance
judgements; they exist only to lock a *relative* policy property and carry no
evaluation authority.

---

## Known limitations

- **P0-6 PARTIAL** — retracted validation, no replacement evidence. See above.
- **`shortlist` is experimental/advisory.** No clean quality evaluation exists.
- **Rank and verify have no labeled outcome datasets.** Routing is supported
  only for confidence-gated advisory use.
- **Scrubbing is key-name based.** No value-level secret detector is
  implemented. Caller-side minimization is mandatory.
- **Log rotation is size-based only.** No time-based rotation, no compression.
- **Pluggable sink is one replaceable function**, not a named-backend registry.
- **Replay cassettes are reconstructed** from aggregated ranking rows, not raw
  HTTP transcripts. Capturing real transcripts needs a live run.
- **The cost model is a calibration, not an independent validation.** Two frozen
  points, treated as a projection. `winner` ≈ 6,928 Jev input tokens,
  `shortlist` ≈ 37,794 on the same 16 sources (~5×) — do not quote the winner
  figure for a shortlist run.
- **Offline is a configuration fact**, asserted at the transport seam, not an
  independent packet-level measurement.
- **Built and validated for Minis.** Other hosts should work (stdlib only,
  `TYPESAFE_DEFAULT_LOG` override) but are not continuously validated beyond CI.

---

## Upstream & attribution

This project is **independent and unofficial**.

- TypeSafe: <https://typesafe.ai>
- Official documentation: <https://docs.typesafe.ai/llms.txt> ·
  <https://docs.typesafe.ai/llms-full.txt>
- Official skills repository: <https://github.com/typesafe-ai/skills>

`references/official-SKILL.md` is a verbatim copy of the official TypeSafe Agent
Skill (upstream front matter declares `license: MIT`), retrieved 2026-09-20 from
the upstream repository at commit
`65a39f393687675ce170e6094757de20370365b9`. The unmodified upstream MIT text is
kept in `references/official-LICENSE`; its bytes are pinned by a regression
test. Attribution details are in [`NOTICE`](NOTICE).

This repository's own code is MIT licensed — see [`LICENSE`](LICENSE).

---

## Repository layout

```
SKILL.md                      agent-facing instructions (the skill entry point)
README.md                     this file
LICENSE  NOTICE               MIT + upstream attribution
CONTRIBUTING.md  SECURITY.md  CHANGELOG.md
pyproject.toml                packaging/tooling metadata (stdlib-only project)
docs/RETRACTION-shortlist-v1.1.md   the P0-6 retraction, in full
references/routing-policy.md        routing and safety policy
references/workflow-policy.md       rank/verify/triage contracts and thresholds
references/official-SKILL.md        verbatim upstream skill (MIT)
references/official-LICENSE         verbatim upstream MIT text
scripts/ts_common.py                version, budget, scrub, transport, retry, drift, logging
scripts/route_task.py               route client
scripts/decision_workflows.py       rank / verify / triage client
scripts/replay_harness.py           offline stub & replay transports, virtual clock
scripts/report.py                   audit aggregation
scripts/record_outcome.py           outcome capture
scripts/selftest.py                 25 legacy contract tests
scripts/tests_phase1.py             119 audit regressions
tests/run_tests.py                  single entry point for the whole suite
tests/generate_fixtures.py          deterministic synthetic fixture generator
tests/fixtures/                     frozen synthetic fixtures + SHA-256 manifest
.github/workflows/ci.yml            CI: compile, tests, secret & path scans
```

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md). Short version: no new dependencies, no
network in tests, no real logs or corpora in fixtures, every behaviour change
gets a regression test, and no claim of official affiliation.
