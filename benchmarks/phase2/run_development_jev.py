#!/usr/bin/env python3
"""Run Jev only on synthetic development tasks; no gold and no MAIN calls."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent.parent
SCRIPTS = REPO / "scripts"
sys.path.insert(0, str(SCRIPTS))
import decision_workflows as dw
import ts_common as tsc

OUT = ROOT / "development" / "jev-outputs"
CONFIG = ROOT / "config" / "design.json"


def seed(task_id, rep):
    raw = f"phase2-v1-candidate-order:{task_id}:development:{rep}".encode()
    return int.from_bytes(hashlib.sha256(raw).digest()[:8], "big")


def shuffled(rows, n):
    import random
    x = list(rows); random.Random(n).shuffle(x); return x


def rank_input(task):
    return {
        "mode": "shortlist", "query": task["query"], "requirements": task["requirements"],
        "candidates": [{"id": c["candidate_id"], "url": c["url"], "title": c["title"],
                        "domain": c["domain"], "text": c["content"]} for c in task["candidates"]],
        "selection": json.load(open(CONFIG, encoding="utf-8"))["arms"]["C_shortlist_default"]["selection"],
    }


def main():
    if os.environ.get("TYPESAFE_OFFLINE") == "1": raise SystemExit("development Jev runner requires live mode")
    if not os.environ.get("TYPESAFE_API_KEY"): raise SystemExit("TYPESAFE_API_KEY is missing")
    OUT.mkdir(parents=True, exist_ok=True)
    tasks = sorted((ROOT / "public").glob("p2-dev-*.json"))
    if len(tasks) != 4: raise SystemExit(f"expected 4 development tasks, got {len(tasks)}")
    summary = []
    for path in tasks:
        task = json.load(open(path, encoding="utf-8"))
        for rep in range(1, 4):
            inp = rank_input(task); inp["candidates"] = shuffled(inp["candidates"], seed(task["task_id"], rep))
            started = time.time(); result = dw.rank(inp); elapsed = round((time.time() - started) * 1000)
            artifact = {"task_id": task["task_id"], "repetition": rep, "candidate_order": [c["id"] for c in inp["candidates"]],
                        "input_sha256": hashlib.sha256(json.dumps(inp, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
                        "elapsed_ms": elapsed, "result": result}
            out = OUT / f"{task['task_id']}__rep{rep}.json"
            out.write_text(json.dumps(artifact, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            summary.append({"task_id": task["task_id"], "rep": rep, "decision": result.get("decision"),
                            "selected": result.get("selected_ids"), "calls": result.get("api_calls"), "usage": result.get("usage")})
            print(json.dumps(summary[-1], ensure_ascii=False), flush=True)
    manifest = []
    for p in sorted(OUT.glob("*.json")):
        b = p.read_bytes(); manifest.append({"path": p.name, "bytes": len(b), "sha256": hashlib.sha256(b).hexdigest()})
    (OUT / "MANIFEST.json").write_text(json.dumps({"kind": "development_jev_outputs", "model_requested": tsc.MODEL,
        "files": manifest, "aggregate_sha256": hashlib.sha256(json.dumps(manifest,sort_keys=True,separators=(",", ":")).encode()).hexdigest()}, indent=2) + "\n")
    print(json.dumps({"ok": True, "runs": len(summary), "manifest_files": len(manifest)}))


if __name__ == "__main__": main()
