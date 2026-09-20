#!/usr/bin/env python3
"""Advisory TypeSafe task router. Never authorizes or executes actions.

Contract (v2.4.0): stdout is always a single valid JSON document and expected
uncertainty exits 0. Log failures are non-fatal and reported in `meta.log_error`.
"""
import argparse
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ts_common as tsc  # noqa: E402

API = tsc.API_URL
MODEL = tsc.MODEL
POLICY_VERSION = tsc.__version__
CONFIDENCE_THRESHOLD = tsc._cfg_num("TYPESAFE_ROUTER_CONFIDENCE", 0.60, float, 0.0, 1.0)
PARALLEL_THRESHOLD = tsc._cfg_num("TYPESAFE_ROUTER_PARALLEL", 0.85, float, 0.0, 1.0)


def _reject_constant(name):
    """json.load hook: refuse the non-standard NaN/Infinity literals outright."""
    raise ValueError(f"non_finite_json_literal:{name}")


def reload_config():
    """Validate deployment configuration inside the protected entrypoint.

    Router-specific thresholds are parsed here too, so a malformed
    TYPESAFE_ROUTER_CONFIDENCE becomes one fail-closed JSON document instead of
    an import-time traceback (audit P1 config/import path).
    """
    global API, MODEL, CONFIDENCE_THRESHOLD, PARALLEL_THRESHOLD, LOG
    tsc.load_config()
    del tsc.CONFIG_ERRORS[:]
    CONFIDENCE_THRESHOLD = tsc._cfg_num("TYPESAFE_ROUTER_CONFIDENCE", 0.60, float, 0.0, 1.0)
    PARALLEL_THRESHOLD = tsc._cfg_num("TYPESAFE_ROUTER_PARALLEL", 0.85, float, 0.0, 1.0)
    tsc._cfg_num("TYPESAFE_ROUTER_TIMEOUT", 20.0, float, 0.1, 3600.0)
    errors = tsc.config_errors()
    if errors:
        raise tsc.ConfigError("invalid_configuration:" + ",".join(errors))
    API = tsc.API_URL
    MODEL = tsc.MODEL
    LOG = tsc.log_path()
    return True

QUESTIONS = {
  "executor": {"type": "choice", "instructions": {
    "question": "Select the single best executor for the task in `task`, considering `context` only when provided.",
    "rules": ["Prefer direct execution when delegation adds little value.",
              "Judge required work, not topic prestige.",
              "Do not assume an executor can ask the user questions mid-run."]},
    "criteria": {
      "main": "The main assistant should do it directly: short work; one or two tool calls; conversation nuance; user confirmation needed; or delegation overhead exceeds benefit.",
      "sub": "A separate lightweight agent should do it: mechanical, clearly bounded, low-risk, and easy to verify at a glance, such as collection, file conversion, or a short summary.",
      "general": "A general tool-using agent should do it: open-ended exploration requiring many rounds across web pages, files, repositories, or trial and error, but not unusually deep or high-stakes reasoning.",
      "max": "The strongest agent should do it: complex architecture, deep multi-step reasoning, difficult programming or verification, substantial ambiguity, or errors would be costly."
    }},
  "delegation_value": {"type": "noul", "instructions": "Delegating this task to a separate agent provides material benefit over the main assistant doing it directly."},
  "parallelizable": {"type": "noul", "instructions": "This task has at least two independent substantial branches that can run concurrently without one branch needing another branch's result."},
  "complexity": {"type": "score", "instructions": "Rate the reasoning and execution complexity required to complete the task correctly.", "criteria": ["Simple and mechanical", "Several routine steps", "Open-ended multi-step investigation", "Deep reasoning, architecture, or difficult implementation"]},
  "consequence": {"type": "score", "instructions": "Rate the consequence of an incorrect or inadequately verified result.", "criteria": ["Trivial and readily reversible", "Moderate inconvenience", "Could damage data, configuration, privacy, security, service availability, or incur meaningful cost", "High-impact, safety-critical, or difficult to reverse"]}
}


LOG = tsc.log_path()  # snapshot for backward compatibility; writes resolve the env at call time
# Fixed reason vocabulary: nothing else may enter the audit log.
REASON_CODES = ("jev_recommendation", "jev_recommends_direct", "low_route_confidence",
                "explicit_user_choice", "confirmation_required", "local_bounded_mechanical_rule",
                "model_drift", "typesafe_unavailable", "invalid_configuration", "other")


def log_path():
    """Resolved lazily so tests and callers can retarget the log via env."""
    return tsc.log_path()


def deterministic_gate(context):
    """Apply only caller-supplied, trusted control metadata.

    Never infer permission or explicit choice from untrusted task text. The caller
    must set these fields in JSON context when it actually has that knowledge.
    """
    if not isinstance(context, dict):
        return None
    explicit = context.get("explicit_executor")
    if isinstance(explicit, str) and explicit in {"main", "sub", "general", "max"}:
        return explicit, "explicit_user_choice"
    if context.get("confirmation_required") and not context.get("user_authorized"):
        return "main_review", "confirmation_required"
    # Jev had 0% recall for `sub` on the real-request holdout. The caller may
    # provide this trusted semantic fact only after locally establishing that
    # the task is mechanical, bounded, low-risk, and glance-verifiable. We do
    # not infer it from task keywords, and it never bypasses confirmation.
    if context.get("bounded_mechanical_task") is True:
        return "sub", "local_bounded_mechanical_rule"
    return None


def normalize_context(context):
    """Return (gate_context, api_context_string).

    Any shape is accepted: dict -> trusted metadata + `summary`; str -> plain
    textual context; anything else -> ignored, never crashes.
    """
    if isinstance(context, dict):
        return context, str(context.get("summary", "") or "").strip()
    if isinstance(context, str):
        return None, context.strip()
    return None, ""


def fallback(reason, latency=0):
    return {"model": MODEL, "raw": None,
            "policy": {"version": POLICY_VERSION, "recommended_executor": "main_review",
                       "parallel_recommended": False, "reason": "typesafe_unavailable", "advisory_only": True},
            "meta": {"latency_ms": latency, "error_type": reason}}


def apply_policy(data, latency, gate=None):
    # Strict envelope validation before ANY attribute access (audit P1).
    answers, usage, served_model = tsc.validate_envelope(data)
    a = answers
    route = a.get("executor")
    if not isinstance(route, dict):
        raise ValueError("api_answer_not_an_object:executor")
    raw_choice = route.get("choice")
    if not isinstance(raw_choice, str):
        raise ValueError("executor_choice_must_be_string")
    for key in ("delegation_value", "parallelizable", "complexity", "consequence"):
        if not isinstance(a.get(key), dict):
            raise ValueError(f"api_answer_not_an_object:{key}")
    conf = float(route["confidence"])
    delegate = float(a["delegation_value"]["noul"])
    parallel = float(a["parallelizable"]["noul"])
    complexity = float(a["complexity"]["score"])
    consequence = float(a["consequence"]["score"])
    for name, value, hi in (("confidence", conf, 1), ("delegation_value", delegate, 1),
                            ("parallelizable", parallel, 1), ("complexity", complexity, 3),
                            ("consequence", consequence, 3)):
        if not math.isfinite(value) or not 0 <= value <= hi:
            raise ValueError(f"invalid_route_score:{name}")
    route = {"choice": raw_choice, "confidence": conf}
    choice = raw_choice
    reason = "jev_recommendation"
    warnings = []
    # Choice is the only Jev judgment that controls executor selection. Separate
    # Noul/Score calls are telemetry because cross-question invariants are not
    # guaranteed (TypeSafe "jaggedness"). Risk never grants permission.
    if gate:
        choice, reason = gate
    elif conf < CONFIDENCE_THRESHOLD:
        # The real-request holdout showed that low-confidence `main` choices are
        # no safer than other labels. Apply the same abstention rule to every
        # Jev executor choice; deterministic gates above still take precedence.
        choice = "main_review"
        reason = "low_route_confidence"
    elif raw_choice == "main":
        reason = "jev_recommends_direct"
    risk_review_recommended = consequence >= 2.0
    if raw_choice not in ("main", "sub", "general", "max"):
        raise ValueError("unknown_executor_choice")
    served = served_model if served_model is not None else str(data.get("model"))
    drift = tsc.model_drift([served])
    if drift:
        warnings.append("model_drift:" + ",".join(drift))
        if tsc.drift_allowed():
            warnings.append("model_drift_allowed_by_env")
        elif gate:
            # A deterministic gate is authoritative; drift is still surfaced.
            warnings.append("model_drift_under_deterministic_gate")
        else:
            if choice != "main_review":
                reason = "model_drift"
            warnings.append("downgraded_for_model_drift")
            choice = "main_review"
    out = {"model": served,
           "raw": {"executor": route, "delegation_value": delegate, "parallelizable": parallel,
                   "complexity": complexity, "consequence": consequence,
                   "usage": tsc.finite_numbers(usage)},
           "policy": {"version": POLICY_VERSION, "recommended_executor": choice,
                      "parallel_recommended": parallel >= PARALLEL_THRESHOLD and choice not in ("main", "main_review"),
                      "risk_review_recommended": risk_review_recommended, "reason": reason, "advisory_only": True},
           "meta": {"latency_ms": latency, "warnings": warnings}}
    if drift:
        out["meta"]["model_drift"] = True
    return out


def write_log(out, task, path=None):
    """Append one content-free row. Returns (decision_id, error); never raises.

    Only fixed-vocabulary values are logged: the recommended executor is one of
    the known statuses, warnings are reduced to structured codes, and the raw
    Jev telemetry is reduced to finite numbers (audit P1 log content).
    """
    policy = out["policy"]
    decision, opaque = tsc.sanitize_decision(policy.get("recommended_executor"))
    raw = out.get("raw") or {}
    telemetry = {k: raw.get(k) for k in ("delegation_value", "parallelizable", "complexity", "consequence")
                 if isinstance(raw.get(k), (int, float)) and not isinstance(raw.get(k), bool)}
    executor = raw.get("executor") if isinstance(raw.get("executor"), dict) else {}
    safe_choice = executor.get("choice") if executor.get("choice") in tsc.STATUS_DECISIONS else None
    confidence = executor.get("confidence")
    row = {"event": "decision", "schema_version": tsc.SCHEMA_VERSION, "workflow": "route",
           "version": POLICY_VERSION, "policy_version": POLICY_VERSION,
           "decision_id": out["meta"].get("decision_id"), "task_sha256": tsc.task_fingerprint(task),
           "model_requested": MODEL, "model": str(out.get("model"))[:64] if out.get("model") else None,
           "models_served": [str(out["model"])[:64]] if out.get("raw") else [],
           "model_drift": bool(out["meta"].get("model_drift")), "decision": decision,
           "policy": {"version": policy.get("version"),
                      "recommended_executor": decision,
                      "parallel_recommended": bool(policy.get("parallel_recommended")),
                      "risk_review_recommended": bool(policy.get("risk_review_recommended")),
                      "reason": policy.get("reason") if policy.get("reason") in REASON_CODES else "other",
                      "advisory_only": True},
           "raw": {"executor_choice": safe_choice,
                   "executor_confidence": confidence if isinstance(confidence, (int, float))
                   and not isinstance(confidence, bool) and math.isfinite(confidence) else None,
                   **telemetry} if out.get("raw") else None,
           "latency_ms": out["meta"]["latency_ms"],
           "api_calls": out["meta"].get("api_calls", 1 if out.get("raw") else 0),
           "usage": tsc.finite_numbers(raw.get("usage") or {}),
           "warnings": tsc.sanitize_warnings(out["meta"].get("warnings")),
           "warnings_total": len(out["meta"].get("warnings") or [])}
    if opaque is not None:
        row["decision_ref"] = opaque
    if out["meta"].get("error_type"):
        row["error_type"] = str(out["meta"]["error_type"])[:64]
    return tsc.write_log(row, path)


def gate_only(gate, latency=0):
    """Deterministic gate result without spending an API call."""
    choice, reason = gate
    return {"model": MODEL, "raw": None,
            "policy": {"version": POLICY_VERSION, "recommended_executor": choice,
                       "parallel_recommended": False, "risk_review_recommended": False,
                       "reason": reason, "advisory_only": True},
            "meta": {"latency_ms": latency, "api_calls": 0, "warnings": ["deterministic_gate_no_api_call"]}}


def run(task, context, deadline=None):
    """Perform one routing decision. Returns the output document."""
    gate = deterministic_gate(context)
    # A deterministic gate is authoritative, so no paid call is needed. Set
    # TYPESAFE_ROUTE_GATE_TELEMETRY=1 to still collect Jev telemetry.
    if gate and os.environ.get("TYPESAFE_ROUTE_GATE_TELEMETRY") != "1":
        return gate_only(gate)
    # Only compact textual context is sent externally. Trusted control metadata
    # is consumed locally and is never treated as model-readable authorization.
    _, api_context = normalize_context(context)
    if not os.environ.get("TYPESAFE_API_KEY"):
        out = fallback("missing_TYPESAFE_API_KEY")
        if gate:
            out["policy"]["recommended_executor"], out["policy"]["reason"] = gate
        return out
    body = {"model": MODEL, "state": {"task": task, "context": api_context}, "questions": QUESTIONS}
    start = tsc.MONOTONIC()
    try:
        data = tsc.post_json(body, url=API, timeout=float(os.environ.get("TYPESAFE_ROUTER_TIMEOUT", "20")),
                             deadline=deadline if deadline is not None else tsc.new_deadline())
        return apply_policy(data, round((tsc.MONOTONIC() - start) * 1000), gate)
    except tsc.EXPECTED_ERRORS + (tsc.TransportError,) as e:
        out = fallback(type(e).__name__, round((tsc.MONOTONIC() - start) * 1000))
        if gate:
            out["policy"]["recommended_executor"], out["policy"]["reason"] = gate
        return out


def main(argv=None):
    exc = None
    out = None
    pretty = False
    try:
        p = tsc.JSONArgumentParser(description="Advisory TypeSafe task router")
        p.add_argument("--task")
        p.add_argument("--context", default="")
        p.add_argument("--stdin-json", action="store_true")
        p.add_argument("--no-log", dest="log", action="store_false", default=True)
        p.add_argument("--log-path", default=None)
        p.add_argument("--pretty", action="store_true")
        x = p.parse_args(argv)
        pretty = x.pretty
        # Configuration is parsed INSIDE the boundary: a malformed env var is a
        # fail-closed JSON document, never a traceback (audit P1 config path).
        reload_config()
        if x.stdin_json:
            obj = json.load(sys.stdin, parse_constant=_reject_constant)
            if not isinstance(obj, dict):
                raise ValueError("stdin JSON must be an object")
            tsc.assert_finite(obj, "input")
            task = obj.get("task", "")
            if not isinstance(task, str):
                raise ValueError("task must be a string")
            task = task.strip()
            context = obj.get("context", "")
        else:
            task = (x.task or "").strip()
            context = x.context
        if not task:
            raise ValueError("task is required")
        out = run(task, context)
        out["meta"]["decision_id"] = tsc.new_decision_id()
        if x.log:
            decision_id, log_error = write_log(out, task, x.log_path)
            out["meta"]["decision_id"] = decision_id
            if log_error:
                out["meta"]["log_error"] = log_error
    except SystemExit as e:  # argparse usage error: keep the documented code
        return tsc.EXIT_USAGE if e.code else tsc.EXIT_OK
    except Exception as e:  # noqa: BLE001 - global boundary, always emit valid JSON
        exc = e
        reason = "invalid_configuration" if isinstance(e, tsc.ConfigError) else type(e).__name__
        out = fallback(reason)
        out["meta"]["error"] = str(e)[:240]
        out["meta"]["failed_closed"] = True
        if isinstance(e, tsc.ConfigError):
            out["policy"]["reason"] = "invalid_configuration"
            out["meta"]["config_errors"] = tsc.config_errors()
    out.update({"workflow": "route", "version": POLICY_VERSION, "schema_version": tsc.SCHEMA_VERSION})
    out["meta"].setdefault("decision_id", tsc.new_decision_id())
    return tsc.emit(out, exc, pretty=pretty)


if __name__ == "__main__":
    sys.exit(main())
