#!/usr/bin/env python3
"""Aggregate the advisory decision log. Read-only; never mutates the log."""
import argparse
import json
import os
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ts_common as tsc  # noqa: E402

LEGACY_SCHEMA = 0  # rows written before schema_version existed


def load(path):
    rows = []
    malformed = 0
    p = tsc.log_path(path)
    if p.exists():
        for line in p.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                malformed += 1
                continue
            if isinstance(row, dict):
                rows.append(row)
            else:
                malformed += 1
    return rows, malformed, p


def workflow_of(row):
    if row.get("workflow"):
        return str(row["workflow"])
    # Legacy rows (schema_version missing) were route-only.
    return "route"


def decision_of(row):
    if row.get("decision"):
        return str(row["decision"])
    return str((row.get("policy") or {}).get("recommended_executor", "unknown"))


def usage_input_tokens(row):
    usage = row.get("usage")
    if not isinstance(usage, dict):
        usage = (row.get("raw") or {}).get("usage") or {}
    value = usage.get("input_tokens") if isinstance(usage, dict) else 0
    return value if isinstance(value, (int, float)) else 0


def main(argv=None):
    p = argparse.ArgumentParser(description="Report on the advisory decision log")
    p.add_argument("--log-path", default=None)
    p.add_argument("--pretty", action="store_true", default=True)
    x = p.parse_args(argv)
    rows, malformed, path = load(x.log_path)
    decisions = [r for r in rows if r.get("event", "decision") == "decision"]
    outcomes = {r.get("decision_id"): r for r in rows if r.get("event") == "outcome"}
    schema_counts = Counter(r.get("schema_version", LEGACY_SCHEMA) for r in decisions)
    per_workflow = defaultdict(lambda: {"decisions": 0, "outcomes": 0, "input_tokens": 0, "latencies": [],
                                        "decision_counts": Counter(), "model_drift": 0, "warnings": Counter(),
                                        "api_calls": 0})
    matched = 0
    evaluated = 0
    success = Counter()
    escalated = 0
    for d in decisions:
        wf = workflow_of(d)
        agg = per_workflow[wf]
        agg["decisions"] += 1
        agg["decision_counts"][decision_of(d)] += 1
        agg["input_tokens"] += usage_input_tokens(d)
        agg["api_calls"] += d.get("api_calls", 1) if isinstance(d.get("api_calls", 1), int) else 0
        if isinstance(d.get("latency_ms"), (int, float)):
            agg["latencies"].append(d["latency_ms"])
        if d.get("model_drift"):
            agg["model_drift"] += 1
        for w in (d.get("warnings") or [])[:20]:
            agg["warnings"][str(w).split(":")[0]] += 1
        o = outcomes.get(d.get("decision_id"))
        if not o:
            continue
        agg["outcomes"] += 1
        if wf == "route":
            evaluated += 1
            matched += o.get("actual_executor") == decision_of(d)
            success[o.get("success", "unknown")] += 1
            escalated += bool(o.get("escalated"))
    total_tokens = sum(a["input_tokens"] for a in per_workflow.values())
    report = {
        "log_path": str(path),
        "log_exists": path.exists(),
        "malformed_lines": malformed,
        "schema_versions": {str(k): v for k, v in sorted(schema_counts.items(), key=lambda kv: str(kv[0]))},
        "legacy_rows_without_schema": schema_counts.get(LEGACY_SCHEMA, 0),
        "decisions": len(decisions),
        "by_workflow": {
            wf: {"decisions": a["decisions"], "with_outcome": a["outcomes"],
                 "decision_counts": dict(a["decision_counts"]), "api_calls": a["api_calls"],
                 "input_tokens": a["input_tokens"], "model_drift_rows": a["model_drift"],
                 "warning_kinds": dict(a["warnings"]),
                 "avg_latency_ms": round(sum(a["latencies"]) / len(a["latencies"]), 1) if a["latencies"] else None}
            for wf, a in sorted(per_workflow.items())},
        "route_agreement": {"with_outcome": evaluated,
                            "agreement_rate": round(matched / evaluated, 3) if evaluated else None,
                            "success": dict(success), "escalations": escalated},
        "input_tokens": total_tokens,
        "estimated_usd_at_0.042_per_mtok": round(total_tokens * tsc.JEV_USD_PER_MTOK_INPUT / 1_000_000, 8),
        "autonomy_readiness": {"minimum_decisions": 100, "enough_data": len(decisions) >= 100,
                               "note": "Agreement and success must be reviewed before enabling autonomy."},
    }
    print(json.dumps(report, indent=2 if x.pretty else None, ensure_ascii=False))
    return tsc.EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
