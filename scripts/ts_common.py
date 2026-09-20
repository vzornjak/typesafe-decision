#!/usr/bin/env python3
"""Shared contract for the TypeSafe advisory decision layer.

Single source of truth for version, payload budget, scrubbing, network egress
(with retry/backoff/deadline), model-drift enforcement, observability logging
and the CLI exit-code contract. Imported by route_task.py, decision_workflows.py,
report.py and record_outcome.py.

Design rules:
- One egress point (`TRANSPORT`). Tests replace it; nothing else opens sockets.
- `TYPESAFE_OFFLINE=1` hard-blocks the network transport even when an API key
  is present, so offline test suites cannot make paid calls.
- Sleeping and clock reads go through `SLEEP` / `MONOTONIC` so retry tests are
  instant and hermetic.
- Logging never raises; a log failure is reported in the result, never fatal.
"""
import argparse
import hashlib
import hmac
import json
import math
import os
import random
import re
import secrets
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

__version__ = "2.5.0"
SCHEMA_VERSION = 4
# Back-compatible aliases (older readers looked for these two names).
POLICY_VERSION = __version__
WORKFLOW_VERSION = __version__


class ConfigError(ValueError):
    """A deployment/configuration value is missing, malformed or out of range.

    Raised at import time is NOT acceptable: every CLI calls `load_config()`
    inside its protected entrypoint, so a bad env var becomes one fail-closed
    JSON document instead of a traceback (audit P1 config/import path).
    """


CONFIG_ERRORS = []


def _cfg_num(name, default, caster, lo, hi):
    """Parse one numeric env var. Never raises at import; records the problem."""
    raw = os.environ.get(name)
    if raw is None or str(raw).strip() == "":
        return caster(default)
    try:
        value = caster(str(raw).strip())
    except (TypeError, ValueError):
        CONFIG_ERRORS.append(f"{name}:not_a_number")
        return caster(default)
    if not math.isfinite(float(value)):
        CONFIG_ERRORS.append(f"{name}:not_finite")
        return caster(default)
    if not lo <= value <= hi:
        CONFIG_ERRORS.append(f"{name}:out_of_range[{lo},{hi}]")
        return caster(default)
    return value


def _cfg_url(name, default):
    raw = os.environ.get(name)
    if raw is None or str(raw).strip() == "":
        return default
    raw = str(raw).strip()
    if not (raw.startswith("http://") or raw.startswith("https://")):
        CONFIG_ERRORS.append(f"{name}:not_an_http_url")
        return default
    return raw


def config_errors():
    """Sorted, content-free configuration problem codes (env var name + reason)."""
    return sorted(set(CONFIG_ERRORS))


def load_config():
    """Re-read every numeric/URL config value and fail closed on any problem.

    Call this FIRST inside the protected CLI entrypoint. Raises ConfigError with
    a machine-readable, content-free list of offending variable names.
    """
    global API_URL, MODEL, MAX_STATE_CHARS, MAX_PAYLOAD_CHARS
    global RETRY_ATTEMPTS, RETRY_BASE_SECONDS, RETRY_MAX_SECONDS
    global REQUEST_TIMEOUT, WORKFLOW_DEADLINE_SECONDS
    del CONFIG_ERRORS[:]
    API_URL = _cfg_url("TYPESAFE_SYSTEMONE_URL", "https://api.typesafe.ai/v1/systemone")
    MODEL = os.environ.get("TYPESAFE_ROUTER_MODEL") or PINNED_MODEL
    MAX_STATE_CHARS = _cfg_num("TYPESAFE_MAX_STATE_CHARS", 24000, int, 500, 1_000_000)
    MAX_PAYLOAD_CHARS = MAX_STATE_CHARS
    RETRY_ATTEMPTS = _cfg_num("TYPESAFE_RETRY_ATTEMPTS", 3, int, 1, 20)
    RETRY_BASE_SECONDS = _cfg_num("TYPESAFE_RETRY_BASE_SECONDS", 0.5, float, 0.0, 60.0)
    RETRY_MAX_SECONDS = _cfg_num("TYPESAFE_RETRY_MAX_SECONDS", 8.0, float, 0.0, 600.0)
    REQUEST_TIMEOUT = _cfg_num("TYPESAFE_REQUEST_TIMEOUT", 30.0, float, 0.1, 3600.0)
    WORKFLOW_DEADLINE_SECONDS = _cfg_num("TYPESAFE_WORKFLOW_DEADLINE_SECONDS", 120.0, float, 0.1, 86400.0)
    errors = config_errors()
    if errors:
        raise ConfigError("invalid_configuration:" + ",".join(errors))
    return {"api_url_configured": API_URL != "https://api.typesafe.ai/v1/systemone",
            "model": MODEL, "max_state_chars": MAX_STATE_CHARS,
            "retry_attempts": RETRY_ATTEMPTS, "request_timeout": REQUEST_TIMEOUT,
            "workflow_deadline_seconds": WORKFLOW_DEADLINE_SECONDS}


PINNED_MODEL = "jev-1.13.0"
API_URL = _cfg_url("TYPESAFE_SYSTEMONE_URL", "https://api.typesafe.ai/v1/systemone")
MODEL = os.environ.get("TYPESAFE_ROUTER_MODEL") or PINNED_MODEL

# Local conservative budget. Applies to the serialized state AND to
# state+questions combined, because both are billed and both enter context.
MAX_STATE_CHARS = _cfg_num("TYPESAFE_MAX_STATE_CHARS", 24000, int, 500, 1_000_000)
MAX_PAYLOAD_CHARS = MAX_STATE_CHARS

# Cost model calibrated on two frozen rank runs: 3.92 and 3.83 chars/input token.
# This is a CALIBRATION over two points, not an independent validation; treat
# any figure derived from it as a projection. See README "Known limitations".
CHARS_PER_INPUT_TOKEN = 3.87
JEV_USD_PER_MTOK_INPUT = 0.042

RETRY_STATUS = {408, 425, 429} | set(range(500, 600))
RETRY_ATTEMPTS = _cfg_num("TYPESAFE_RETRY_ATTEMPTS", 3, int, 1, 20)
RETRY_BASE_SECONDS = _cfg_num("TYPESAFE_RETRY_BASE_SECONDS", 0.5, float, 0.0, 60.0)
RETRY_MAX_SECONDS = _cfg_num("TYPESAFE_RETRY_MAX_SECONDS", 8.0, float, 0.0, 600.0)
REQUEST_TIMEOUT = _cfg_num("TYPESAFE_REQUEST_TIMEOUT", 30.0, float, 0.1, 3600.0)
WORKFLOW_DEADLINE_SECONDS = _cfg_num("TYPESAFE_WORKFLOW_DEADLINE_SECONDS", 120.0, float, 0.1, 86400.0)

# Default audit-log location. The Minis deployment path stays the built-in
# default; `TYPESAFE_DEFAULT_LOG` lets another deployment (or a test run) move
# the *default* without patching code. Per-run overrides remain
# `TYPESAFE_DECISION_LOG` / `--log-path`, which take precedence over this.
DEFAULT_LOG = os.environ.get(
    "TYPESAFE_DEFAULT_LOG", "/var/minis/shared/typesafe-decision/decisions.jsonl")

# Exit-code contract. Expected uncertainty is always a valid JSON document on
# stdout with exit 0; only unexpected programming faults use a nonzero code.
EXIT_OK = 0
EXIT_USAGE = 2          # argparse / CLI misuse
EXIT_INTERNAL = 3       # unexpected exception type: bug, not an input problem

EXPECTED_ERRORS = (
    ValueError,          # local validation, including json.JSONDecodeError
    TypeError,           # malformed API answer shapes
    KeyError,            # missing API answer keys
    IndexError,
    RuntimeError,        # missing API key
    OSError,             # log/file/socket level failures
    TimeoutError,
    urllib.error.URLError,   # HTTPError subclasses URLError
)


class TransportError(RuntimeError):
    """Any non-success HTTP exchange or blocked/unavailable transport."""


def exit_code_for(exc):
    return EXIT_OK if isinstance(exc, EXPECTED_ERRORS) else EXIT_INTERNAL


# ---------------------------------------------------------------- scrubbing
# Token-based matching: a key name is split on camelCase and any non-alphanumeric
# separator, so api_key / apiKey / x-api-key / API-KEY all match, while ordinary
# words that merely contain a secret substring (authority, author, keypoints,
# keywords, tokenizer_config) are preserved.
SECRET_TOKENS = {
    "key", "keys", "token", "tokens", "secret", "secrets", "password", "passwords",
    "passwd", "pwd", "passphrase", "authorization", "auth", "bearer", "cookie", "cookies",
    "credential", "credentials", "otp", "mfa", "totp", "pin", "salt", "signature",
    "apikey", "apikeys", "accesstoken", "refreshtoken", "idtoken", "privatekey",
    "sshkey", "clientsecret", "signingkey", "sessionid", "sessionkey", "authheader",
}
SECRET_PAIRS = {
    ("api", "key"), ("access", "token"), ("refresh", "token"), ("id", "token"),
    ("private", "key"), ("public", "key"), ("ssh", "key"), ("client", "secret"),
    ("signing", "key"), ("session", "id"), ("session", "key"), ("auth", "header"),
    ("secret", "key"), ("encryption", "key"), ("hash", "key"), ("bearer", "token"),
}
_CAMEL = re.compile(r"(?<=[a-z0-9])(?=[A-Z])")
_SPLIT = re.compile(r"[^A-Za-z0-9]+")
# Kept for backward-compatible introspection by older callers/tests.
_SENSITIVE_WORD = re.compile("|".join(sorted(SECRET_TOKENS, key=len, reverse=True)), re.I)


def key_tokens(key):
    name = _CAMEL.sub("_", str(key))
    return [t.lower() for t in _SPLIT.split(name) if t]


def sensitive_key(key):
    """True when a mapping key name looks like a secret holder.

    Values are never scanned; caller-side minimization stays mandatory.
    """
    tokens = key_tokens(key)
    if any(t in SECRET_TOKENS for t in tokens):
        return True
    return any((a, b) in SECRET_PAIRS for a, b in zip(tokens, tokens[1:]))


def scrub(value, depth=0):
    if depth > 6:
        return "[omitted:depth]"
    if isinstance(value, dict):
        return {str(k): ("[redacted]" if sensitive_key(k) else scrub(v, depth + 1)) for k, v in value.items()}
    if isinstance(value, list):
        return [scrub(v, depth + 1) for v in value]
    if value is None or isinstance(value, (bool, int, float)):
        return value
    return str(value)


def state_size(state):
    return len(json.dumps(state, ensure_ascii=False, separators=(",", ":")))


# ------------------------------------------------------- finiteness contract
def assert_finite(obj, where="input", depth=0, _path=""):
    """Reject NaN/Infinity anywhere in a nested structure.

    Called during local preflight (before any paid call) and on every API
    envelope, so the strict `allow_nan=False` serializer can never be surprised
    later (audit P2 non-finite numbers).
    """
    if depth > 12:
        raise ValueError(f"{where}_too_deeply_nested:{depth}")
    if isinstance(obj, bool) or obj is None:
        return obj
    if isinstance(obj, float):
        if not math.isfinite(obj):
            raise ValueError(f"non_finite_number:{where}{_path}")
        return obj
    if isinstance(obj, int):
        return obj
    if isinstance(obj, dict):
        for k, v in obj.items():
            assert_finite(v, where, depth + 1, f"{_path}.{k}")
        return obj
    if isinstance(obj, (list, tuple)):
        for i, v in enumerate(obj):
            assert_finite(v, where, depth + 1, f"{_path}[{i}]")
        return obj
    return obj


def finite_numbers(mapping):
    """Keep only finite int/float values from a mapping. Bools are dropped."""
    if not isinstance(mapping, dict):
        return {}
    return {str(k): v for k, v in mapping.items()
            if isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)}


def validate_envelope(data, require_answers=True):
    """Strictly validate an API response envelope BEFORE any attribute access.

    Returns (answers_dict, usage_dict, model_string). Raises ValueError on any
    unexpected shape, so a malformed late/second response can never raise an
    unguarded AttributeError outside the partial-result boundary
    (audit P1 malformed answers/usage shape).
    """
    if not isinstance(data, dict):
        raise ValueError(f"api_envelope_not_an_object:{type(data).__name__}")
    usage_raw = data.get("usage")
    if usage_raw is not None and not isinstance(usage_raw, dict):
        raise ValueError(f"api_usage_not_an_object:{type(usage_raw).__name__}")
    usage = finite_numbers(usage_raw or {})
    model = data.get("model")
    if model is not None and not isinstance(model, str):
        raise ValueError(f"api_model_not_a_string:{type(model).__name__}")
    answers = data.get("answers")
    if require_answers:
        if not isinstance(answers, dict):
            raise ValueError(f"api_answers_not_an_object:{type(answers).__name__}")
        if not answers:
            raise ValueError("api_answers_empty")
        for k, v in answers.items():
            if not isinstance(v, dict):
                raise ValueError(f"api_answer_not_an_object:{str(k)[:40]}")
        assert_finite(answers, "api_answers")
    elif answers is not None and not isinstance(answers, dict):
        raise ValueError(f"api_answers_not_an_object:{type(answers).__name__}")
    return (answers if isinstance(answers, dict) else {}), usage, (model if model is not None else None)


def usage_of(data):
    """Best-effort, never-raising usage extraction, for accounting a response
    whose result is NOT accepted (malformed shape or post-deadline arrival)."""
    if not isinstance(data, dict):
        return {}
    return finite_numbers(data.get("usage") or {})


# --------------------------------------------- audit-log sanitization
STATUS_DECISIONS = ("block", "review", "allow_advisory", "pass", "human_review",
                    "selected", "insufficient_coverage", "main", "sub", "general",
                    "max", "main_review")
# Warning codes that may keep a controlled, non-arbitrary suffix. Everything
# else is reduced to its bare code plus a count.
WARNING_CODES = (
    "injection_vetoed", "near_duplicates_excluded", "duplicate_kept_for_unique_coverage",
    "duplicate_requeued_for_feasibility", "cover_candidate_blocked",
    "coverage_candidate_below_minimum_score", "required_source_vetoed",
    "required_source_not_selected", "required_exceeded_max_candidates",
    "required_exceeded_max_per_domain", "required_exceeded_target_context_chars",
    "partial_run_aborted", "late_response_usage_preserved", "malformed_response_usage_preserved",
    "model_drift", "model_drift_allowed_by_env", "downgraded_for_model_drift",
    "model_drift_under_deterministic_gate", "missing_evidence_score", "failed_closed",
    "deterministic_gate_no_api_call", "invalid_configuration", "log_rotated",
    "winner_id_withheld_from_log", "note_omitted_from_log",
)
_SAFE_SUFFIX = re.compile(r"^[A-Za-z0-9_.:,\-]{0,64}$")


def opaque_id(value):
    """Short opaque fingerprint of an arbitrary identifier.

    HMAC-keyed when TYPESAFE_TASK_HMAC_KEY is set, otherwise plain SHA-256.
    Only the first 16 hex chars are kept: enough to correlate rows within one
    deployment, not a carrier of the original string (audit P1 log content).
    """
    raw = str(value).encode("utf-8")
    key = os.environ.get("TYPESAFE_TASK_HMAC_KEY")
    if key:
        return "h:" + hmac.new(key.encode("utf-8"), raw, hashlib.sha256).hexdigest()[:16]
    return "s:" + hashlib.sha256(raw).hexdigest()[:16]


def sanitize_warning(warning):
    """Reduce one warning to a structured, content-free code.

    `code:payload` becomes `code:<opaque>` when the payload is an arbitrary
    identifier, and unknown codes become `unknown_warning`. Numeric-only
    payloads (counts) are preserved because they carry no content.
    """
    text = str(warning)
    code, _, payload = text.partition(":")
    if code not in WARNING_CODES:
        return "unknown_warning"
    if not payload:
        return code
    if payload.isdigit():
        return f"{code}:{payload}"
    if code in ("model_drift", "partial_run_aborted", "invalid_configuration"):
        # Model names and exception-type prefixes are deployment facts, not task
        # content; still length-capped and character-restricted.
        safe = payload.split(":")[0][:48]
        return f"{code}:{safe}" if _SAFE_SUFFIX.match(safe) else code
    return f"{code}:{opaque_id(payload)}"


def sanitize_warnings(warnings, limit=20):
    out = []
    for w in (warnings or [])[:limit]:
        out.append(sanitize_warning(w))
    return out


def sanitize_decision(decision, allowed=STATUS_DECISIONS):
    """Return (log_decision, opaque_or_None).

    A recognised policy status is logged verbatim. Anything else (for example a
    winner candidate ID) is replaced with the literal `winner` plus a separate
    opaque fingerprint, so arbitrary strings never enter the log.
    """
    if decision is None:
        return None, None
    text = str(decision)
    if text in allowed:
        return text, None
    return "winner", opaque_id(text)


def payload_size(state, questions):
    return state_size({"model": MODEL, "state": scrub(state), "questions": questions})


def validate_state(state, questions=None):
    # Non-finite numbers are rejected during preflight, so the strict
    # allow_nan=False request serializer can never fail after a paid call.
    assert_finite(state, "state")
    if questions is not None:
        assert_finite(questions, "questions")
    n = state_size(state)
    if n > MAX_STATE_CHARS:
        raise ValueError(f"state_too_large:{n}>{MAX_STATE_CHARS}; compact or chunk input")
    if questions is not None:
        total = payload_size(state, questions)
        if total > MAX_PAYLOAD_CHARS:
            raise ValueError(f"payload_too_large:{total}>{MAX_PAYLOAD_CHARS}; fewer questions or smaller state")
    return n


def estimate_input_tokens(payload_chars):
    return int(round(payload_chars / CHARS_PER_INPUT_TOKEN))


def estimate_usd(payload_chars):
    return round(estimate_input_tokens(payload_chars) * JEV_USD_PER_MTOK_INPUT / 1_000_000, 8)


# ---------------------------------------------------------------- transport
SLEEP = time.sleep
MONOTONIC = time.monotonic


def network_transport(url, body_bytes, headers, timeout):
    """The only place a socket is opened. Returns (status, headers, body)."""
    if os.environ.get("TYPESAFE_OFFLINE") == "1":
        raise TransportError("offline_mode_network_blocked")
    req = urllib.request.Request(url, data=body_bytes, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            status = getattr(r, "status", None) or r.getcode()
            return int(status), dict(r.headers or {}), r.read()
    except urllib.error.HTTPError as e:
        return int(e.code), dict(e.headers or {}), (e.read() or b"")
    except urllib.error.URLError as e:
        raise TransportError(f"url_error:{getattr(e, 'reason', e)}") from e


TRANSPORT = network_transport


def set_transport(fn):
    """Install a replay/stub transport. Returns the previous one."""
    global TRANSPORT
    prev = TRANSPORT
    TRANSPORT = fn
    return prev


def _retry_after_seconds(headers):
    raw = None
    for k, v in (headers or {}).items():
        if str(k).lower() == "retry-after":
            raw = v
            break
    if raw is None:
        return None
    try:
        value = float(str(raw).strip())
        return max(0.0, value) if math.isfinite(value) else None
    except ValueError:
        from email.utils import parsedate_to_datetime
        try:
            return max(0.0, parsedate_to_datetime(str(raw)).timestamp() - time.time())
        except (ValueError, TypeError, OverflowError):
            return None


def post_json(body, url=None, timeout=None, attempts=None, deadline=None, rng=None, accounting=None):
    """POST JSON with exponential backoff + jitter, Retry-After and a deadline.

    Raises TransportError on exhausted retries, non-retryable status or a
    blocked transport; ValueError when the body is not decodable JSON.

    `accounting` (optional mutable dict) separates ATTEMPTS, RECEIVED RESPONSES
    and ACCEPTED results. The usage of a response that is received but not
    accepted (arrived after the deadline) is still recorded there, so paid work
    is never invisible (audit P1 late successful response).
    """
    url = url or API_URL
    timeout = REQUEST_TIMEOUT if timeout is None else timeout
    attempts = RETRY_ATTEMPTS if attempts is None else attempts
    rnd = rng or random
    acct = accounting if isinstance(accounting, dict) else None
    if acct is not None:
        acct.setdefault("attempts", 0)
        acct.setdefault("responses_received", 0)
        acct.setdefault("unaccepted_usage", {})
        acct.setdefault("notes", [])
    key = os.environ.get("TYPESAFE_API_KEY")
    if not key:
        raise RuntimeError("missing_TYPESAFE_API_KEY")
    headers = {"Authorization": "Bearer " + key, "Content-Type": "application/json"}
    validate_state(body.get("state", {}), body.get("questions", {}))
    payload = json.dumps(body, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode()
    attempt = 0
    last = "unknown"

    def note(code):
        if acct is not None and code not in acct["notes"]:
            acct["notes"].append(code)

    def bank(data):
        """Record the usage of a received-but-unaccepted response."""
        if acct is None:
            return
        for k, v in usage_of(data).items():
            acct["unaccepted_usage"][k] = acct["unaccepted_usage"].get(k, 0) + v

    while True:
        if deadline is not None and MONOTONIC() >= deadline:
            raise TransportError(f"deadline_exceeded_before_attempt:{last}")
        remaining = deadline - MONOTONIC() if deadline is not None else timeout
        if acct is not None:
            acct["attempts"] += 1
        status, headers_in, data = TRANSPORT(url, payload, headers, min(timeout, remaining))
        if acct is not None:
            acct["responses_received"] += 1
        late = deadline is not None and MONOTONIC() > deadline
        if 200 <= status < 300:
            try:
                parsed = json.loads(data.decode("utf-8") if isinstance(data, (bytes, bytearray)) else data)
            except (json.JSONDecodeError, UnicodeDecodeError) as e:
                if late:
                    note("late_response_unparseable")
                raise ValueError(f"invalid_json_response:{e}") from e
            if late:
                # The response is NOT accepted, but it was paid for: bank its usage.
                bank(parsed)
                note("late_response_usage_preserved")
                raise TransportError("deadline_exceeded_after_response")
            return parsed
        if late:
            raise TransportError("deadline_exceeded_after_response")
        last = f"http_{status}"
        attempt += 1
        if status not in RETRY_STATUS or attempt >= max(1, attempts):
            raise TransportError(f"{last}:attempts={attempt}")
        wait = _retry_after_seconds(headers_in)
        if wait is None:
            wait = min(RETRY_BASE_SECONDS * (2 ** (attempt - 1)), RETRY_MAX_SECONDS)
        wait += rnd.uniform(0, min(0.5, RETRY_BASE_SECONDS))  # jitter
        if deadline is not None and MONOTONIC() + wait > deadline:
            raise TransportError(f"deadline_exceeded_before_retry:{last}")
        SLEEP(wait)


def new_deadline(seconds=None):
    return MONOTONIC() + (WORKFLOW_DEADLINE_SECONDS if seconds is None else seconds)


# ------------------------------------------------------------- model drift
def drift_allowed():
    return os.environ.get("TYPESAFE_ALLOW_MODEL_DRIFT") == "1"


def model_drift(served):
    """served: iterable of model strings the API reported."""
    served = [str(s) if s else "missing" for s in (served or [None])]
    return sorted({s for s in served if s != MODEL or MODEL != PINNED_MODEL})


def apply_drift_gate(result, served, safe_decisions=("pass", "selected"), decision_key="decision",
                     mode=None, degrade_to="human_review"):
    """Degrade an accept-style decision when the served model is not the pinned one.

    Mode-aware: in winner mode the decision field carries an arbitrary candidate
    ID, so the gate degrades ANY value that is not already a terminal
    non-accepting status, regardless of the ID text. A candidate ID that happens
    to read `block` / `review` / `insufficient_coverage` can no longer bypass the
    gate (audit P1 drift bypass). `mode` defaults to `result["mode"]`.
    """
    drift = model_drift(served)
    if not drift:
        return result
    warnings = result.setdefault("warnings", [])
    result["model_drift"] = True
    result["model_drift_served"] = drift
    warnings.append("model_drift:" + ",".join(drift))
    if drift_allowed():
        warnings.append("model_drift_allowed_by_env")
        return result
    decision = result.get(decision_key)
    mode = mode if mode is not None else result.get("mode")
    if mode == "winner":
        # `decision` is a candidate ID here; only an explicit degraded status stays.
        degrade = decision != degrade_to
        if not degrade and result.get("winner_id") is not None:
            # Already non-actionable, but the winner is still withdrawn under drift.
            result["winner_id_degraded"] = True
            warnings.append("downgraded_for_model_drift")
    elif decision in safe_decisions:
        degrade = True
    else:
        degrade = decision not in ("human_review", "insufficient_coverage", "block", "review",
                                   "main_review")
    if degrade:
        result[decision_key] = degrade_to
        if result.get("winner_id") is not None:
            result["winner_id_degraded"] = True
        warnings.append("downgraded_for_model_drift")
    return result


# ------------------------------------------------------------ observability
def log_path(explicit=None):
    return Path(explicit or os.environ.get("TYPESAFE_DECISION_LOG",
                                           os.environ.get("TYPESAFE_ROUTER_LOG", DEFAULT_LOG)))


def new_decision_id():
    return f"{int(time.time())}-{secrets.token_hex(4)}"


def task_fingerprint(task):
    """HMAC when a key is configured (shared/multi-tenant), plain SHA-256 otherwise."""
    raw = str(task).encode("utf-8")
    key = os.environ.get("TYPESAFE_TASK_HMAC_KEY")
    if key:
        return "hmac-sha256:" + hmac.new(key.encode("utf-8"), raw, hashlib.sha256).hexdigest()
    return hashlib.sha256(raw).hexdigest()


def input_fingerprint(obj):
    try:
        raw = json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    except (TypeError, ValueError):
        raw = repr(obj).encode("utf-8", "replace")
    key = os.environ.get("TYPESAFE_TASK_HMAC_KEY")
    return ("hmac-sha256:" + hmac.new(key.encode(), raw, hashlib.sha256).hexdigest()
            if key else hashlib.sha256(raw).hexdigest())


MAX_LOG_BYTES = _cfg_num("TYPESAFE_MAX_LOG_BYTES", 5_000_000, int, 10_000, 1_000_000_000)
LOG_ROTATE_KEEP = _cfg_num("TYPESAFE_LOG_ROTATE_KEEP", 3, int, 1, 20)


def rotate_log(path, max_bytes=None, keep=None):
    """Rotate `path` to `path.1` (shifting older generations) when it grows too big.

    Best effort and never raises; returns the rotation code or None. Size-based
    rotation is the phase-1 scope: a time/date policy and an external sink are
    deliberately left to a later phase.
    """
    max_bytes = MAX_LOG_BYTES if max_bytes is None else max_bytes
    keep = LOG_ROTATE_KEEP if keep is None else keep
    try:
        p = Path(path)
        if not p.exists() or p.stat().st_size < max_bytes:
            return None
        for i in range(int(keep), 0, -1):
            src = p.with_name(p.name + f".{i}")
            if i == int(keep) and src.exists():
                src.unlink()
                continue
            if src.exists():
                src.rename(p.with_name(p.name + f".{i + 1}"))
        p.rename(p.with_name(p.name + ".1"))
        return "log_rotated:1"
    except OSError:
        return None


def log_sink(row, path=None):
    """The single audit-log sink.

    Replace this attribute (`ts_common.log_sink = fn`) to ship rows elsewhere;
    `write_log` calls it through the module attribute, so one seam covers every
    client. The default implementation appends JSONL to a 0600 file.
    """
    p = log_path(path)
    if os.environ.get("TYPESAFE_OFFLINE") == "1" and _is_production_log(p):
        # Hard guarantee: an offline/test run can never mutate the production log.
        return "offline_refuses_default_production_log"
    p.parent.mkdir(parents=True, exist_ok=True)
    rotated = rotate_log(p)
    line = (json.dumps(row, separators=(",", ":"), ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")
    fd = os.open(str(p), os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
    try:
        import fcntl
        fcntl.flock(fd, fcntl.LOCK_EX)
        while line:
            written = os.write(fd, line)
            if written <= 0:
                raise OSError("short_log_write")
            line = line[written:]
    finally:
        os.close(fd)
    try:
        os.chmod(str(p), 0o600)
    except OSError:
        pass
    return rotated


def _is_production_log(p):
    """True when `p` is the production log by path, symlink target OR inode.

    The inode check also covers a hardlink, which a pure `resolve()` comparison
    misses. `st_dev` is compared defensively: iSH/Alpine reports it
    inconsistently (0 for some mounts), so a matching inode with an unusable
    device id is treated as the same file rather than as a different one.

    Scope of the claim: this prevents an offline/test run from writing the
    production log through a path, symlink or hardlink. It is NOT a defence
    against a process that has direct write access to the file itself.
    """
    prod = Path(DEFAULT_LOG)
    try:
        if p.resolve() == prod.resolve():
            return True
    except OSError:
        pass
    try:
        a, b = p.stat(), prod.stat()
    except OSError:
        return False
    if a.st_ino != b.st_ino:
        return False
    if a.st_dev == b.st_dev:
        return True
    # Same inode but a mismatching device id: trust it only when at least one
    # device id is unusable (0) and the file really has more than one link.
    return (a.st_dev == 0 or b.st_dev == 0) and max(a.st_nlink, b.st_nlink) > 1


def write_log(row, path=None):
    """Append one JSONL row through `log_sink`. Never raises.

    Returns (decision_id, error) where error is None on success. The file is
    created 0600; a single short write under an advisory lock keeps concurrent
    appends from interleaving, and oversized logs are rotated first.
    """
    decision_id = row.get("decision_id") or new_decision_id()
    row = dict(row)
    row["decision_id"] = decision_id
    row.setdefault("event", "decision")
    row.setdefault("schema_version", SCHEMA_VERSION)
    row.setdefault("ts", int(time.time()))
    try:
        result = globals()["log_sink"](row, path)
        if isinstance(result, str) and result.startswith("offline_refuses"):
            return decision_id, result
        return decision_id, None
    except Exception as e:  # logging must never break a decision
        return decision_id, f"{type(e).__name__}:{str(e)[:120]}"


class JSONArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        print(json.dumps({"decision": "human_review", "error_type": "CLIUsageError",
                          "error": message, "schema_version": SCHEMA_VERSION,
                          "version": __version__, "advisory_only": True}))
        raise SystemExit(EXIT_USAGE)


def emit(payload, exc=None, stream=None, pretty=False):
    """Print the JSON contract and return the process exit code.

    Serialization is strict (`allow_nan=False`): a non-finite number can never
    leave as non-standard `NaN`/`Infinity` JSON. If it somehow reaches here, the
    document degrades to a fail-closed envelope instead of emitting bad JSON.
    """
    stream = stream or sys.stdout
    try:
        text = json.dumps(payload, ensure_ascii=False, indent=2 if pretty else None, allow_nan=False)
    except (ValueError, TypeError) as e:
        payload = {"decision": "human_review", "error_type": "NonSerializableResult",
                   "error": f"{type(e).__name__}:{str(e)[:120]}", "schema_version": SCHEMA_VERSION,
                   "version": __version__, "advisory_only": True, "warnings": ["failed_closed"]}
        text = json.dumps(payload, ensure_ascii=False, indent=2 if pretty else None)
        exc = exc or ValueError("non_serializable_result")
    stream.write(text + "\n")
    return EXIT_OK if exc is None else exit_code_for(exc)
