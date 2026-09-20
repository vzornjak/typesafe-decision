#!/usr/bin/env python3
"""Optional pytest adapter.

The canonical entry point is `python3 tests/run_tests.py`, which needs no
third-party packages. This thin wrapper lets `pytest tests/` run the same
stages when pytest happens to be installed. It adds no assertions of its own —
it delegates to the real suite so there is exactly one source of truth.
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def _stage_report():
    r = subprocess.run([sys.executable, os.path.join(HERE, "run_tests.py"), "--verbose"],
                       capture_output=True, text=True, timeout=3600)
    assert r.stdout.strip(), f"run_tests.py produced no output: {r.stderr[-2000:]}"
    return json.loads(r.stdout)


_REPORT = None


def _report():
    global _REPORT
    if _REPORT is None:
        _REPORT = _stage_report()
    return _REPORT


def _check(stage):
    rep = _report()
    st = rep["stages"][stage]
    assert st["ok"], json.dumps(st.get("detail", st), indent=2)[:4000]


def test_py_compile():
    _check("py_compile")


def test_selftest():
    _check("selftest")
    detail = _report()["stages"]["selftest"]["detail"]
    assert detail["tests"] == 25, detail


def test_regressions():
    _check("regressions")
    detail = _report()["stages"]["regressions"]["detail"]
    assert detail["failures"] == 0, detail
    assert detail["duplicates"] == 0, detail
    assert detail["unique_tests"] == detail["tests"] == 119, detail


def test_fixture_integrity():
    _check("fixture_integrity")


def test_no_secrets():
    _check("secret_scan")


def test_no_absolute_paths():
    _check("absolute_path_scan")
