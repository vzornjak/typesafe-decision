#!/usr/bin/env python3
"""Single entry point for the whole test suite.

Runs, in order:
  1. py_compile over every shipped Python file (syntax gate)
  2. scripts/selftest.py        — 25 legacy behaviour-contract tests
  3. scripts/tests_phase1.py    — 119 audit regressions
  4. Phase 2 protocol contract tests
  5. fixture integrity          — per-file and aggregate SHA-256
  6. hygiene scans              — secrets and non-portable absolute paths

Everything is offline and self-contained. Exit 0 only when all stages pass.

    python3 tests/run_tests.py [--verbose]
"""
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SCRIPTS = os.path.join(ROOT, "scripts")
VERBOSE = "--verbose" in sys.argv

# Hygiene scan configuration. These patterns must not appear in tracked files.
SECRET_PATTERNS = [
    (r"sk-[A-Za-z0-9]{16,}", "openai-style api key"),
    (r"ghp_[A-Za-z0-9]{20,}", "github personal access token"),
    (r"github_pat_[A-Za-z0-9_]{20,}", "github fine-grained pat"),
    (r"AKIA[0-9A-Z]{16}", "aws access key id"),
    (r"-----BEGIN [A-Z ]*PRIVATE KEY-----", "private key block"),
    (r"eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}", "jwt"),
    (r"xox[abposr]-[A-Za-z0-9-]{10,}", "slack token"),
    (r"(?i)authorization\s*:\s*bearer\s+[A-Za-z0-9._-]{12,}", "hardcoded bearer header"),
]

# Absolute host paths that must not be *required* by code or tests.
# `/var/minis/shared/typesafe-decision/decisions.jsonl` is allowed exactly where
# it is documented as the overridable Minis default.
ALLOWED_DEFAULT_LOG = "/var/minis/shared/typesafe-decision/decisions.jsonl"
PATH_PATTERN = re.compile(r"/var/minis/[A-Za-z0-9._/-]*")

SKIP_DIRS = {".git", "__pycache__", ".github/.cache"}
TEXT_EXT = {".py", ".md", ".toml", ".yml", ".yaml", ".json", ".txt", ".cfg", ".ini", ""}


def iter_files():
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for name in filenames:
            p = os.path.join(dirpath, name)
            ext = os.path.splitext(name)[1]
            if ext.lower() in TEXT_EXT:
                yield p


def stage_compile():
    files = [p for p in iter_files() if p.endswith(".py")]
    r = subprocess.run([sys.executable, "-m", "py_compile", *files],
                       capture_output=True, text=True)
    return r.returncode == 0, {"files": len(files), "stderr": r.stderr[-800:]}


def _run_json(path, extra=()):
    env = dict(os.environ)
    env["TYPESAFE_OFFLINE"] = "1"
    env.pop("TYPESAFE_API_KEY", None)
    r = subprocess.run([sys.executable, path, *extra], capture_output=True,
                       text=True, env=env, timeout=1800)
    try:
        doc = json.loads(r.stdout)
    except Exception:
        return False, {"returncode": r.returncode, "stdout": r.stdout[-800:],
                       "stderr": r.stderr[-800:]}
    return r.returncode == 0 and doc.get("ok") is True, doc


def stage_selftest():
    return _run_json(os.path.join(SCRIPTS, "selftest.py"))


def stage_regressions():
    ok, doc = _run_json(os.path.join(SCRIPTS, "tests_phase1.py"))
    if not VERBOSE:
        doc = {k: v for k, v in doc.items() if k != "by_finding"}
    return ok, doc


def stage_fixtures():
    import hashlib
    base = os.path.join(HERE, "fixtures")
    manifest_path = os.path.join(base, "MANIFEST.sha256.json")
    if not os.path.exists(manifest_path):
        return False, {"error": "missing MANIFEST.sha256.json"}
    doc = json.load(open(manifest_path, encoding="utf-8"))
    agg = hashlib.sha256()
    bad = []
    for entry in doc["files"]:
        p = os.path.join(base, entry["name"])
        if not os.path.exists(p):
            bad.append({"name": entry["name"], "error": "missing"})
            continue
        got = hashlib.sha256(open(p, "rb").read()).hexdigest()
        if got != entry["sha256"]:
            bad.append({"name": entry["name"], "error": "hash mismatch"})
        agg.update((entry["name"] + ":" + got + "\n").encode())
    on_disk = sorted(n for n in os.listdir(base)
                     if n != "MANIFEST.sha256.json" and not n.startswith("."))
    declared = sorted(e["name"] for e in doc["files"])
    if on_disk != declared:
        bad.append({"error": "undeclared or missing fixture files",
                    "on_disk": on_disk, "declared": declared})
    agg_ok = agg.hexdigest() == doc["aggregate_sha256"]
    if not agg_ok:
        bad.append({"error": "aggregate hash mismatch"})
    prov = open(os.path.join(base, "provenance.txt"), encoding="utf-8").read()
    if "origin=synthetic" not in prov:
        bad.append({"error": "fixtures not declared synthetic"})
    return not bad, {"files": len(doc["files"]), "label": doc.get("manifest_label"),
                     "aggregate_ok": agg_ok, "problems": bad}


def stage_phase2_protocol():
    """Exercise protocol invariants; a draft benchmark is expected to remain unlocked."""
    ok, doc = _run_json(os.path.join(ROOT, "benchmarks", "phase2", "tests_protocol.py"))
    return ok, doc


def stage_scored_runner():
    return _run_json(os.path.join(ROOT, "benchmarks", "phase2", "tests_scored_runner.py"))


def stage_scoped_inputs():
    return _run_json(os.path.join(ROOT, "benchmarks", "phase2", "tests_scoped_inputs.py"))


def stage_output_seal():
    return _run_json(os.path.join(ROOT, "benchmarks", "phase2", "tests_output_seal.py"))


def stage_pre_unblind():
    return _run_json(os.path.join(ROOT, "benchmarks", "phase2", "tests_audit_unblind.py"))


def stage_main_anthropic():
    return _run_json(os.path.join(ROOT, "benchmarks", "phase2", "tests_main_anthropic.py"))


def stage_minis_relay():
    return _run_json(os.path.join(ROOT, "benchmarks", "phase2", "tests_relay.py"))


def stage_cost_model():
    return _run_json(os.path.join(ROOT, "benchmarks", "phase2", "tests_cost_model.py"))


def stage_secret_scan():
    hits = []
    for p in iter_files():
        rel = os.path.relpath(p, ROOT)
        if rel == os.path.join("tests", "run_tests.py"):
            continue  # this file defines the patterns
        try:
            text = open(p, encoding="utf-8", errors="ignore").read()
        except OSError:
            continue
        for pat, label in SECRET_PATTERNS:
            for m in re.finditer(pat, text):
                hits.append({"file": rel, "kind": label,
                             "at": text[:m.start()].count("\n") + 1})
    return not hits, {"hits": hits}


def stage_path_scan():
    """No tracked file may DEPEND on a host-specific absolute path.

    The documented, overridable Minis default log path is the only
    `/var/minis/...` string allowed, and only in files that also document the
    `TYPESAFE_DEFAULT_LOG` override.
    """
    problems = []
    for p in iter_files():
        rel = os.path.relpath(p, ROOT)
        if rel == os.path.join("tests", "run_tests.py"):
            continue
        try:
            text = open(p, encoding="utf-8", errors="ignore").read()
        except OSError:
            continue
        for m in PATH_PATTERN.finditer(text):
            found = m.group(0)
            line_no = text[:m.start()].count("\n") + 1
            if found == ALLOWED_DEFAULT_LOG and "TYPESAFE_DEFAULT_LOG" in text:
                continue
            if found.startswith("/var/minis/skills/typesafe-decision"):
                continue  # documented install location, not a code dependency
            if text[m.end():m.end() + 3] == "..." or found.endswith("..."):
                continue  # illustrative prose pattern, e.g. "/var/minis/..."
            problems.append({"file": rel, "line": line_no, "path": found})
    return not problems, {"problems": problems}


STAGES = [
    ("py_compile", stage_compile),
    ("selftest", stage_selftest),
    ("regressions", stage_regressions),
    ("phase2_protocol", stage_phase2_protocol),
    ("scored_runner", stage_scored_runner),
    ("scoped_inputs", stage_scoped_inputs),
    ("output_seal", stage_output_seal),
    ("pre_unblind", stage_pre_unblind),
    ("main_anthropic", stage_main_anthropic),
    ("minis_relay", stage_minis_relay),
    ("cost_model", stage_cost_model),
    ("fixture_integrity", stage_fixtures),
    ("secret_scan", stage_secret_scan),
    ("absolute_path_scan", stage_path_scan),
]


def main():
    report = {"ok": True, "stages": {}}
    for name, fn in STAGES:
        try:
            ok, detail = fn()
        except Exception as e:  # noqa: BLE001
            ok, detail = False, {"error": f"{type(e).__name__}: {e}"}
        report["stages"][name] = {"ok": ok, **({"detail": detail} if (not ok or VERBOSE) else
                                               {"summary": _summary(name, detail)})}
        if not ok:
            report["ok"] = False
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["ok"] else 1


def _summary(name, detail):
    if name == "regressions":
        return {k: detail.get(k) for k in ("tests", "unique_tests", "duplicates", "failures",
                                           "version", "schema_version")}
    if name == "selftest":
        return {k: detail.get(k) for k in ("tests", "version")}
    if name in ("phase2_protocol", "scored_runner", "scoped_inputs", "output_seal", "pre_unblind", "main_anthropic", "minis_relay", "cost_model"):
        return {k: detail.get(k) for k in ("tests", "failures")}
    if name == "fixture_integrity":
        return {"files": detail.get("files"), "label": detail.get("label")}
    if name == "py_compile":
        return {"files": detail.get("files")}
    return {}


if __name__ == "__main__":
    sys.exit(main())
