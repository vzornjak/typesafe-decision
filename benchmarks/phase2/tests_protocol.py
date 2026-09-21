#!/usr/bin/env python3
"""Offline contract tests for the Phase 2 preregistration/locking utility."""
import importlib.util
import json
from pathlib import Path
import tempfile

TOOL = Path(__file__).resolve().parent / "tools" / "phase2.py"
spec = importlib.util.spec_from_file_location("phase2_tool", TOOL)
p2 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p2)

checks = []

def check(name, condition):
    checks.append({"name": name, "ok": bool(condition)})
    if not condition:
        raise AssertionError(name)


def task():
    text = "Synthetic candidate content for an offline protocol test. " * 2
    return {
        "task_id": "p2-dev-en-01", "language": "en", "domain": "software_technical",
        "complexity": "moderate", "query": "Compare two documented technical approaches and explain tradeoffs.",
        "requirements": [{"id": "r01", "text": "Explain approach one"}, {"id": "r02", "text": "Explain approach two"}],
        "candidates": [{"candidate_id": f"c{i:02d}", "url": f"https://source{i}.test/doc", "title": f"Source {i}",
                        "domain": f"source{i}.test", "content": text, "content_chars": len(text)} for i in range(1, 11)]
    }


def main():
    good = task()
    check("valid public task", p2.validate_task(good, "synthetic") == [])
    leaked = json.loads(json.dumps(good)); leaked["required_source_ids"] = ["c01"]
    check("extra gold top-level rejected", any("extra top-level" in e for e in p2.validate_task(leaked, "synthetic")))
    check("recursive gold scan", p2.scan_gold({"nested": [{"support_spans": []}]}) == ["$.nested[0].support_spans"])
    bad_chars = json.loads(json.dumps(good)); bad_chars["candidates"][0]["content_chars"] += 1
    check("content length mismatch rejected", any("content/content_chars" in e for e in p2.validate_task(bad_chars, "synthetic")))
    placeholder = json.loads(json.dumps(good)); placeholder["candidates"][0]["content"] = "PENDING VERIFIED PUBLIC EXTRACT " + "x" * 60; placeholder["candidates"][0]["content_chars"] = len(placeholder["candidates"][0]["content"])
    check("unresolved scored placeholder rejected", any("unresolved placeholder" in e for e in p2.validate_task(placeholder, "synthetic")))
    duplicate = json.loads(json.dumps(good)); duplicate["requirements"][1]["id"] = "r01"
    check("duplicate requirements rejected", any("duplicate requirement" in e for e in p2.validate_task(duplicate, "synthetic")))
    rows = [{"path": "a", "bytes": 1, "sha256": p2.digest(b"x")}]
    check("canonical digest deterministic", p2.digest(p2.canonical(rows)) == p2.digest(p2.canonical(list(rows))))
    with tempfile.TemporaryDirectory() as td:
        base = Path(td); (base / "a").write_bytes(b"x")
        lock = base / "lock.json"
        p2.atomic(lock, {"files": rows, "aggregate_sha256": p2.digest(p2.canonical(rows))})
        check("valid lock verifies", p2.verify_lock(lock, base) == [])
        (base / "a").write_bytes(b"y")
        check("mutated file breaks lock", bool(p2.verify_lock(lock, base)))
    ready = p2.validate()
    check("complete local runner inputs validate before lock", ready["ok"] and ready["public_tasks"] == 20)
    check("input lock has not been created prematurely", not p2.INPUT_LOCK.exists())
    saved_public = p2.PUBLIC
    saved_runner = p2.RUNNER_INPUTS
    saved_config = p2.CONFIG
    with tempfile.TemporaryDirectory() as td:
        base = Path(td); pub = base / "public"; cfg = base / "config"; pub.mkdir(); cfg.mkdir()
        (cfg / "design.json").write_text(json.dumps({"scored_tasks": 1}), encoding="utf-8")
        scored = task(); scored["task_id"] = "p2-score-en-01"
        (pub / "p2-score-en-01.json").write_text(json.dumps(scored), encoding="utf-8")
        p2.PUBLIC = pub; p2.RUNNER_INPUTS = pub; p2.CONFIG = cfg
        names = p2.expected_output_names()
        check("output schedule has ten artifacts per scored task", len(names) == 10)
        check("output schedule has one baseline artifact", sum("A_no_rank" in n for n in names) == 1)
        check("output schedule has three repetitions per model arm", all(sum(arm in n for n in names) == 3 for arm in ("B_winner_top8", "C_shortlist_default", "D_shortlist_tuned")))
        p2.PUBLIC = saved_public; p2.RUNNER_INPUTS = saved_runner; p2.CONFIG = saved_config
    result = {"ok": all(x["ok"] for x in checks), "tests": len(checks), "failures": [x for x in checks if not x["ok"]]}
    print(json.dumps(result, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
