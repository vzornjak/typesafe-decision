#!/usr/bin/env python3
"""Phase 1 regression suite: one or more tests per audit finding (P0-1..P0-6, P1-1..P1-9).

Fully hermetic and self-contained. Every test either uses pure local functions
or the offline replay/stub harness over the SYNTHETIC fixtures in
`tests/fixtures`. TYPESAFE_OFFLINE=1 is enforced, so the real network transport
raises even when TYPESAFE_API_KEY is present.

No real production log is read, written or hashed: `TYPESAFE_DEFAULT_LOG` is
repointed at a synthetic temp file before ts_common is imported, and the
production-log guard tests run against that synthetic default.

Run: python3 scripts/tests_phase1.py [--verbose]
"""
import importlib.util
import json
import os
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(ROOT)
sys.path.insert(0, ROOT)

# A synthetic stand-in for the deployment's production log. The suite must NEVER
# read, write or hash a real production log, so the *default* log path is moved
# into a throwaway temp directory BEFORE ts_common is imported. Everything the
# guard tests exercise (`_is_production_log`, the offline write refusal, the
# symlink/hardlink identity checks) runs against this synthetic file through
# exactly the same code path as a real deployment.
TMP = tempfile.mkdtemp(prefix="ts-phase1-")
SYNTHETIC_PRODLOG = os.path.join(TMP, "synthetic-production-log.jsonl")
with open(SYNTHETIC_PRODLOG, "w", encoding="utf-8") as _f:
    _f.write('{"event":"decision","synthetic":true,"schema_version":4,"workflow":"rank"}\n')
os.environ["TYPESAFE_DEFAULT_LOG"] = SYNTHETIC_PRODLOG

os.environ["TYPESAFE_OFFLINE"] = "1"
os.environ["TYPESAFE_API_KEY"] = "test-key-not-real"
os.environ["TYPESAFE_ROUTER_MODEL"] = "jev-1.13.0"
os.environ.pop("TYPESAFE_ALLOW_MODEL_DRIFT", None)

import socket

def _deny_network(*args, **kwargs):
    raise AssertionError("hermetic_test_network_access_denied")

socket.create_connection = _deny_network
import ts_common as tsc  # noqa: E402
import replay_harness as rh  # noqa: E402


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, os.path.join(ROOT, path))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


dw = load("decision_workflows", "decision_workflows.py")
rt = load("route_task", "route_task.py")
PINNED = tsc.MODEL
TESTLOG = os.path.join(TMP, "decisions.jsonl")
PRODLOG = SYNTHETIC_PRODLOG
PRODLOG_SHA256 = __import__("hashlib").sha256(open(PRODLOG, "rb").read()).hexdigest()
PRODLOG_SHA256_AT_START = PRODLOG_SHA256

RESULTS = []
VERBOSE = "--verbose" in sys.argv
SEEN = set()

# Pinned bytes of the verbatim upstream MIT license copy (skills/typesafe-ai/LICENSE,
# upstream commit below). Verified once against a local upstream checkout; the
# pin keeps the copy honest without needing that checkout at test time.
UPSTREAM_LICENSE_SHA256 = "835f233f1d6ed84a9b9a351aba0689b47644a4137d6316911fc7957bde523b02"
UPSTREAM_COMMIT = "65a39f393687675ce170e6094757de20370365b9"


def test(finding, name):
    """Register and immediately run one regression.

    Duplicate (finding, name) pairs are a hard error: a duplicated test would
    inflate the executed count without adding coverage (audit P2 test inflation).
    """
    def deco(fn):
        key = (finding, name)
        if key in SEEN:
            RESULTS.append({"finding": finding, "test": name, "ok": False,
                            "error": "DuplicateTest: this (finding, name) pair is already registered"})
            return fn
        SEEN.add(key)
        try:
            fn()
            RESULTS.append({"finding": finding, "test": name, "ok": True})
        except Exception as e:  # noqa: BLE001
            RESULTS.append({"finding": finding, "test": name, "ok": False,
                            "error": f"{type(e).__name__}: {e}"})
        return fn
    return deco


def final_gate(name):
    """Register a gate that must run AFTER every other test.

    Decorated gates are collected, not executed, and `main()` runs them last, so
    the privacy/production-hash checks really observe the whole suite's side
    effects (audit P2 gates executed too early).
    """
    def deco(fn):
        FINAL_GATES.append((name, fn))
        return fn
    return deco


FINAL_GATES = []


def harness(transport, **kw):
    kw.setdefault("log_path", TESTLOG)
    return rh.Harness(tsc, transport, **kw)


def rank_via(transport, obj):
    with harness(transport):
        return dw.rank(obj)


# ============================================================ FOUNDATION
@test("FOUNDATION", "offline mode blocks the real network transport even with a key")
def _f1():
    os.environ["TYPESAFE_API_KEY"] = "test-key-not-real"
    try:
        tsc.network_transport("https://api.typesafe.ai/v1/systemone", b"{}", {}, 1)
        raise AssertionError("network transport was not blocked")
    except tsc.TransportError as e:
        assert "offline_mode_network_blocked" in str(e), str(e)


@test("FOUNDATION", "write_log refuses the production log path in offline mode")
def _f2():
    _id, err = tsc.write_log({"event": "decision", "probe": True}, PRODLOG)
    assert err == "offline_refuses_default_production_log", err


@test("FOUNDATION", "cost model reproduces both frozen runs within 5%")
def _f3():
    # Payload chars and observed usage from the two frozen calibration runs.
    # A calibration over two points, not an independent validation.
    for chars, observed in ((27157, 6928), (144663, 37794)):
        est = tsc.estimate_input_tokens(chars)
        err = abs(est - observed) / observed
        assert err <= 0.05, f"{est} vs {observed}: {err:.3%}"


@test("FOUNDATION", "replay of the frozen shortlist reproduces the ranking rows exactly")
def _f4():
    base = rh.FIXTURES_DIR + "/"
    inp = json.load(open(base + "rank_shortlist_input.json", encoding="utf-8"))
    frozen = json.load(open(base + "rank_shortlist_output.json", encoding="utf-8"))["result"]
    got = rank_via(rh.frozen_shortlist_cassette(base), inp)
    a = {r["id"]: (r["fit"], r["useful"], r["injection"], r["coverage"]) for r in frozen["ranking"]}
    b = {r["id"]: (r["fit"], r["useful"], r["injection"], r["coverage"]) for r in got["ranking"]}
    assert a == b, "replayed ranking rows differ from the frozen run"
    assert [r["id"] for r in frozen["ranking"]] == [r["id"] for r in got["ranking"]], "order differs"
    # The replay must reproduce the frozen policy DECISION, not just the rows.
    assert got["decision"] == frozen["decision"], (got["decision"], frozen["decision"])
    assert got["selected"] == frozen["selected"], got["selected"]


@test("P1B-J", "the replay cassette refuses modified frozen fixtures")
def _b_replay_refuses_tampered():
    import shutil
    tampered = os.path.join(TMP, "tampered-fixtures")
    shutil.copytree(rh.FIXTURES_DIR, tampered, dirs_exist_ok=True)
    rh.frozen_shortlist_cassette(tampered)  # pristine copy verifies fine
    p = os.path.join(tampered, "rank_shortlist_output.json")
    doc = json.load(open(p, encoding="utf-8"))
    doc["result"]["ranking"][0]["fit"] = 0.123456
    json.dump(doc, open(p, "w", encoding="utf-8"))
    try:
        rh.frozen_shortlist_cassette(tampered)
        raise AssertionError("a tampered fixture was accepted")
    except rh.FixtureIntegrityError as e:
        assert "fixture_hash_mismatch" in str(e), str(e)


@test("P1B-J", "the replayer records fixture provenance without sensitive content")
def _b_replay_provenance():
    prov = rh.fixture_provenance()
    assert prov["file_count"] >= 6 and len(prov["aggregate_sha256"]) == 64, prov
    assert prov["manifest_label"] == "synthetic-fixtures-frozen", prov
    assert "origin=synthetic" in prov["provenance"], prov
    blob = json.dumps(prov)
    for marker in ("sk-", "Bearer", "@"):
        assert marker not in blob, marker


# ============================================================ P0-1 state preflight
@test("P0-1", "chunks() measures the real request payload: no chunk exceeds the cap")
def _p011():
    base = rh.FIXTURES_DIR + "/"
    obj = json.load(open(base + "rank_shortlist_input.json", encoding="utf-8"))
    cands = [dw.scrub(c) for c in obj["candidates"]]
    reqs = dw.requirement_rows(obj["requirements"])
    compact = [{"id": str(c["id"]), "content": {k: v for k, v in c.items() if k != "id"}} for c in cands]
    base_state = {"query": obj.get("query", ""), "criteria": obj.get("criteria", []),
                  "requirements": reqs, "note": dw.NOTE}
    groups = dw.chunks(compact, base_state, 4, len(reqs))
    for g in groups:
        size = dw.rank_payload_chars(base_state, g, len(reqs))
        assert size <= tsc.MAX_PAYLOAD_CHARS, f"chunk of {len(g)} needs {size} > {tsc.MAX_PAYLOAD_CHARS}"
    assert sum(len(g) for g in groups) == len(compact)


@test("P0-1", "oversize input makes ZERO paid calls (preflight, not mid-loop failure)")
def _p012():
    t = rh.StubTransport(answer_fn=rh.rank_answer_fn())
    reqs_big = [{"id": f"r{i}", "text": "R" * 1200} for i in range(12)]
    cl = [{"id": f"s{i}", "text": "s" * 200} for i in range(4)] + \
         [{"id": f"b{i}", "text": "B" * 4000} for i in range(4)]
    with harness(t):
        try:
            dw.rank({"mode": "shortlist", "query": "Q" * 600, "criteria": ["a"],
                     "requirements": reqs_big, "candidates": cl})
            raise AssertionError("oversize request accepted")
        except ValueError as e:
            assert "too_large" in str(e), str(e)
    # Pre-fix behaviour: 1 paid call, then ValueError, whole run discarded.
    assert t.calls == 0, f"{t.calls} paid calls made before refusing"


@test("P0-1", "a single candidate too large to ever fit raises before any paid call")
def _p013():
    t = rh.StubTransport(answer_fn=rh.rank_answer_fn())
    with harness(t):
        try:
            dw.rank({"query": "q", "candidates": [{"id": "a", "text": "x" * 40000},
                                                  {"id": "b", "text": "y"}]})
            raise AssertionError("oversize candidate accepted")
        except ValueError as e:
            assert "payload_too_large_for_single_candidate" in str(e), str(e)
    assert t.calls == 0, f"{t.calls} paid calls"


@test("P0-1", "failure AFTER a paid call returns partial result + partial_usage, not a discard")
def _p014():
    # 8 small candidates -> 2 chunks; second chunk returns a non-retryable 400
    t = rh.StubTransport(answer_fn=rh.rank_answer_fn(), script=[None, (400, None)])
    with harness(t):
        out = dw.rank({"query": "q", "candidates": [{"id": f"c{i}", "text": "t" * 50} for i in range(12)]})
    assert out["decision"] == "human_review", out["decision"]
    assert out["api_calls"] == 1 and out["planned_api_calls"] == 2, out
    assert "partial_usage" in out and out["partial_usage"], out.get("partial_usage")
    assert len(out["ranking"]) == 8, len(out["ranking"])
    assert any(w.startswith("partial_run_aborted") for w in out["warnings"]), out["warnings"]


@test("P0-1", "base_state that dwarfs the budget is refused with a diagnostic")
def _p015():
    t = rh.StubTransport(answer_fn=rh.rank_answer_fn())
    with harness(t):
        try:
            dw.rank({"query": "Q" * 20000, "candidates": [{"id": "a", "text": "x"}, {"id": "b", "text": "y"}]})
            raise AssertionError("oversize base state accepted")
        except ValueError as e:
            assert "base_state_too_large" in str(e), str(e)
    assert t.calls == 0


# ============================================================ P0-2 route fail-closed
def route_cli(args, stdin=None, env=None):
    e = rh.child_env(env or {}, log_path=TESTLOG)
    return subprocess.run([sys.executable, os.path.join(ROOT, "route_task.py")] + args,
                          input=stdin, text=True, capture_output=True, env=e, timeout=60)


@test("P0-2", "context: [] returns valid JSON main_review with exit 0 (was AttributeError)")
def _p021():
    r = route_cli(["--stdin-json", "--no-log"], json.dumps({"task": "x", "context": []}))
    assert r.returncode == 0, f"rc={r.returncode} stderr={r.stderr[:200]}"
    o = json.loads(r.stdout)
    assert o["policy"]["recommended_executor"] == "main_review", o["policy"]


@test("P0-2", "context: 5 returns valid JSON main_review with exit 0")
def _p022():
    r = route_cli(["--stdin-json", "--no-log"], json.dumps({"task": "x", "context": 5}))
    assert r.returncode == 0, f"rc={r.returncode} stderr={r.stderr[:200]}"
    assert json.loads(r.stdout)["policy"]["recommended_executor"] == "main_review"


@test("P0-2", "unwritable log path is non-fatal: valid JSON, exit 0, meta.log_error present")
def _p023():
    r = route_cli(["--task", "x"], env={"TYPESAFE_DECISION_LOG": "/proc/definitely/not/writable/x.jsonl"})
    assert r.returncode == 0, f"rc={r.returncode} stderr={r.stderr[:300]}"
    o = json.loads(r.stdout)
    assert o["policy"]["recommended_executor"] == "main_review"
    assert o["meta"].get("log_error"), o["meta"]


@test("P0-2", "normalize_context accepts every shape without raising")
def _p024():
    for ctx in ([], 5, None, {"summary": "s"}, "text", 3.5, True, {"summary": None}):
        gate, api = rt.normalize_context(ctx)
        assert isinstance(api, str)
    assert rt.normalize_context({"summary": "  s  "})[1] == "s"


@test("P0-2", "malformed stdin JSON is fail-closed JSON with exit 0")
def _p025():
    r = route_cli(["--stdin-json", "--no-log"], "{not json")
    assert r.returncode == 0, f"rc={r.returncode}"
    o = json.loads(r.stdout)
    assert o["policy"]["recommended_executor"] == "main_review" and o["meta"].get("failed_closed")


@test("P0-2", "argparse misuse uses the documented nonzero usage code")
def _p026():
    r = route_cli(["--nonexistent-flag"])
    assert r.returncode == tsc.EXIT_USAGE, r.returncode


# ============================================================ P0-3 set-cover blocked candidate
@test("P0-3", "domain-capped best cover candidate is skipped, not a loop break (audit I1)")
def _p031():
    t = rh.StubTransport(answer_fn=rh.rank_answer_fn(
        cov={"x1": {1: .95}, "x2": {0: .95}, "y1": {0: .95}},
        fit={"x1": .99, "x2": .97, "y1": .40, "n1": .96}))
    out = rank_via(t, {"mode": "shortlist", "query": "q",
                       "requirements": [{"id": "r0", "text": "r0"}, {"id": "r1", "text": "r1"}],
                       "selection": {"max_candidates": 2, "max_per_domain": 1,
                                     "target_context_chars": 100000, "minimum_score": .2},
                       "candidates": [{"id": "x1", "url": "https://x.test/1", "text": "a"},
                                      {"id": "x2", "url": "https://x.test/2", "text": "b"},
                                      {"id": "y1", "url": "https://y.test/1", "text": "c"},
                                      {"id": "n1", "url": "https://n.test/1", "text": "d"}]})
    assert out["decision"] == "selected", f"{out['decision']} selected={out['selected']} unc={out['uncovered_requirements']}"
    assert set(out["selected"]) == {"x1", "y1"}, out["selected"]


@test("P0-3", "domain cap with an alternative still reaches full coverage (audit H2)")
def _p032():
    t = rh.StubTransport(answer_fn=rh.rank_answer_fn(
        cov={"x1": {0: .95}, "x2": {1: .95}, "y1": {1: .95}},
        fit={"x1": .99, "x2": .98, "y1": .30}))
    out = rank_via(t, {"mode": "shortlist", "query": "q",
                       "requirements": [{"id": "r0", "text": "r0"}, {"id": "r1", "text": "r1"}],
                       "selection": {"max_candidates": 5, "max_per_domain": 1,
                                     "target_context_chars": 100000, "minimum_score": .2},
                       "candidates": [{"id": "x1", "url": "https://x.test/1", "text": "aaa"},
                                      {"id": "x2", "url": "https://x.test/2", "text": "bbb"},
                                      {"id": "y1", "url": "https://y.test/1", "text": "ccc"}]})
    assert out["decision"] == "selected" and set(out["selected"]) == {"x1", "y1"}, out["selected"]
    assert any(w.startswith("cover_candidate_blocked:x2") for w in out["warnings"]), out["warnings"]


@test("P0-3", "budget-blocked best candidate is skipped for a fitting alternative (audit H1)")
def _p033():
    t = rh.StubTransport(answer_fn=rh.rank_answer_fn(
        cov={"big": {0: .95}, "small2": {0: .95}, "small1": {1: .95}},
        fit={"big": .99, "small2": .30, "small1": .95}))
    out = rank_via(t, {"mode": "shortlist", "query": "q",
                       "requirements": [{"id": "r0", "text": "r0"}, {"id": "r1", "text": "r1"}],
                       "selection": {"max_candidates": 5, "max_per_domain": 9,
                                     "target_context_chars": 1000, "minimum_score": .2},
                       "candidates": [{"id": "big", "url": "https://a.test", "text": "B" * 1500},
                                      {"id": "small2", "url": "https://b.test", "text": "s" * 30},
                                      {"id": "small1", "url": "https://c.test", "text": "t" * 30}]})
    assert out["decision"] == "selected", f"{out['decision']} {out['selected']} {out['uncovered_requirements']}"
    assert {"small2", "small1"} <= set(out["selected"]), out["selected"]


# ============================================================ P0-4 coverage-aware dedup
@test("P0-4", "duplicate text with unique coverage survives dedup (audit H5)")
def _p041():
    txt = "alpha beta gamma delta epsilon zeta eta theta iota kappa lambda mu nu xi omicron pi"
    t = rh.StubTransport(answer_fn=rh.rank_answer_fn(
        cov={"dupA": {0: .95}, "dupB": {1: .95}}, fit={"dupA": .95, "dupB": .94}))
    out = rank_via(t, {"mode": "shortlist", "query": "q",
                       "requirements": [{"id": "r0", "text": "r0"}, {"id": "r1", "text": "r1"}],
                       "candidates": [{"id": "dupA", "url": "https://a.test", "text": txt},
                                      {"id": "dupB", "url": "https://b.test", "text": txt}]})
    assert out["decision"] == "selected", f"{out['decision']} unc={out['uncovered_requirements']}"
    assert set(out["selected"]) == {"dupA", "dupB"}, out["selected"]
    assert "dupB" not in out["duplicate_of"], out["duplicate_of"]
    assert any(w.startswith("duplicate_kept_for_unique_coverage:dupB") for w in out["warnings"]), out["warnings"]


@test("P0-4", "a true duplicate with no unique coverage is still excluded")
def _p042():
    txt = "alpha beta gamma delta epsilon zeta eta theta iota kappa lambda mu nu xi omicron pi"
    t = rh.StubTransport(answer_fn=rh.rank_answer_fn(
        cov={"dupA": {0: .95}, "dupB": {0: .95}}, fit={"dupA": .95, "dupB": .94}))
    out = rank_via(t, {"mode": "shortlist", "query": "q", "requirements": [{"id": "r0", "text": "r0"}],
                       "candidates": [{"id": "dupA", "url": "https://a.test", "text": txt},
                                      {"id": "dupB", "url": "https://b.test", "text": txt}]})
    assert out["duplicate_of"].get("dupB") == "dupA", out["duplicate_of"]
    assert out["decision"] == "selected"


# ============================================================ P0-5 injection provenance
@test("P0-5", "an injection-vetoed duplicate keeps exclusion_reason=injection (audit L2)")
def _p051():
    txt = "alpha beta gamma delta epsilon zeta eta theta iota kappa lambda mu nu xi omicron pi rho"
    t = rh.StubTransport(answer_fn=rh.rank_answer_fn(
        cov={"good": {0: .95}, "evil": {0: .95}}, inj={"evil": .99}, fit={"good": .9, "evil": .9}))
    out = rank_via(t, {"mode": "shortlist", "query": "q", "requirements": [{"id": "r0", "text": "r0"}],
                       "candidates": [{"id": "good", "url": "https://a.test", "text": txt},
                                      {"id": "evil", "url": "https://b.test", "text": txt}]})
    evil = next(r for r in out["ranking"] if r["id"] == "evil")
    assert evil["exclusion_reason"] == "injection", evil.get("exclusion_reason")
    assert "evil" not in out["duplicate_of"], out["duplicate_of"]
    assert "injection_vetoed:evil" in out["warnings"], out["warnings"]


@test("P0-5", "every injection veto emits a warning, not only required ones (audit L1)")
def _p052():
    t = rh.StubTransport(answer_fn=rh.rank_answer_fn(
        cov={"good": {0: .95}}, inj={"bad": .77}, fit={"good": .9, "bad": .9}))
    out = rank_via(t, {"mode": "shortlist", "query": "q", "requirements": [{"id": "r0", "text": "r0"}],
                       "candidates": [{"id": "good", "url": "https://a.test", "text": "aaa"},
                                      {"id": "bad", "url": "https://b.test", "text": "bbb"}]})
    assert "injection_vetoed:bad" in out["warnings"], out["warnings"]


@test("P0-5", "winner mode also surfaces injection vetoes in warnings")
def _p053():
    t = rh.StubTransport(answer_fn=rh.rank_answer_fn(inj={"bad": .9}, fit={"good": .95, "bad": .99}))
    out = rank_via(t, {"query": "q", "candidates": [{"id": "good", "text": "a"}, {"id": "bad", "text": "b"}]})
    assert "injection_vetoed:bad" in out["warnings"], out["warnings"]
    bad = next(r for r in out["ranking"] if r["id"] == "bad")
    assert bad["exclusion_reason"] == "injection" and bad["eligible"] is False


# ============================================================ P0-6 contaminated validation
@test("P0-6", "contaminated validation is retracted in the artifact and the docs")
def _p061():
    v = os.path.join(REPO_ROOT, "docs", "RETRACTION-shortlist-v1.1.md")
    text = open(v, encoding="utf-8").read()
    low = text.lower()
    assert "retracted" in low or "povuč" in low or "povuc" in low, "validation doc is not marked retracted"
    assert "11" in text, "requirement count not corrected to 11"
    assert "max_per_domain=4" in text or "max_per_domain 4" in text, "non-default parameter not disclosed"
    for doc_name in ("SKILL.md", "README.md"):
        skill = open(os.path.join(REPO_ROOT, doc_name), encoding="utf-8").read().lower()
        assert "51.7" in skill or "51,7" in skill, f"{doc_name} does not qualify the 51.7% figure"
        assert "projection" in skill or "retracted" in skill, \
            f"{doc_name} does not mark it as a projection"


@test("P0-6", "documented default max_per_domain=2 replays to the audited weaker recall")
def _p062():
    # Synthetic-fixture property test. The authored labels in query_and_gold.json
    # are NOT relevance judgements; they exist only to lock the *relative* policy
    # behaviour that the P0-6 retraction is about: the documented default
    # max_per_domain=2 recalls fewer same-domain sources than the undocumented
    # max_per_domain=4 that the retracted v1.1 run actually used.
    import copy
    base = rh.FIXTURES_DIR + "/"
    out = json.load(open(base + "rank_shortlist_output.json", encoding="utf-8"))["result"]
    inp = json.load(open(base + "rank_shortlist_input.json", encoding="utf-8"))
    gold = json.load(open(base + "query_and_gold.json", encoding="utf-8"))["gold_sources"]
    hi = set(gold["highly_relevant"])
    cands = [dw.scrub(c) for c in inp["candidates"]]
    reqs = dw.requirement_rows(inp["requirements"])

    def fresh():
        rows = copy.deepcopy(out["ranking"])
        for r in rows:
            r.pop("selection_reason", None)
            r.pop("exclusion_reason", None)
            r["eligible"] = r["injection"] < .5
        rows.sort(key=lambda x: (not x["eligible"], -x["score"], x["id"]))
        return rows

    sel = {"max_candidates": 8, "target_context_chars": 50000, "minimum_score": .25,
           "minimum_coverage_score": .40}
    r2 = dw.shortlist(fresh(), cands, reqs, dict(sel, max_per_domain=2))
    r4 = dw.shortlist(fresh(), cands, reqs, dict(sel, max_per_domain=4))
    rec2 = len(set(r2["selected"]) & hi)
    rec4 = len(set(r4["selected"]) & hi)
    assert rec2 < rec4, f"documented default no longer weaker: {rec2} vs {rec4}"


# ============================================================ P1-1 observability
@test("P1-1", "rank/verify/triage write a content-free audit row with decision_id and usage")
def _p111():
    log = os.path.join(TMP, "obs.jsonl")
    inp = json.dumps({"query": "secret query text", "candidates": [{"id": "a", "text": "aa"},
                                                                   {"id": "b", "text": "bb"}]})
    e = rh.child_env(log_path=log)
    r = subprocess.run([sys.executable, os.path.join(ROOT, "decision_workflows.py"), "rank"],
                       input=inp, text=True, capture_output=True, env=e, timeout=60)
    assert r.returncode == 0, f"rc={r.returncode} {r.stderr[:200]}"
    o = json.loads(r.stdout)
    assert o.get("decision_id"), o
    rows = [json.loads(l) for l in open(log, encoding="utf-8").read().splitlines() if l.strip()]
    row = rows[-1]
    for k in ("decision_id", "workflow", "schema_version", "decision", "api_calls", "usage",
              "latency_ms", "models_served", "input_sha256", "version"):
        assert k in row, f"missing log field {k}"
    assert row["workflow"] == "rank" and row["schema_version"] == tsc.SCHEMA_VERSION
    assert "secret query text" not in json.dumps(row), "log leaked input content"


@test("P1-1", "report.py groups by workflow and tolerates legacy rows without schema_version")
def _p112():
    log = os.path.join(TMP, "mixed.jsonl")
    with open(log, "w", encoding="utf-8") as f:
        f.write(json.dumps({"event": "decision", "decision_id": "old1", "ts": 1,
                            "policy": {"recommended_executor": "max"}, "raw": {"usage": {"input_tokens": 100}},
                            "latency_ms": 10}) + "\n")
        f.write(json.dumps({"event": "decision", "schema_version": 3, "decision_id": "new1",
                            "workflow": "rank", "decision": "human_review", "api_calls": 2,
                            "usage": {"input_tokens": 50}, "latency_ms": 20, "warnings": ["injection_vetoed:x"]}) + "\n")
        f.write("{not json\n")
    r = subprocess.run([sys.executable, os.path.join(ROOT, "report.py"), "--log-path", log],
                       text=True, capture_output=True, env=rh.child_env(log_path=log), timeout=60)
    assert r.returncode == 0, r.stderr[:300]
    rep = json.loads(r.stdout)
    assert rep["malformed_lines"] == 1, rep["malformed_lines"]
    assert rep["legacy_rows_without_schema"] == 1, rep
    assert set(rep["by_workflow"]) == {"route", "rank"}, rep["by_workflow"]
    assert rep["by_workflow"]["rank"]["input_tokens"] == 50
    assert rep["input_tokens"] == 150, rep["input_tokens"]


@test("P1-1", "--no-log makes no log row at all")
def _p113():
    log = os.path.join(TMP, "nolog.jsonl")
    inp = json.dumps({"query": "q", "candidates": [{"id": "a", "text": "a"}, {"id": "b", "text": "b"}]})
    subprocess.run([sys.executable, os.path.join(ROOT, "decision_workflows.py"), "rank", "--no-log"],
                   input=inp, text=True, capture_output=True, env=rh.child_env(log_path=log), timeout=60)
    assert not os.path.exists(log), "log written despite --no-log"


@test("P1-1", "concurrent appends never corrupt a JSONL row")
def _p114():
    log = os.path.join(TMP, "concurrent.jsonl")
    procs = [subprocess.Popen([sys.executable, os.path.join(ROOT, "route_task.py"),
                               "--task", f"task-{i}"], stdout=subprocess.DEVNULL,
                              stderr=subprocess.DEVNULL, env=rh.child_env(log_path=log))
             for i in range(8)]
    for p in procs:
        p.wait(timeout=60)
    lines = [l for l in open(log, encoding="utf-8").read().splitlines() if l.strip()]
    assert len(lines) == 8, len(lines)
    for l in lines:
        json.loads(l)  # raises on a torn row
    assert oct(os.stat(log).st_mode)[-3:] == "600", oct(os.stat(log).st_mode)


# ============================================================ P1-2 retry/backoff/deadline
@test("P1-2", "429 is retried with backoff and jitter, then succeeds")
def _p121():
    t = rh.StubTransport(script=[(429, None), (429, None), None])
    h = harness(t)
    with h:
        data = tsc.post_json({"model": PINNED, "state": {}, "questions": {"q": 1}}, attempts=5)
    assert data["model"] == PINNED
    assert t.calls == 3, t.calls
    assert len(h.clock.slept) == 2, h.clock.slept
    assert h.clock.slept[1] > h.clock.slept[0], h.clock.slept  # exponential
    assert all(s > 0 for s in h.clock.slept)


@test("P1-2", "Retry-After header is honoured exactly (plus bounded jitter)")
def _p122():
    t = rh.StubTransport(script=[(429, 7), None])
    h = harness(t)
    with h:
        tsc.post_json({"model": PINNED, "state": {}, "questions": {}}, attempts=3)
    assert 7.0 <= h.clock.slept[0] <= 7.5, h.clock.slept


@test("P1-2", "529 and 5xx are retried; 400 is not")
def _p123():
    for status, expect_calls in ((529, 3), (503, 3), (400, 1), (401, 1)):
        t = rh.StubTransport(script=[(status, 0)] * 5)
        with harness(t):
            try:
                tsc.post_json({"model": PINNED, "state": {}, "questions": {}}, attempts=3)
                raise AssertionError(f"status {status} did not raise")
            except tsc.TransportError:
                pass
        assert t.calls == expect_calls, f"status {status}: {t.calls} calls, expected {expect_calls}"


@test("P1-2", "a global deadline stops retrying instead of looping forever")
def _p124():
    t = rh.StubTransport(script=[(429, 30)] * 10)
    h = harness(t)
    with h:
        deadline = tsc.new_deadline(5)
        try:
            tsc.post_json({"model": PINNED, "state": {}, "questions": {}}, attempts=9, deadline=deadline)
            raise AssertionError("deadline not enforced")
        except tsc.TransportError as e:
            assert "deadline_exceeded" in str(e), str(e)
    assert t.calls == 1, t.calls
    assert h.clock.slept == [], h.clock.slept


@test("P1-2", "retry tests do not use real sleep (virtual clock only)")
def _p125():
    import time as _t
    t = rh.StubTransport(script=[(429, 60), (429, 60), None])
    start = _t.monotonic()
    with harness(t):
        tsc.post_json({"model": PINNED, "state": {}, "questions": {}}, attempts=5)
    assert _t.monotonic() - start < 2.0, "real sleeping occurred in a unit test"


@test("P1-2", "a mid-workflow 429 storm returns partial usage instead of discarding paid calls")
def _p126():
    t = rh.StubTransport(answer_fn=rh.rank_answer_fn(),
                         script=[None, (429, 0), (429, 0), (429, 0)])
    with harness(t):
        out = dw.rank({"query": "q", "candidates": [{"id": f"c{i}", "text": "t" * 50} for i in range(9)]})
    assert out["decision"] == "human_review"
    assert out["api_calls"] == 1 and "partial_usage" in out, out


# ============================================================ P1-3 model drift gate
@test("P1-3", "verify degrades pass -> human_review on model drift (audit V6)")
def _p131():
    t = rh.StubTransport(answer_fn=rh.verify_answer_fn(), model="jev-2.0.0")
    with harness(t):
        out = dw.verify({"requirements": ["a"], "candidate": "a"})
    assert out["decision"] == "human_review", out["decision"]
    assert out["model_drift"] is True and "downgraded_for_model_drift" in out["warnings"], out["warnings"]


@test("P1-3", "shortlist degrades selected -> human_review on model drift")
def _p132():
    t = rh.StubTransport(answer_fn=rh.rank_answer_fn(cov={"a": {0: .95}}), model="jev-9.9.9")
    out = rank_via(t, {"mode": "shortlist", "query": "q", "requirements": [{"id": "r0", "text": "r0"}],
                       "candidates": [{"id": "a", "text": "aa"}, {"id": "b", "text": "bb"}]})
    assert out["decision"] == "human_review" and out["model_drift"] is True, out["decision"]
    assert out["model_drift_served"] == ["jev-9.9.9"], out.get("model_drift_served")


@test("P1-3", "winner mode degrades a winner to human_review on model drift")
def _p133():
    t = rh.StubTransport(answer_fn=rh.rank_answer_fn(fit={"a": .99, "b": .3}), model="jev-2.0.0")
    out = rank_via(t, {"query": "q", "candidates": [{"id": "a", "text": "aa"}, {"id": "b", "text": "bb"}]})
    assert out["decision"] == "human_review", out["decision"]


@test("P1-3", "route degrades to main_review on model drift")
def _p134():
    data = {"model": "jev-2.0.0", "answers": {"executor": {"choice": "max", "confidence": .95},
                                              "delegation_value": {"noul": .9}, "parallelizable": {"noul": .1},
                                              "complexity": {"score": 3.0}, "consequence": {"score": 1.0}},
            "usage": {}}
    o = rt.apply_policy(data, 1)
    assert o["policy"]["recommended_executor"] == "main_review" and o["policy"]["reason"] == "model_drift", o["policy"]
    assert o["meta"]["model_drift"] is True


@test("P1-3", "TYPESAFE_ALLOW_MODEL_DRIFT=1 allows drift but still warns")
def _p135():
    t = rh.StubTransport(answer_fn=rh.verify_answer_fn(), model="jev-2.0.0")
    os.environ["TYPESAFE_ALLOW_MODEL_DRIFT"] = "1"
    try:
        with harness(t):
            out = dw.verify({"requirements": ["a"], "candidate": "a"})
    finally:
        os.environ.pop("TYPESAFE_ALLOW_MODEL_DRIFT", None)
    assert out["decision"] == "pass", out["decision"]
    assert "model_drift_allowed_by_env" in out["warnings"], out["warnings"]


@test("P1-3", "the pinned model never triggers the drift gate")
def _p136():
    t = rh.StubTransport(answer_fn=rh.verify_answer_fn(), model=PINNED)
    with harness(t):
        out = dw.verify({"requirements": ["a"], "candidate": "a"})
    assert out["decision"] == "pass" and not out.get("model_drift"), out


# ============================================================ P1-4 verify budget
@test("P1-4", "verify_groups counts question text: payload never exceeds the cap (audit K/C)")
def _p141():
    base = {"request": "r", "candidate_output": "C" * 21000}
    groups = dw.verify_groups(base, ["req " + str(i) for i in range(8)], evidence_mode=False)
    for g in groups:
        state = dict(base)
        state["requirements"] = [r for _, r in g]
        total = dw.state_size(dw.scrub(state)) + dw.state_size(dw.verify_questions(g, False))
        assert total <= tsc.MAX_PAYLOAD_CHARS, f"{total} > {tsc.MAX_PAYLOAD_CHARS}"
    assert [i for g in groups for i, _ in g] == list(range(8))


@test("P1-4", "evidence mode doubles questions and is accounted for in the budget")
def _p142():
    base = {"request": "r", "candidate_output": "C" * 18000, "supplied_evidence": "E" * 1000}
    groups = dw.verify_groups(base, ["req " + str(i) * 50 for i in range(8)])
    for g in groups:
        state = dict(base)
        state["requirements"] = [r for _, r in g]
        qs = dw.verify_questions(g, True)
        assert len(qs) == 2 * len(g), (len(qs), len(g))
        total = dw.state_size(dw.scrub(state)) + dw.state_size(qs)
        assert total <= tsc.MAX_PAYLOAD_CHARS, f"{total} > {tsc.MAX_PAYLOAD_CHARS}"


@test("P1-4", "docs state 8 requirements / up to 16 questions, not 8 questions")
def _p143():
    skill = open(os.path.join(os.path.dirname(ROOT), "SKILL.md"), encoding="utf-8").read()
    wp = open(os.path.join(os.path.dirname(ROOT), "references", "workflow-policy.md"), encoding="utf-8").read()
    for text, label in ((skill, "SKILL.md"), (wp, "workflow-policy.md")):
        assert "16" in text and "eight requirements" in text.lower().replace("8 requirements", "eight requirements"), \
            f"{label} still misstates the verify batch limit"


@test("P1-4", "actual verify calls never exceed the enforced per-call requirement limit")
def _p144():
    sizes = []

    def fn(state, questions):
        sizes.append(len(state["requirements"]))
        return rh.verify_answer_fn()(state, questions)
    t = rh.StubTransport(answer_fn=fn)
    with harness(t):
        dw.verify({"requirements": [f"r{i}" for i in range(20)], "candidate": "x"})
    assert sizes and max(sizes) <= dw.MAX_REQUIREMENTS_PER_VERIFY_CALL, sizes


# ============================================================ P1-5 null-safe evidence
@test("P1-5", "missing evidence answer -> human_review, not TypeError (audit V3)")
def _p151():
    t = rh.StubTransport(answer_fn=rh.verify_answer_fn(evidence=None))  # no *_evidence keys
    with harness(t):
        out = dw.verify({"requirements": ["a"], "candidate": "a", "evidence": "ev"})
    assert out["decision"] == "human_review", out["decision"]
    assert out["requirements"][0]["evidence_score"] is None
    assert "missing_evidence_score:r0" in out["warnings"], out["warnings"]


@test("P1-5", "present evidence score >= 0.80 still passes")
def _p152():
    t = rh.StubTransport(answer_fn=rh.verify_answer_fn(evidence=0.9))
    with harness(t):
        out = dw.verify({"requirements": ["a"], "candidate": "a", "evidence": "ev"})
    assert out["decision"] == "pass" and out["requirements"][0]["evidence_score"] == 0.9, out


@test("P1-5", "evidence score below 0.80 blocks the pass")
def _p153():
    t = rh.StubTransport(answer_fn=rh.verify_answer_fn(evidence=0.5))
    with harness(t):
        out = dw.verify({"requirements": ["a"], "candidate": "a", "evidence": "ev"})
    assert out["decision"] == "human_review", out


# ============================================================ P1-6 strict requirements
@test("P1-6", "requirements as a string raises instead of iterating characters")
def _p161():
    for bad in ("not a list", {"a": 1, "b": 2}, b"bytes"):
        try:
            dw.requirement_rows(bad)
            raise AssertionError(f"accepted {type(bad).__name__}")
        except ValueError as e:
            assert "must be a list" in str(e), str(e)


@test("P1-6", "a non-string non-dict requirement item raises")
def _p162():
    try:
        dw.requirement_rows(["ok", 5])
        raise AssertionError("accepted an int requirement")
    except ValueError as e:
        assert "requirements[1]" in str(e), str(e)


@test("P1-6", "rank CLI turns a string requirements field into fail-closed JSON, no paid call")
def _p163():
    t = rh.StubTransport(answer_fn=rh.rank_answer_fn())
    with harness(t):
        try:
            dw.rank({"mode": "shortlist", "query": "q", "requirements": "Setup steps",
                     "candidates": [{"id": "a", "text": "x"}, {"id": "b", "text": "y"}]})
            raise AssertionError("string requirements accepted")
        except ValueError:
            pass
    assert t.calls == 0, t.calls


@test("P1-6", "empty list and None requirements remain valid for winner mode")
def _p164():
    assert dw.requirement_rows([]) == [] and dw.requirement_rows(None) == []


# ============================================================ P1-7 selection validation
@test("P1-7", "out-of-range selection values raise (audit M1)")
def _p171():
    for sel, key in (({"minimum_coverage_score": 5}, "minimum_coverage_score"),
                     ({"minimum_score": -3}, "minimum_score"),
                     ({"max_candidates": 0}, "max_candidates"),
                     ({"target_context_chars": 10}, "target_context_chars"),
                     ({"max_per_domain": 0}, "max_per_domain")):
        try:
            dw.validate_selection(sel)
            raise AssertionError(f"accepted {sel}")
        except ValueError as e:
            assert key in str(e), str(e)


@test("P1-7", "non-dict selection raises a clear error, not AttributeError")
def _p172():
    for bad in ("eight", 8, [1, 2]):
        try:
            dw.validate_selection(bad)
            raise AssertionError(f"accepted {bad!r}")
        except ValueError as e:
            assert "selection must be an object" in str(e), str(e)


@test("P1-7", "unknown selection keys are rejected (typo protection)")
def _p173():
    try:
        dw.validate_selection({"max_candidate": 3})
        raise AssertionError("typo accepted")
    except ValueError as e:
        assert "unknown selection keys" in str(e), str(e)


@test("P1-7", "defaults match the documented policy values")
def _p174():
    d = dw.validate_selection({})
    assert d == {"max_candidates": 8, "target_context_chars": 50000, "minimum_score": .25,
                 "minimum_coverage_score": .4, "max_per_domain": 2}, d


@test("P1-7", "invalid selection is fail-closed at the CLI boundary with exit 0 and no call")
def _p175():
    inp = json.dumps({"mode": "shortlist", "query": "q", "requirements": ["r"], "selection": "eight",
                      "candidates": [{"id": "a", "text": "x"}, {"id": "b", "text": "y"}]})
    r = subprocess.run([sys.executable, os.path.join(ROOT, "decision_workflows.py"), "rank", "--no-log"],
                       input=inp, text=True, capture_output=True, env=rh.child_env(), timeout=60)
    assert r.returncode == 0, r.returncode
    o = json.loads(r.stdout)
    assert o["result"]["decision"] == "human_review" and o["result"]["error_type"] == "ValueError", o["result"]


# ============================================================ P1-8 required overflow signals
@test("P1-8", "required beyond max_candidates emits a warning (audit K2)")
def _p181():
    cands = [{"id": f"q{i}", "url": f"https://d{i}.test", "text": "t" * 20, "required": True} for i in range(6)]
    t = rh.StubTransport(answer_fn=rh.rank_answer_fn(cov={"q0": {0: .95}}))
    out = rank_via(t, {"mode": "shortlist", "query": "q", "requirements": [{"id": "r0", "text": "r0"}],
                       "selection": {"max_candidates": 2}, "candidates": cands})
    assert len(out["selected"]) == 6, out["selected"]
    assert any(w.startswith("required_exceeded_max_candidates") for w in out["warnings"]), out["warnings"]


@test("P1-8", "required beyond max_per_domain emits a warning (audit K3)")
def _p182():
    cands = [{"id": f"q{i}", "url": "https://same.test/" + str(i), "text": "t" * 20, "required": True}
             for i in range(4)]
    t = rh.StubTransport(answer_fn=rh.rank_answer_fn(cov={"q0": {0: .95}}))
    out = rank_via(t, {"mode": "shortlist", "query": "q", "requirements": [{"id": "r0", "text": "r0"}],
                       "selection": {"max_per_domain": 1}, "candidates": cands})
    assert len(out["selected"]) == 4, out["selected"]
    assert any(w.startswith("required_exceeded_max_per_domain") for w in out["warnings"]), out["warnings"]


@test("P1-8", "required beyond target_context_chars emits a per-candidate warning")
def _p183():
    cands = [{"id": f"q{i}", "url": f"https://d{i}.test", "text": "t" * 900, "required": True} for i in range(3)]
    t = rh.StubTransport(answer_fn=rh.rank_answer_fn(cov={"q0": {0: .95}}))
    out = rank_via(t, {"mode": "shortlist", "query": "q", "requirements": [{"id": "r0", "text": "r0"}],
                       "selection": {"target_context_chars": 1000}, "candidates": cands})
    assert any(w.startswith("required_exceeded_target_context_chars") for w in out["warnings"]), out["warnings"]


@test("P1-8", "a coverage candidate dropped by minimum_score is reported (audit H4)")
def _p184():
    t = rh.StubTransport(answer_fn=rh.rank_answer_fn(
        cov={"low": {0: .99}, "high": {1: .99}}, fit={"low": .10, "high": .95}))
    out = rank_via(t, {"mode": "shortlist", "query": "q",
                       "requirements": [{"id": "r0", "text": "r0"}, {"id": "r1", "text": "r1"}],
                       "selection": {"minimum_score": .25, "max_candidates": 5},
                       "candidates": [{"id": "low", "url": "https://a.test", "text": "a"},
                                      {"id": "high", "url": "https://b.test", "text": "b"}]})
    assert any(w.startswith("coverage_candidate_below_minimum_score:low") for w in out["warnings"]), out["warnings"]


# ============================================================ P1-9 break-even / reduction honesty
@test("P1-9", "estimated_reduction_pct is computed over eligible candidates only (audit L7)")
def _p191():
    t = rh.StubTransport(answer_fn=rh.rank_answer_fn(cov={"good": {0: .95}}, inj={"junk": .99},
                                                     fit={"good": .9, "junk": .9}))
    out = rank_via(t, {"mode": "shortlist", "query": "q", "requirements": [{"id": "r0", "text": "r0"}],
                       "candidates": [{"id": "good", "url": "https://a.test", "text": "g" * 100},
                                      {"id": "junk", "url": "https://b.test", "text": "J" * 10000}]})
    assert out["estimated_eligible_chars"] < out["estimated_total_chars"], out
    assert out["estimated_reduction_pct"] <= 5, out["estimated_reduction_pct"]
    assert out["estimated_reduction_pct_vs_all_candidates"] > 90, out


@test("P1-9", "separate winner and shortlist break-even figures are documented")
def _p192():
    for path in (os.path.join(os.path.dirname(ROOT), "SKILL.md"),
                 os.path.join(os.path.dirname(ROOT), "references", "workflow-policy.md")):
        text = open(path, encoding="utf-8").read()
        assert "0.0199" in text and "0.1442" in text, f"{path} lacks both break-even figures"


# ============================================================ CLI / exit-code contract
@test("CONTRACT", "expected uncertainty always exits 0 with a valid JSON document")
def _c1():
    cases = [("rank", json.dumps({"query": "q", "candidates": []})),
             ("verify", json.dumps({"requirements": [], "candidate": "x"})),
             ("triage", "not json"),
             ("rank", json.dumps({"query": "q", "candidates": [{"id": "a"}, {"id": "a"}]}))]
    for wf, payload in cases:
        r = subprocess.run([sys.executable, os.path.join(ROOT, "decision_workflows.py"), wf, "--no-log"],
                           input=payload, text=True, capture_output=True, env=rh.child_env(), timeout=60)
        assert r.returncode == 0, f"{wf}: rc={r.returncode}"
        o = json.loads(r.stdout)
        assert o["result"]["decision"] == "human_review", o["result"]
        assert o["advisory_only"] is True and o["version"] == tsc.__version__


@test("CONTRACT", "workflow CLI reports a log failure without failing the decision")
def _c2():
    inp = json.dumps({"query": "q", "candidates": [{"id": "a", "text": "a"}, {"id": "b", "text": "b"}]})
    r = subprocess.run([sys.executable, os.path.join(ROOT, "decision_workflows.py"), "rank",
                        "--log-path", "/proc/nope/x.jsonl"], input=inp, text=True, capture_output=True,
                       env=rh.child_env(), timeout=60)
    assert r.returncode == 0, r.returncode
    o = json.loads(r.stdout)
    assert o.get("log_error"), o
    assert o["result"]["decision"] in ("human_review", "a", "b"), o["result"]["decision"]


@test("CONTRACT", "exit_code_for maps expected vs unexpected errors as documented")
def _c3():
    assert tsc.exit_code_for(ValueError("x")) == 0
    assert tsc.exit_code_for(tsc.TransportError("x")) == 0  # RuntimeError subclass
    assert tsc.exit_code_for(KeyError("x")) == 0
    assert tsc.exit_code_for(AttributeError("x")) == tsc.EXIT_INTERNAL
    assert tsc.exit_code_for(ZeroDivisionError("x")) == tsc.EXIT_INTERNAL


@test("CONTRACT", "version is single-sourced across all modules and SKILL.md")
def _c4():
    assert dw.VERSION == tsc.__version__ == rt.POLICY_VERSION
    skill = open(os.path.join(os.path.dirname(ROOT), "SKILL.md"), encoding="utf-8").read()
    assert f"version: {tsc.__version__}" in skill, "SKILL.md front matter version mismatch"
    rp = open(os.path.join(os.path.dirname(ROOT), "references", "routing-policy.md"), encoding="utf-8").read()
    assert tsc.__version__ in rp, "routing-policy.md version mismatch"


# ============================================================ PRIVACY / SECURITY
@test("PRIVACY", "scrub redacts camelCase, kebab-case and substring secret keys (audit P2-4)")
def _p2_4():
    keys = ["api_key", "apiKey", "api-key", "x-api-key", "bearer", "auth", "auth_header", "ssh_key",
            "passwd", "pwd", "pin", "otp", "refresh-token", "clientSecret", "sessionId",
            "Authorization", "PRIVATE_KEY", "user_password", "cookie"]
    out = tsc.scrub({k: "sk-live-SECRET" for k in keys})
    leaked = [k for k, v in out.items() if v != "[redacted]"]
    assert not leaked, f"unredacted: {leaked}"


@test("PRIVACY", "non-secret keys are preserved")
def _p2_4b():
    out = tsc.scrub({"title": "t", "url": "https://x", "authority": "primary", "keypoints": "k"})
    assert out["title"] == "t" and out["url"] == "https://x" and out["authority"] == "primary"


@test("PRIVACY", "route log stores only a task fingerprint, never the task text")
def _pr1():
    log = os.path.join(TMP, "route.jsonl")
    subprocess.run([sys.executable, os.path.join(ROOT, "route_task.py"), "--task",
                    "VERY SECRET TASK TEXT 12345"], capture_output=True, text=True,
                   env=rh.child_env(log_path=log), timeout=60)
    body = open(log, encoding="utf-8").read()
    assert "VERY SECRET TASK TEXT" not in body, "task text leaked into the log"
    row = json.loads(body.splitlines()[-1])
    assert len(row["task_sha256"]) == 64, row["task_sha256"]


@test("PRIVACY", "TYPESAFE_TASK_HMAC_KEY switches the fingerprint to keyed HMAC")
def _pr2():
    plain = tsc.task_fingerprint("abc")
    os.environ["TYPESAFE_TASK_HMAC_KEY"] = "tenant-key"
    try:
        keyed = tsc.task_fingerprint("abc")
    finally:
        os.environ.pop("TYPESAFE_TASK_HMAC_KEY", None)
    assert keyed.startswith("hmac-sha256:") and keyed.split(":")[1] != plain



# ==================================================== PHASE 1B (second audit)
# One or more independent regressions per confirmed finding of the second
# independent audit. Finding labels: P1B-A..P1B-L.

@test("P1B-A", "every hard-risk flag blocks unauthorized triage, read BEFORE scrubbing")
def _b_triage_each_hard_flag():
    for flag in dw.HARD_RISK_KEYS:
        t = rh.StubTransport(answer_fn=rh.triage_answer_fn("low", .9, .9))
        with harness(t):
            out = dw.triage({"action": "x", flag: True, "user_authorized": False})
        assert out["decision"] == "block", f"{flag} -> {out['decision']}"
        assert out["hard_risk_flags"] == [flag], out["hard_risk_flags"]
    # changes_credentials is the flag the scrubber used to erase.
    t = rh.StubTransport(answer_fn=rh.triage_answer_fn("low", .9, .9))
    with harness(t):
        out = dw.triage({"action": "x", "changes_credentials": True, "user_authorized": False})
    assert out["decision"] == "block"
    sent = t.requests[0]["body"]["state"]
    assert sent["changes_credentials"] == "[redacted]", sent


@test("P1B-A", "an authorized hard-risk action degrades to review, never allow_advisory")
def _b_triage_authorized():
    t = rh.StubTransport(answer_fn=rh.triage_answer_fn("low", .9, .9))
    with harness(t):
        out = dw.triage({"action": "x", "changes_credentials": True, "user_authorized": True})
    assert out["decision"] == "review", out["decision"]
    assert out["authorization"] is False


@test("P1B-A", "a non-boolean control flag is refused instead of being coerced")
def _b_triage_flag_types():
    for value in ("true", 1, [], {}, None):
        t = rh.StubTransport(answer_fn=rh.triage_answer_fn())
        try:
            with harness(t):
                dw.triage({"action": "x", "changes_credentials": value})
            raise AssertionError(f"accepted non-boolean flag {value!r}")
        except ValueError as e:
            assert "control_flag_must_be_boolean" in str(e), str(e)
        assert t.calls == 0, "a paid call was made despite an invalid control flag"


@test("P1B-B", "malformed answers/usage shapes never raise AttributeError and keep usage")
def _b_malformed_shapes():
    good = rh.rank_answer_fn()
    for second in ({"model": PINNED, "answers": [], "usage": {}},
                   {"model": PINNED, "answers": {}, "usage": [1]},
                   [1, 2, 3], "nope", None):
        class T(rh.StubTransport):
            def __init__(self):
                super().__init__(answer_fn=good, usage={"input_tokens": 55})
                self.n = 0
            def respond(self, body):
                self.n += 1
                if self.n >= 2:
                    return self.ok(second) if isinstance(second, (dict, list)) else \
                        (200, {}, json.dumps(second).encode())
                return super().respond(body)
        t = T()
        with harness(t):
            out = dw.rank({"query": "q", "candidates": [{"id": f"c{i}", "text": "t" * 10}
                                                        for i in range(9)]})
        assert out["decision"] == "human_review", out["decision"]
        assert out["partial_usage"]["input_tokens"] >= 55, out["partial_usage"]
        assert len(out["ranking"]) == 8, len(out["ranking"])
        assert out["api_calls"] == 1 and out["api_responses_received"] == 2, out


@test("P1B-B", "a successful response arriving after the deadline keeps its usage")
def _b_late_response():
    class Late(rh.StubTransport):
        def __init__(self):
            super().__init__(answer_fn=rh.rank_answer_fn(), usage={"input_tokens": 55})
            self.clock = None
        def respond(self, body):
            r = super().respond(body)
            if self.clock:
                self.clock.advance(10_000)
            return r
    t = Late()
    h = harness(t)
    with h:
        t.clock = h.clock
        out = dw.rank({"query": "q", "candidates": [{"id": f"c{i}", "text": "t" * 10}
                                                    for i in range(9)]})
    assert out["decision"] == "human_review", out["decision"]
    assert out["partial_usage"]["input_tokens"] == 55, out["partial_usage"]
    assert out["api_responses_received"] == 1 and out["api_calls"] == 0, out
    assert "late_response_usage_preserved" in out["warnings"], out["warnings"]


@test("P1B-B", "attempts, received responses and accepted chunks are reported separately")
def _b_accounting_fields():
    t = rh.StubTransport(answer_fn=rh.rank_answer_fn(), usage={"input_tokens": 7})
    with harness(t):
        out = dw.rank({"query": "q", "candidates": [{"id": f"c{i}", "text": "t"} for i in range(9)]})
    assert out["api_calls"] == 2 and out["api_attempts"] == 2 and out["api_responses_received"] == 2, out
    assert out["usage"]["input_tokens"] == 14 and out["total_usage"]["input_tokens"] == 14, out


@test("P1B-C", "an arbitrary winner candidate ID never reaches the audit log")
def _b_log_no_arbitrary_id():
    marker = "AUDIT_SYNTHETIC_SECRET"
    t = rh.StubTransport(answer_fn=rh.rank_answer_fn(fit={marker: .99}, useful={marker: .99},
                                                     default_fit=.2))
    with harness(t):
        out = dw.rank({"query": "q", "candidates": [{"id": marker, "text": "alpha"},
                                                    {"id": "other", "text": "beta"}]})
    assert out["decision"] == marker and out["winner_id"] == marker, out["decision"]
    row = dw.log_row("rank", out, {"candidates": [1, 2]})
    blob = json.dumps(row, ensure_ascii=False)
    assert marker not in blob, blob[:400]
    assert row["decision"] == "winner" and row["decision_ref"].split(":")[0] in ("s", "h"), row
    assert "winner_id_withheld_from_log" in row["warnings"], row["warnings"]


@test("P1B-C", "warning payloads (ids, domains) are reduced to opaque codes in the log")
def _b_log_warning_codes():
    t = rh.StubTransport(answer_fn=rh.rank_answer_fn(cov={"AUDIT_ID_LEAK_A": {0: .9},
                                                          "AUDIT_ID_LEAK_B": {1: .9}}))
    with harness(t):
        out = dw.rank({"mode": "shortlist", "query": "q", "requirements": ["x", "y"],
                       "selection": {"max_candidates": 1},
                       "candidates": [{"id": "AUDIT_ID_LEAK_A", "url": "https://leak-a.example/1", "text": "a"},
                                      {"id": "AUDIT_ID_LEAK_B", "url": "https://leak-b.example/2", "text": "b"}]})
    row = dw.log_row("rank", out, {"candidates": [1, 2]})
    blob = json.dumps(row, ensure_ascii=False)
    for marker in ("AUDIT_ID_LEAK", "leak-a.example", "leak-b.example"):
        assert marker not in blob, marker
    assert any(w.startswith("cover_candidate_blocked:") for w in row["warnings"]), row["warnings"]
    assert row["warnings_total"] >= 1


@test("P1B-C", "unknown warning codes collapse instead of passing text through")
def _b_sanitize_unknown_warning():
    assert tsc.sanitize_warning("totally_new_code:SECRET") == "unknown_warning"
    assert tsc.sanitize_warning("near_duplicates_excluded:3") == "near_duplicates_excluded:3"
    assert tsc.sanitize_warning("model_drift:jev-2") == "model_drift:jev-2"
    op = tsc.sanitize_warning("injection_vetoed:SECRET_ID")
    assert op.startswith("injection_vetoed:") and "SECRET_ID" not in op


@test("P1B-C", "opaque_id switches to keyed HMAC and never contains the input")
def _b_opaque_id():
    plain = tsc.opaque_id("AUDIT_VALUE")
    assert plain.startswith("s:") and "AUDIT_VALUE" not in plain and len(plain) == 18
    os.environ["TYPESAFE_TASK_HMAC_KEY"] = "tenant-key"
    try:
        keyed = tsc.opaque_id("AUDIT_VALUE")
    finally:
        os.environ.pop("TYPESAFE_TASK_HMAC_KEY", None)
    assert keyed.startswith("h:") and keyed.split(":")[1] != plain.split(":")[1]


@test("P1B-C", "record_outcome omits --note from the log unless explicitly allowed")
def _b_note_policy():
    log = os.path.join(TMP, "outcome.jsonl")
    tsc.write_log({"event": "decision", "decision_id": "note-1", "workflow": "route"}, log)
    r = subprocess.run([sys.executable, os.path.join(ROOT, "record_outcome.py"),
                        "--decision-id", "note-1", "--actual", "max",
                        "--note", "AUDIT_NOTE_SECRET_PAYLOAD"],
                       capture_output=True, text=True, env=rh.child_env(log_path=log), timeout=60)
    assert r.returncode == 0, r.stderr[:300]
    doc = json.loads(r.stdout)
    body = open(log, encoding="utf-8").read()
    assert "AUDIT_NOTE_SECRET_PAYLOAD" not in body, "note leaked into the log"
    assert doc["note_policy"] == "omitted_from_log" and doc["note_ref"]
    assert doc["note_echo"] == "AUDIT_NOTE_SECRET_PAYLOAD"
    # Explicit opt-in still works, and is labelled in the row.
    r2 = subprocess.run([sys.executable, os.path.join(ROOT, "record_outcome.py"),
                         "--decision-id", "note-1", "--actual", "max", "--note", "OPTED_IN_TEXT",
                         "--allow-note-in-log"],
                        capture_output=True, text=True, env=rh.child_env(log_path=log), timeout=60)
    assert json.loads(r2.stdout)["note_policy"] == "explicitly_allowed_free_text"
    assert "OPTED_IN_TEXT" in open(log, encoding="utf-8").read()


@test("P1B-D", "a duplicate is requeued when its representative is domain-blocked")
def _b_dedup_requeue_domain():
    body = "alpha beta gamma delta epsilon zeta eta theta iota kappa lambda mu"
    t = rh.StubTransport(answer_fn=rh.rank_answer_fn(
        cov={"anchor": {0: .9}, "dupA": {1: .9}, "dupB": {1: .9}}))
    with harness(t):
        out = dw.rank({"mode": "shortlist", "query": "q", "requirements": ["r0", "r1"],
                       "selection": {"max_per_domain": 1},
                       "candidates": [
                           {"id": "anchor", "url": "https://a.test/0",
                            "text": "anchor unique text here", "required": True},
                           {"id": "dupA", "url": "https://a.test/1", "text": body},
                           {"id": "dupB", "url": "https://b.test/2", "text": body}]})
    assert out["decision"] == "selected", out["decision"]
    assert set(out["selected"]) == {"anchor", "dupB"}, out["selected"]
    assert out["uncovered_requirements"] == [], out["uncovered_requirements"]
    assert any(w.startswith("duplicate_requeued_for_feasibility:") for w in out["warnings"]), out["warnings"]
    assert "dupB" not in out["duplicate_of"], out["duplicate_of"]


@test("P1B-D", "a genuine duplicate with a feasible representative stays excluded")
def _b_dedup_still_excludes():
    body = "alpha beta gamma delta epsilon zeta eta theta iota kappa lambda mu"
    t = rh.StubTransport(answer_fn=rh.rank_answer_fn(cov={"dupA": {0: .9}, "dupB": {0: .9}}))
    with harness(t):
        out = dw.rank({"mode": "shortlist", "query": "q", "requirements": ["r0"],
                       "selection": {"max_per_domain": 4},
                       "candidates": [{"id": "dupA", "url": "https://a.test/1", "text": body},
                                      {"id": "dupB", "url": "https://b.test/2", "text": body}]})
    assert out["decision"] == "selected" and out["selected"] == ["dupA"], out["selected"]
    assert out["duplicate_of"].get("dupB") == "dupA", out["duplicate_of"]


@test("P1B-E", "a candidate ID colliding with a policy status cannot bypass the drift gate")
def _b_drift_no_bypass():
    for cid in ("normal", "block", "review", "insufficient_coverage", "human_review", "selected", "pass"):
        t = rh.StubTransport(answer_fn=rh.rank_answer_fn(fit={cid: .99}, useful={cid: .99},
                                                         default_fit=.1), model="jev-2")
        with harness(t):
            out = dw.rank({"query": "q", "candidates": [{"id": cid, "text": "a"},
                                                        {"id": "zzz", "text": "b"}]})
        assert out["model_drift"] is True, cid
        assert out["decision"] == "human_review", f"{cid} -> {out['decision']}"
        assert "downgraded_for_model_drift" in out["warnings"], cid


@test("P1B-E", "winner_id is the separate carrier and is marked degraded under drift")
def _b_drift_winner_id():
    t = rh.StubTransport(answer_fn=rh.rank_answer_fn(fit={"a": .99}, useful={"a": .99},
                                                     default_fit=.1), model="jev-2")
    with harness(t):
        out = dw.rank({"query": "q", "candidates": [{"id": "a", "text": "x"}, {"id": "b", "text": "y"}]})
    assert out["decision"] == "human_review" and out["winner_id"] == "a", out
    assert out.get("winner_id_degraded") is True, out
    row = dw.log_row("rank", out, {"candidates": [1, 2]})
    assert row["decision"] == "human_review" and row["model_drift"] is True, row


@test("P1B-F", "a malformed config env var is one fail-closed JSON document, no traceback")
def _b_config_fail_closed():
    cases = [("TYPESAFE_RETRY_ATTEMPTS", "bad"), ("TYPESAFE_RETRY_ATTEMPTS", "0"),
             ("TYPESAFE_REQUEST_TIMEOUT", "nan"), ("TYPESAFE_WORKFLOW_DEADLINE_SECONDS", "inf"),
             ("TYPESAFE_MAX_STATE_CHARS", "-5"), ("TYPESAFE_ROUTER_CONFIDENCE", "high"),
             ("TYPESAFE_SYSTEMONE_URL", "file:///etc/passwd")]
    for var, value in cases:
        for script, args, stdin in (("route_task.py", ["--task", "x", "--no-log"], None),
                                    ("decision_workflows.py", ["rank", "--no-log"], "{}")):
            r = subprocess.run([sys.executable, "-B", os.path.join(ROOT, script)] + args,
                               input=stdin, capture_output=True, text=True, timeout=60,
                               env=rh.child_env({var: value}))
            assert r.returncode == 0, f"{script} {var}={value} exit {r.returncode}: {r.stderr[:200]}"
            assert "Traceback" not in r.stderr, f"{script} {var}={value} traceback"
            doc = json.loads(r.stdout)  # must be a single valid JSON document
            got = doc.get("policy", {}).get("recommended_executor") or doc.get("result", {}).get("decision")
            assert got in ("main_review", "human_review"), (script, var, got)


@test("P1B-F", "load_config reports content-free codes for every bad value")
def _b_config_codes():
    saved = {k: os.environ.get(k) for k in ("TYPESAFE_RETRY_ATTEMPTS", "TYPESAFE_REQUEST_TIMEOUT")}
    os.environ["TYPESAFE_RETRY_ATTEMPTS"] = "bad"
    os.environ["TYPESAFE_REQUEST_TIMEOUT"] = "9999999"
    try:
        try:
            tsc.load_config()
            raise AssertionError("bad configuration was accepted")
        except tsc.ConfigError as e:
            codes = tsc.config_errors()
            assert "TYPESAFE_RETRY_ATTEMPTS:not_a_number" in codes, codes
            assert any(c.startswith("TYPESAFE_REQUEST_TIMEOUT:out_of_range") for c in codes), codes
            assert "bad" not in str(e).replace("TYPESAFE_RETRY_ATTEMPTS:not_a_number", ""), str(e)
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        tsc.load_config()


@test("P1B-G", "injection warnings and provenance survive the partial path")
def _b_partial_injection():
    class T(rh.StubTransport):
        def __init__(self):
            super().__init__(answer_fn=rh.rank_answer_fn(inj={"c0": .99}), usage={"input_tokens": 55})
            self.n = 0
        def respond(self, body):
            self.n += 1
            return self.err(400) if self.n >= 2 else super().respond(body)
    t = T()
    with harness(t):
        out = dw.rank({"query": "q", "candidates": [{"id": f"c{i}", "text": "t" * 10}
                                                    for i in range(9)]})
    assert out["decision"] == "human_review", out["decision"]
    assert any(w.startswith("injection_vetoed:") for w in out["warnings"]), out["warnings"]
    assert any(w.startswith("partial_run_aborted:") for w in out["warnings"]), out["warnings"]
    row = next(r for r in out["ranking"] if r["id"] == "c0")
    assert row["exclusion_reason"] == "injection" and row["eligible"] is False, row


@test("P1B-H", "NaN/Infinity anywhere in the input is refused with ZERO paid calls")
def _b_nonfinite_input():
    for bad in (float("nan"), float("inf"), float("-inf")):
        for obj in ({"query": "q", "candidates": [{"id": "a", "w": bad}, {"id": "b"}]},
                    {"query": "q", "candidates": [{"id": "a", "n": {"deep": [1, bad]}}, {"id": "b"}]},
                    {"requirements": ["r"], "candidate": "c", "evidence": {"x": bad}},
                    {"action": "x", "score": bad}):
            wf = dw.rank if "candidates" in obj else (dw.verify if "requirements" in obj else dw.triage)
            t = rh.StubTransport(answer_fn=rh.rank_answer_fn())
            try:
                with harness(t):
                    wf(obj)
                raise AssertionError(f"non-finite accepted: {bad} in {list(obj)}")
            except ValueError as e:
                assert "non_finite_number" in str(e), str(e)
            assert t.calls == 0, "a paid call was made before the finiteness check"


@test("P1B-H", "non-finite API usage neither propagates nor breaks strict JSON")
def _b_nonfinite_usage():
    t = rh.StubTransport(answer_fn=rh.triage_answer_fn(), usage={"input_tokens": float("nan"),
                                                                 "output_tokens": 3})
    with harness(t):
        out = dw.triage({"action": "x"})
    assert "input_tokens" not in out["usage"], out["usage"]
    assert out["usage"]["output_tokens"] == 3, out["usage"]
    json.dumps(out, allow_nan=False)  # must not raise


@test("P1B-H", "the NaN JSON literal is rejected at both CLI boundaries")
def _b_nonfinite_cli():
    payload = '{"query":"q","candidates":[{"id":"a","w":NaN},{"id":"b"}]}'
    r = subprocess.run([sys.executable, "-B", os.path.join(ROOT, "decision_workflows.py"),
                        "rank", "--no-log"], input=payload, capture_output=True, text=True,
                       timeout=60, env=rh.child_env())
    doc = json.loads(r.stdout)
    assert r.returncode == 0 and doc["result"]["decision"] == "human_review", r.stdout[:300]
    assert "NaN" not in r.stdout or "non_finite" in r.stdout, r.stdout[:300]
    r2 = subprocess.run([sys.executable, "-B", os.path.join(ROOT, "route_task.py"),
                         "--stdin-json", "--no-log"], input='{"task":"x","context":{"w":Infinity}}',
                        capture_output=True, text=True, timeout=60, env=rh.child_env())
    doc2 = json.loads(r2.stdout)
    assert r2.returncode == 0 and doc2["policy"]["recommended_executor"] == "main_review", r2.stdout[:300]


@test("P1B-H", "emit never writes non-standard NaN JSON")
def _b_emit_strict():
    import io
    buf = io.StringIO()
    code = tsc.emit({"decision": "pass", "usage": {"input_tokens": float("nan")}}, stream=buf)
    text = buf.getvalue()
    assert "NaN" not in text, text
    doc = json.loads(text)
    assert doc["error_type"] == "NonSerializableResult" and code == tsc.EXIT_OK, doc


@test("P1B-I", "the suite registers only unique (finding, name) pairs")
def _b_unique_tests():
    names = [(r["finding"], r["test"]) for r in RESULTS]
    dupes = sorted({n for n in names if names.count(n) > 1})
    assert not dupes, dupes


@test("P1B-L", "oversized logs rotate and the rotation is bounded")
def _b_log_rotation():
    log = os.path.join(TMP, "rotate.jsonl")
    with open(log, "w", encoding="utf-8") as f:
        f.write("x" * 30_000 + "\n")
    assert tsc.rotate_log(log, max_bytes=10_000, keep=2) == "log_rotated:1"
    assert os.path.exists(log + ".1")
    with open(log, "w", encoding="utf-8") as f:
        f.write("y" * 30_000 + "\n")
    tsc.rotate_log(log, max_bytes=10_000, keep=2)
    assert os.path.exists(log + ".2"), sorted(os.listdir(TMP))
    assert not os.path.exists(log + ".3"), "rotation is not bounded"
    # A small log is never rotated.
    small = os.path.join(TMP, "small.jsonl")
    open(small, "w", encoding="utf-8").write("{}\n")
    assert tsc.rotate_log(small, max_bytes=10_000, keep=2) is None


@test("P1B-L", "log_sink is a replaceable seam used by every client")
def _b_log_sink_seam():
    captured = []
    original = tsc.log_sink
    try:
        tsc.log_sink = lambda row, path=None: captured.append((dict(row), path))
        decision_id, err = tsc.write_log({"event": "decision", "workflow": "probe"}, "/nonexistent/x")
        assert err is None and captured and captured[0][0]["workflow"] == "probe", captured
        assert captured[0][0]["schema_version"] == tsc.SCHEMA_VERSION
        assert decision_id
    finally:
        tsc.log_sink = original


@test("P1B-L", "the production log is refused by path, symlink AND hardlink identity")
def _b_prodlog_identity():
    # Non-destructive: the guard predicate is asserted BEFORE any write is
    # attempted, and the hardlink is removed immediately. A write is only ever
    # issued through a symlink, which the path check already refuses.
    from pathlib import Path
    assert tsc._is_production_log(Path(PRODLOG)), "direct path not recognised"
    link = os.path.join(TMP, "symlink-to-prod.jsonl")
    if not os.path.exists(link):
        os.symlink(PRODLOG, link)
    assert tsc._is_production_log(Path(link)), "symlink not recognised"
    _id, err = tsc.write_log({"event": "decision", "probe": True}, link)
    assert err == "offline_refuses_default_production_log", err
    hard = os.path.join(TMP, "hardlink-to-prod.jsonl")
    try:
        os.link(PRODLOG, hard)
    except OSError:
        return  # hardlinks unsupported on this filesystem: nothing to assert
    try:
        assert tsc._is_production_log(Path(hard)), "hardlink not recognised as the production log"
    finally:
        os.unlink(hard)
    # A hardlink to an UNRELATED file must not be misclassified.
    other = os.path.join(TMP, "other.jsonl")
    other_link = os.path.join(TMP, "other-link.jsonl")
    open(other, "w", encoding="utf-8").write("{}\n")
    try:
        os.link(other, other_link)
        assert not tsc._is_production_log(Path(other_link)), "false positive on an unrelated hardlink"
    except OSError:
        pass


@test("P1B-K", "no stray argparse-artifact file exists anywhere in the repository")
def _b_no_stray_help_file():
    from pathlib import Path
    strays = [p for p in Path(REPO_ROOT).rglob("*")
              if p.name.startswith("--") or p.name in ("-", "--help")]
    assert not strays, f"argparse artifact files in the repo: {[str(p) for p in strays]}"


@test("P1B-J", "replay fixtures are byte-identical to the frozen fixture manifest")
def _b_replay_fixture_hashes():
    import hashlib
    from pathlib import Path
    base = Path(rh.FIXTURES_DIR)
    manifest = json.load(open(base / "MANIFEST.sha256.json", encoding="utf-8"))
    assert manifest["file_count"] >= 6, manifest["file_count"]
    assert manifest["manifest_label"] == "synthetic-fixtures-frozen", manifest["manifest_label"]
    agg = hashlib.sha256()
    for entry in manifest["files"]:
        p = base / entry["name"]
        assert p.exists(), entry["name"]
        got = hashlib.sha256(p.read_bytes()).hexdigest()
        assert got == entry["sha256"], f"{entry['name']}: {got} != {entry['sha256']}"
        agg.update((entry["name"] + ":" + got + "\n").encode())
    # The aggregate must also match, so a file cannot be added or removed silently.
    assert agg.hexdigest() == manifest["aggregate_sha256"], "aggregate fixture hash drifted"
    # Fixtures must be declared synthetic, never derived from a real corpus.
    prov = (base / "provenance.txt").read_text(encoding="utf-8")
    assert "origin=synthetic" in prov, prov
    assert "derived_from_production_log=no" in prov, prov


@final_gate("PRIVACY: no secret-looking value appears in any fixture log produced by this suite")
def _pr3():
    bad = []
    for name in os.listdir(TMP):
        if not (name.endswith(".jsonl") or ".jsonl." in name):
            continue
        text = open(os.path.join(TMP, name), encoding="utf-8").read()
        for marker in ("sk-live", "test-key-not-real", "Bearer ", "SECRET TASK",
                       "AUDIT_SYNTHETIC", "AUDIT_ID_LEAK", "AUDIT_NOTE"):
            if marker in text:
                bad.append((name, marker))
    assert not bad, bad


@final_gate("PRIVACY: the production decision log is untouched by the whole suite")
def _pr4():
    import hashlib
    h = hashlib.sha256(open(PRODLOG, "rb").read()).hexdigest()
    assert h == PRODLOG_SHA256, h


# ============================================================ LICENSING
@test("LICENSE", "LICENSE and NOTICE exist and carry MIT attribution (audit P2-8)")
def _l1():
    root = os.path.dirname(ROOT)
    lic = open(os.path.join(root, "LICENSE"), encoding="utf-8").read()
    notice = open(os.path.join(root, "NOTICE"), encoding="utf-8").read()
    assert "MIT" in lic and "Permission is hereby granted" in lic, "LICENSE is not the MIT text"
    assert "Copyright" in lic, "LICENSE lacks a copyright line"
    assert "TypeSafe" in notice and "MIT" in notice, "NOTICE lacks upstream attribution"
    up = open(os.path.join(root, "references", "official-SKILL.md"), encoding="utf-8").read()
    assert "MIT" in up or "NOTICE" in up, "upstream copy lacks a license pointer"


@test("P1-6", "strict candidate/requirement validation rejects invalid shapes before egress")
def _strict_inputs():
    good = {"query": "q", "candidates": [{"id": "a"}, {"id": "b"}]}
    invalid = [dict(good, candidates=5), dict(good, candidates=[1, 2]),
               dict(good, candidates=[{"id": None}, {"id": "b"}]),
               dict(good, candidates=[{"id": "a", "required": "false"}, {"id": "b"}]),
               dict(good, requirements=[{"id": " ", "text": "x"}]),
               dict(good, requirements=[{"id": "r", "text": None}]),
               dict(good, requirements=["   "])]
    t = rh.StubTransport()
    with harness(t):
        for obj in invalid:
            try:
                dw.rank(obj)
                raise AssertionError("invalid input accepted")
            except ValueError:
                pass
        for reqs in ([None], [5], [" "], [{"text": None}]):
            try:
                dw.verify({"requirements": reqs, "candidate": "a"})
                raise AssertionError("invalid verify requirements accepted")
            except ValueError:
                pass
    assert t.calls == 0


@test("P1-7", "fractional counts, bools, null, NaN and Infinity are not valid selection numbers")
def _strict_numbers():
    for sel in ({"max_candidates": 2.1}, {"max_candidates": True}, {"max_per_domain": 1.9},
                {"minimum_score": None}, {"minimum_score": float("nan")},
                {"minimum_coverage_score": float("inf")}, {"target_context_chars": 1000.5}):
        try:
            dw.validate_selection(sel)
            raise AssertionError("invalid selection accepted")
        except ValueError:
            pass


@test("P1-1", "invalid scalar metadata cannot crash logging or lose the JSON response")
def _scalar_metadata():
    for wf, obj in (("rank", {"candidates": 42}), ("verify", {"requirements": 42})):
        r = subprocess.run([sys.executable, os.path.join(ROOT, "decision_workflows.py"), wf],
                           input=json.dumps(obj), text=True, capture_output=True,
                           env=rh.child_env(log_path=TESTLOG), timeout=60)
        assert r.returncode == 0, r.stderr
        out = json.loads(r.stdout)
        assert out["result"]["decision"] == "human_review" and out["decision_id"]


@test("P1-1", "common observability exists on every successful workflow and no-log output")
def _common_observability():
    for wf, t, obj in (
        ("rank", rh.StubTransport(answer_fn=rh.rank_answer_fn()),
         {"query": "q", "candidates": [{"id": "a"}, {"id": "b"}]}),
        ("verify", rh.StubTransport(answer_fn=rh.verify_answer_fn()),
         {"requirements": ["a"], "candidate": "a"}),
        ("triage", rh.StubTransport(answer_fn=rh.triage_answer_fn()), {"action": "inspect"})):
        with harness(t):
            result = getattr(dw, wf)(obj)
        row = dw.log_row(wf, result, obj)
        for key in ("schema_version", "decision_id", "workflow", "policy_version",
                    "model_requested", "models_served", "usage", "latency_ms"):
            assert key in row, (wf, key)
        assert row["api_calls"] > 0
    r = route_cli(["--task", "x", "--no-log"])
    out = json.loads(r.stdout)
    assert out["workflow"] == "route" and out["schema_version"] == tsc.SCHEMA_VERSION
    assert out["meta"]["decision_id"]


@test("P1-2", "remaining deadline caps transport timeout and includes all chunks")
def _deadline_actual():
    t = rh.StubTransport(answer_fn=rh.verify_answer_fn())
    with harness(t) as h:
        tsc.post_json({"state": {}, "questions": {}}, deadline=tsc.new_deadline(2), timeout=30)
        assert t.requests[0]["timeout"] <= 2
        h.clock.advance(3)
        try:
            tsc.post_json({"state": {}, "questions": {}}, deadline=h.clock.now - 1)
            raise AssertionError("expired deadline allowed a call")
        except tsc.TransportError:
            pass
        assert t.calls == 1


@test("P1-2", "HTTP-date Retry-After is supported and every 5xx retries")
def _retry_date():
    import time
    from email.utils import formatdate
    wait = tsc._retry_after_seconds({"retry-after": formatdate(time.time()+30, usegmt=True)})
    assert 28 <= wait <= 31, wait
    for status in (501, 507, 599):
        t = rh.StubTransport(script=[(status, 0), None])
        with harness(t):
            tsc.post_json({"state": {}, "questions": {}})
        assert t.calls == 2


@test("P0-1", "malformed first PAID response preserves usage instead of throwing it away")
def _partial_malformed():
    for wf, obj in (("rank", {"candidates": [{"id": "a"}, {"id": "b"}]}),
                    ("verify", {"requirements": ["a"], "candidate": "a"})):
        t = rh.StubTransport(answer_fn=lambda s,q: {}, usage={"input_tokens": 55})
        with harness(t):
            out = getattr(dw, wf)(obj)
        assert out["decision"] == "human_review", out["decision"]
        # The response was received and paid for but NOT accepted: accepted chunks
        # stay 0 while the known usage is preserved and the spend is visible.
        assert out["partial_usage"]["input_tokens"] == 55, out["partial_usage"]
        assert out["api_calls"] == 0 and out["api_responses_received"] == 1, out
        assert out["unaccepted_usage"]["input_tokens"] == 55, out
        assert "malformed_response_usage_preserved" in out["warnings"], out["warnings"]


@test("P0-1", "route also preflights full oversized payload with ZERO API calls")
def _route_preflight():
    t = rh.StubTransport(answer_fn=rh.route_answer_fn())
    with harness(t):
        out = rt.run("X"*300000, [])
    assert t.calls == 0 and out["policy"]["recommended_executor"] == "main_review"


@test("P1-3", "missing served model is drift, not implicit pin success")
def _missing_model():
    data = {"answers": rh.route_answer_fn()(None,None)}
    out = rt.apply_policy(data, 1)
    assert out["policy"]["recommended_executor"] == "main_review"
    assert out["meta"]["model_drift"]


@test("P0-3", "already-required coverage does not waste the only remaining coverage slot")
def _required_coverage():
    t = rh.StubTransport(answer_fn=rh.rank_answer_fn(
        cov={"req": {0:.9}, "redundant": {0:.9}, "needed": {1:.9}},
        fit={"req":.99, "redundant":.98, "needed":.4}))
    out = rank_via(t, {"mode":"shortlist", "requirements":["r0","r1"],
        "selection":{"max_candidates":2}, "candidates":[
        {"id":"req","text":"a","required":True},
        {"id":"redundant","text":"b"}, {"id":"needed","text":"c"}]})
    assert out["decision"] == "selected" and set(out["selected"]) == {"req", "needed"}


@test("FOUNDATION", "ReplayTransport replays a cassette and refuses exhaustion")
def _cassette_test():
    response = {"model": PINNED, "answers": {"x": {"noul":.4}}}
    t = rh.ReplayTransport([{"response":response}])
    with harness(t):
        out = tsc.post_json({"state":{},"questions":{}})
        assert out == response
        try:
            tsc.post_json({"state":{},"questions":{}})
            raise AssertionError("cassette exhaustion ignored")
        except AssertionError as e:
            assert "replay_exhausted" in str(e)


@test("P1-3", "triage model drift never returns allow_advisory")
def _triage_drift():
    t = rh.StubTransport(answer_fn=rh.triage_answer_fn(), model="jev-other")
    with harness(t):
        out = dw.triage({"action":"inspect"})
    assert out["decision"] == "human_review" and out["authorization"] is False


@test("CONTRACT", "CLI usage errors carry valid JSON and exit 2 for both clients")
def _usage_json():
    for script in ("decision_workflows.py", "route_task.py"):
        r = subprocess.run([sys.executable, os.path.join(ROOT,script), "--bad-flag"],
                           text=True,capture_output=True,env=rh.child_env(),timeout=60)
        assert r.returncode == 2
        assert json.loads(r.stdout)["error_type"] == "CLIUsageError"


@test("P0-3", "count saturation terminates with uncovered requirements, never false selected")
def _count_block():
    t = rh.StubTransport(answer_fn=rh.rank_answer_fn(cov={"a":{0:.9},"b":{1:.9}}))
    out = rank_via(t, {"mode":"shortlist", "requirements":["x","y"],
        "selection":{"max_candidates":1}, "candidates":[{"id":"a"},{"id":"b"}]})
    assert out["decision"] == "insufficient_coverage" and len(out["selected"]) == 1
    assert any(w.startswith("cover_candidate_blocked:") for w in out["warnings"])


@test("LICENSE", "upstream license copy is intact MIT with the recorded upstream copyright")
def _license_exact():
    from pathlib import Path
    copied = Path(REPO_ROOT) / 'references' / 'official-LICENSE'
    text = copied.read_text(encoding='utf-8')
    # Byte-level pin: the verbatim upstream MIT file must not drift silently.
    import hashlib
    assert hashlib.sha256(copied.read_bytes()).hexdigest() == UPSTREAM_LICENSE_SHA256, \
        "references/official-LICENSE no longer matches the verified upstream bytes"
    assert "MIT License" in text and "Permission is hereby granted" in text
    assert "TypeSafe" in text, "upstream copyright holder missing"
    notice = (Path(REPO_ROOT) / 'NOTICE').read_text(encoding='utf-8')
    assert UPSTREAM_COMMIT in notice, "NOTICE does not record the verified upstream commit"


def main():
    # Final gates run AFTER every registered regression, so they observe the
    # complete side-effect surface of the suite.
    for name, fn in FINAL_GATES:
        try:
            fn()
            RESULTS.append({"finding": "FINAL_GATE", "test": name, "ok": True})
        except Exception as e:  # noqa: BLE001
            RESULTS.append({"finding": "FINAL_GATE", "test": name, "ok": False,
                            "error": f"{type(e).__name__}: {e}"})
    failed = [r for r in RESULTS if not r["ok"]]
    by_finding = {}
    for r in RESULTS:
        by_finding.setdefault(r["finding"], {"total": 0, "failed": 0})
        by_finding[r["finding"]]["total"] += 1
        if not r["ok"]:
            by_finding[r["finding"]]["failed"] += 1
    unique = {(r["finding"], r["test"]) for r in RESULTS}
    summary = {"ok": not failed and len(unique) == len(RESULTS),
               "tests": len(RESULTS), "unique_tests": len(unique),
               "duplicates": len(RESULTS) - len(unique),
               "final_gates": len(FINAL_GATES),
               "failures": len(failed),
               "version": tsc.__version__, "schema_version": tsc.SCHEMA_VERSION,
               "prod_log_unchanged": PRODLOG_SHA256_AT_START == PRODLOG_SHA256,
               "by_finding": by_finding}
    if len(unique) != len(RESULTS):
        summary["duplicate_names"] = sorted({f"{f}|{t}" for f, t in
                                            [(r["finding"], r["test"]) for r in RESULTS]
                                            if [x["test"] for x in RESULTS].count(t) > 1})
    if failed or VERBOSE:
        summary["detail"] = failed if failed else RESULTS
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 1 if (failed or len(unique) != len(RESULTS)) else 0


if __name__ == "__main__":
    sys.exit(main())
