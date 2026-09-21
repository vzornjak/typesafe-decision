#!/usr/bin/env python3
"""Fail-closed Phase 2 validation, hashing, and blind-unblinding gates."""
import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
REPO = ROOT.parent.parent
CONFIG = ROOT / "config"
PUBLIC = ROOT / "public"
INPUT_LOCK = ROOT / "inputs.lock.json"
OUTPUT_LOCK_NAME = "outputs.lock.json"
GOLD_NAMES = {"gold", "gold.json", "gold.jsonl", "labels", "answer_key"}
GOLD_FIELDS = {
    "required_source_ids", "primary_source_ids", "supporting_source_ids",
    "support_spans", "known_contradictions", "authority_label", "source_type_label",
}
REQUIRED_CONFIGS = ["design.json", "execution.json", "decision-gates.json", "metadata-policy.json"]


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def load(path):
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def atomic(path, doc):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(doc, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def files_under(base, exclude=()):
    excluded = {Path(x).resolve() for x in exclude}
    return sorted(p for p in base.rglob("*") if p.is_file() and p.resolve() not in excluded and "__pycache__" not in p.parts)


def manifest(base, paths):
    rows = []
    for p in paths:
        b = p.read_bytes()
        rows.append({"path": p.relative_to(base).as_posix(), "bytes": len(b), "sha256": digest(b)})
    return rows


def duplicate(values):
    return len(values) != len(set(values))


def validate_task(doc, path):
    errors = []
    allowed_top = {"task_id", "language", "domain", "complexity", "query", "requirements", "candidates"}
    extra = set(doc) - allowed_top
    if extra: errors.append(f"{path}: extra top-level fields: {sorted(extra)}")
    tid = doc.get("task_id")
    if not isinstance(tid, str) or not re.fullmatch(r"p2-(dev|score)-(hr|en)-\d{2}", tid or ""):
        errors.append(f"{path}: invalid task_id")
    if doc.get("language") not in {"hr", "en"}: errors.append(f"{path}: invalid language")
    if doc.get("domain") not in {"software_technical", "public_policy_regulation", "science_health", "consumer_product"}:
        errors.append(f"{path}: invalid domain")
    if doc.get("complexity") not in {"moderate", "complex"}: errors.append(f"{path}: invalid complexity")
    if not isinstance(doc.get("query"), str) or len(doc["query"]) < 20: errors.append(f"{path}: query too short")
    reqs = doc.get("requirements")
    if not isinstance(reqs, list) or not 2 <= len(reqs) <= 6:
        errors.append(f"{path}: requirements must contain 2..6 rows")
        reqs = []
    rids = []
    for r in reqs:
        if not isinstance(r, dict) or set(r) != {"id", "text"}: errors.append(f"{path}: malformed requirement"); continue
        rids.append(r.get("id"))
        if not re.fullmatch(r"r\d{2}", str(r.get("id", ""))) or not isinstance(r.get("text"), str) or len(r["text"]) < 8:
            errors.append(f"{path}: invalid requirement")
    if duplicate(rids): errors.append(f"{path}: duplicate requirement id")
    candidates = doc.get("candidates")
    if not isinstance(candidates, list) or not 10 <= len(candidates) <= 16:
        errors.append(f"{path}: candidates must contain 10..16 rows")
        candidates = []
    cids = []
    allowed_c = {"candidate_id", "url", "title", "domain", "published_at_if_observable", "content", "content_chars"}
    required_c = {"candidate_id", "url", "title", "domain", "content", "content_chars"}
    for c in candidates:
        if not isinstance(c, dict) or set(c) - allowed_c or not required_c <= set(c): errors.append(f"{path}: malformed candidate"); continue
        cids.append(c.get("candidate_id"))
        if not re.fullmatch(r"c\d{2}", str(c.get("candidate_id", ""))): errors.append(f"{path}: invalid candidate id")
        if not str(c.get("url", "")).startswith("https://"): errors.append(f"{path}: candidate URL must use https")
        content = c.get("content")
        if not isinstance(content, str) or len(content) < 50 or c.get("content_chars") != len(content): errors.append(f"{path}: invalid content/content_chars")
        if isinstance(content, str) and "PENDING VERIFIED PUBLIC EXTRACT" in content:
            errors.append(f"{path}: candidate content is an unresolved placeholder")
    if duplicate(cids): errors.append(f"{path}: duplicate candidate id")
    return errors


def scan_gold(value, where="$", hits=None):
    hits = [] if hits is None else hits
    if isinstance(value, dict):
        for k, v in value.items():
            if k in GOLD_FIELDS or k.lower() in GOLD_NAMES: hits.append(f"{where}.{k}")
            scan_gold(v, f"{where}.{k}", hits)
    elif isinstance(value, list):
        for i, v in enumerate(value): scan_gold(v, f"{where}[{i}]", hits)
    return hits


def validate():
    errors = []
    for name in REQUIRED_CONFIGS:
        p = CONFIG / name
        if not p.exists(): errors.append(f"missing config/{name}")
        else:
            try: load(p)
            except Exception as e: errors.append(f"config/{name}: {type(e).__name__}: {e}")
    execution = load(CONFIG / "execution.json") if (CONFIG / "execution.json").exists() else {}
    incomplete = []
    def walk(v, key=""):
        if isinstance(v, dict):
            for k, x in v.items(): walk(x, f"{key}.{k}" if key else k)
        elif v is None and key not in {"main.seed", "pricing.main_cached_input_per_million"}:
            incomplete.append(key)
    walk(execution)
    if incomplete: errors.append("execution config incomplete: " + ", ".join(incomplete))
    tasks = []
    if PUBLIC.exists():
        tasks = sorted(p for p in PUBLIC.glob("*.json") if p.name != "MANIFEST.json")
    for p in tasks:
        try:
            doc = load(p); errors.extend(validate_task(doc, p.relative_to(REPO))); hits = scan_gold(doc)
            if hits: errors.append(f"{p.relative_to(REPO)}: gold fields present: {hits}")
        except Exception as e: errors.append(f"{p.relative_to(REPO)}: {type(e).__name__}: {e}")
    ids = []
    docs = []
    for p in tasks:
        try:
            doc = load(p); docs.append(doc); ids.append(doc.get("task_id"))
        except Exception: pass
    if duplicate(ids): errors.append("duplicate task_id across public tasks")
    design = load(CONFIG / "design.json") if (CONFIG / "design.json").exists() else {}
    expected = design.get("scored_tasks", 0) + design.get("development_tasks", 0)
    if len(tasks) != expected: errors.append(f"public task count {len(tasks)} != expected {expected}")
    scored = [d for d in docs if str(d.get("task_id", "")).startswith("p2-score-")]
    dev = [d for d in docs if str(d.get("task_id", "")).startswith("p2-dev-")]
    if len(scored) != design.get("scored_tasks", 0): errors.append(f"scored task count {len(scored)} != expected {design.get('scored_tasks', 0)}")
    if len(dev) != design.get("development_tasks", 0): errors.append(f"development task count {len(dev)} != expected {design.get('development_tasks', 0)}")
    for lang, n in design.get("languages", {}).items():
        got = sum(d.get("language") == lang for d in scored)
        if got != n: errors.append(f"scored language {lang} count {got} != expected {n}")
    for domain, n in design.get("domains", {}).items():
        got = sum(d.get("domain") == domain for d in scored)
        if got != n: errors.append(f"scored domain {domain} count {got} != expected {n}")
    moderate = sum(d.get("complexity") == "moderate" and 2 <= len(d.get("requirements", [])) <= 3 for d in scored)
    complex_n = sum(d.get("complexity") == "complex" and 4 <= len(d.get("requirements", [])) <= 6 for d in scored)
    if scored and moderate != design.get("complexity", {}).get("moderate_2_to_3_requirements"):
        errors.append(f"moderate scored stratum {moderate} incorrect")
    if scored and complex_n != design.get("complexity", {}).get("complex_4_to_6_requirements"):
        errors.append(f"complex scored stratum {complex_n} incorrect")
    roles = (ROOT / "ROLES.md").read_text(encoding="utf-8") if (ROOT / "ROLES.md").exists() else ""
    if "TBD" in roles: errors.append("ROLES.md still contains TBD")
    prompt_map = {"system_prompt_sha256": ROOT / "prompts" / "main-system.md", "user_prompt_template_sha256": ROOT / "prompts" / "main-user-template.md"}
    for key, path in prompt_map.items():
        if not path.exists() or execution.get("main", {}).get(key) != digest(path.read_bytes()): errors.append(f"prompt hash mismatch: {key}")
    return {"ok": not errors, "errors": errors, "public_tasks": len(tasks), "expected_tasks": expected}


def git_value(*args):
    r = subprocess.run(["git", "-C", str(REPO), *args], capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else None


def lock_inputs(args):
    if INPUT_LOCK.exists(): return {"ok": False, "errors": ["inputs.lock.json already exists; never overwrite a lock"]}
    report = validate()
    if not report["ok"]: return report
    tracked = [ROOT / "PREREGISTRATION.md", ROOT / "ROLES.md", ROOT / "DEVELOPMENT-RECORD.md", ROOT / "CORPUS-STATUS.md"] + [CONFIG / x for x in REQUIRED_CONFIGS]
    tracked += files_under(ROOT / "schemas") + files_under(ROOT / "prompts") + files_under(PUBLIC)
    tracked += files_under(ROOT / "builder-provenance")
    rows = manifest(ROOT, sorted(set(tracked)))
    doc = {
        "schema_version": 1, "kind": "phase2_input_lock", "created_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "actor": args.actor, "note": args.note, "git_commit": git_value("rev-parse", "HEAD"),
        "git_status_porcelain": git_value("status", "--porcelain"), "files": rows,
        "aggregate_sha256": digest(canonical(rows)), "validation": report,
    }
    if doc["git_status_porcelain"]: return {"ok": False, "errors": ["git worktree must be clean before lock"], "git_status": doc["git_status_porcelain"]}
    atomic(INPUT_LOCK, doc)
    return {"ok": True, "lock": str(INPUT_LOCK.relative_to(REPO)), "aggregate_sha256": doc["aggregate_sha256"], "files": len(rows)}


def verify_lock(lock_path, base):
    doc = load(lock_path); errors = []
    rows = []
    for row in doc.get("files", []):
        p = base / row["path"]
        if not p.exists(): errors.append(f"missing {row['path']}"); continue
        b = p.read_bytes(); got = digest(b)
        rows.append({"path": row["path"], "bytes": len(b), "sha256": got})
        if got != row["sha256"] or len(b) != row["bytes"]: errors.append(f"changed {row['path']}")
    if digest(canonical(rows)) != doc.get("aggregate_sha256"): errors.append("aggregate hash mismatch")
    return errors


def expected_output_names():
    design = load(CONFIG / "design.json")
    task_ids = [load(p)["task_id"] for p in sorted(PUBLIC.glob("*.json")) if load(p)["task_id"].startswith("p2-score-")]
    names = []
    for tid in task_ids:
        names.append(f"{tid}__A_no_rank__rep0.json")
        for arm in ("B_winner_top8", "C_shortlist_default", "D_shortlist_tuned"):
            for rep in range(1, 4): names.append(f"{tid}__{arm}__rep{rep}.json")
    return sorted(names)


def lock_outputs(args):
    out = Path(args.outputs).resolve(); lock = out / OUTPUT_LOCK_NAME
    if not INPUT_LOCK.exists(): return {"ok": False, "errors": ["missing inputs.lock.json"]}
    if not out.is_dir(): return {"ok": False, "errors": ["outputs directory missing"]}
    if lock.exists(): return {"ok": False, "errors": ["output lock already exists"]}
    input_errors = verify_lock(INPUT_LOCK, ROOT)
    if input_errors: return {"ok": False, "errors": input_errors}
    paths = files_under(out, exclude=[lock])
    actual = sorted(p.relative_to(out).as_posix() for p in paths)
    expected = expected_output_names()
    if actual != expected:
        return {"ok": False, "errors": ["output set does not match preregistered 160 artifacts"],
                "missing": sorted(set(expected) - set(actual)), "unexpected": sorted(set(actual) - set(expected))}
    rows = manifest(out, paths)
    if not rows: return {"ok": False, "errors": ["no output files"]}
    doc = {"schema_version": 1, "kind": "phase2_output_lock", "created_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
           "actor": args.actor, "input_lock_sha256": digest(INPUT_LOCK.read_bytes()), "files": rows,
           "aggregate_sha256": digest(canonical(rows))}
    atomic(lock, doc)
    return {"ok": True, "lock": str(lock), "aggregate_sha256": doc["aggregate_sha256"], "files": len(rows)}


def audit_pre_unblind(args):
    out = Path(args.outputs).resolve(); lock = out / OUTPUT_LOCK_NAME; errors = []
    if not INPUT_LOCK.exists(): errors.append("missing inputs.lock.json")
    else: errors.extend(verify_lock(INPUT_LOCK, ROOT))
    if not lock.exists(): errors.append("missing outputs.lock.json")
    else: errors.extend(verify_lock(lock, out))
    for p in files_under(PUBLIC):
        if p.suffix.lower() == ".json":
            try:
                hits = scan_gold(load(p))
                if hits: errors.append(f"gold fields in {p.relative_to(REPO)}: {hits}")
            except Exception as e: errors.append(f"cannot inspect {p}: {e}")
        if p.name.lower() in GOLD_NAMES or "gold" in p.name.lower(): errors.append(f"gold-like filename in public input: {p.name}")
    if INPUT_LOCK.exists() and lock.exists():
        inp = dt.datetime.fromisoformat(load(INPUT_LOCK)["created_at_utc"])
        out_time = dt.datetime.fromisoformat(load(lock)["created_at_utc"])
        if out_time <= inp: errors.append("output lock does not postdate input lock")
    return {"ok": not errors, "decision": "unblind_allowed" if not errors else "unblind_forbidden", "errors": errors}


def verify(args):
    if args.kind == "inputs":
        if not INPUT_LOCK.exists(): return {"ok": False, "errors": ["missing inputs.lock.json"]}
        errors = verify_lock(INPUT_LOCK, ROOT)
    else:
        out = Path(args.outputs).resolve(); lock = out / OUTPUT_LOCK_NAME
        if not lock.exists(): return {"ok": False, "errors": ["missing outputs.lock.json"]}
        errors = verify_lock(lock, out)
    return {"ok": not errors, "errors": errors}


def parser():
    p = argparse.ArgumentParser(description=__doc__); sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("validate")
    a = sub.add_parser("lock-inputs"); a.add_argument("--actor", required=True); a.add_argument("--note", default="")
    a = sub.add_parser("lock-outputs"); a.add_argument("--outputs", required=True); a.add_argument("--actor", required=True)
    a = sub.add_parser("audit-pre-unblind"); a.add_argument("--outputs", required=True)
    a = sub.add_parser("verify"); a.add_argument("kind", choices=["inputs", "outputs"]); a.add_argument("--outputs")
    return p


def main():
    args = parser().parse_args()
    try:
        if args.cmd == "validate": result = validate()
        elif args.cmd == "lock-inputs": result = lock_inputs(args)
        elif args.cmd == "lock-outputs": result = lock_outputs(args)
        elif args.cmd == "audit-pre-unblind": result = audit_pre_unblind(args)
        else:
            if args.kind == "outputs" and not args.outputs: result = {"ok": False, "errors": ["--outputs required"]}
            else: result = verify(args)
    except Exception as e:
        result = {"ok": False, "errors": [f"{type(e).__name__}: {e}"]}
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
