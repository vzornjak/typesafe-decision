#!/usr/bin/env python3
"""Deterministically generate the synthetic, public-safe replay fixtures.

Nothing here is derived from a real corpus, a real API transcript or a real
decision log. Candidate bodies are generated text, scores are authored
constants, and the "frozen" output is produced by running the real shortlist
pipeline against a stub transport that returns those authored scores. That
keeps the fixture set self-consistent: the replay test can reproduce the frozen
ranking rows bit-exactly without any network access.

Re-run with:  python3 tests/generate_fixtures.py
Then commit the regenerated tests/fixtures/ directory.
"""
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SCRIPTS = os.path.join(ROOT, "scripts")
OUT = os.path.join(HERE, "fixtures")
sys.path.insert(0, SCRIPTS)

os.environ["TYPESAFE_OFFLINE"] = "1"
os.environ["TYPESAFE_API_KEY"] = "test-key-not-real"
os.environ.setdefault("TYPESAFE_DEFAULT_LOG", os.path.join(OUT, ".unused-log.jsonl"))

import ts_common as tsc  # noqa: E402
import replay_harness as rh  # noqa: E402
import importlib.util  # noqa: E402

_spec = importlib.util.spec_from_file_location("decision_workflows",
                                               os.path.join(SCRIPTS, "decision_workflows.py"))
dw = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(dw)

QUERY = ("How do I publish a static documentation site behind a CDN with automatic TLS, "
         "cache invalidation and a rollback path?")

REQUIREMENTS = [
    {"id": "g1", "text": "Describes how to point a custom apex domain at the CDN edge."},
    {"id": "g2", "text": "Explains automatic TLS certificate issuance and renewal at the edge."},
    {"id": "g3", "text": "Documents cache invalidation / purge after a deploy."},
    {"id": "g4", "text": "Describes immutable build artifacts and atomic deploys."},
    {"id": "g5", "text": "Explains how to roll back to a previous deploy."},
    {"id": "g6", "text": "Covers cache-control and max-age headers for static assets."},
    {"id": "g7", "text": "Describes origin authentication between CDN and object storage."},
    {"id": "g8", "text": "Explains edge redirect and rewrite rules."},
    {"id": "g9", "text": "Covers access logs and basic request metrics."},
    {"id": "g10", "text": "Describes cost drivers: egress, requests and invalidations."},
    {"id": "g11", "text": "Explains the CI permissions needed for an automated deploy."},
]
RIDS = [r["id"] for r in REQUIREMENTS]

# Authored per-candidate synthetic scores. `cov` maps requirement id -> support.
# Numbers are hand-picked to exercise the selection policy, not measurements.
SPEC = [
    # id, host, authority, source_type, fit, useful, injection, coverage
    ("c01", "docs.edgehost.test", "primary", "official_documentation", 0.96, 0.93, 0.03,
     {"g1": 0.94, "g2": 0.91, "g3": 0.31, "g4": 0.22, "g5": 0.18, "g6": 0.27,
      "g7": 0.16, "g8": 0.24, "g9": 0.14, "g10": 0.19, "g11": 0.12}),
    ("c02", "docs.edgehost.test", "primary", "official_documentation", 0.94, 0.92, 0.02,
     {"g1": 0.26, "g2": 0.24, "g3": 0.92, "g4": 0.88, "g5": 0.35, "g6": 0.29,
      "g7": 0.18, "g8": 0.21, "g9": 0.17, "g10": 0.22, "g11": 0.15}),
    ("c03", "docs.edgehost.test", "primary", "official_documentation", 0.92, 0.90, 0.02,
     {"g1": 0.21, "g2": 0.19, "g3": 0.33, "g4": 0.30, "g5": 0.93, "g6": 0.28,
      "g7": 0.20, "g8": 0.23, "g9": 0.16, "g10": 0.18, "g11": 0.14}),
    ("c04", "docs.edgehost.test", "primary", "official_documentation", 0.90, 0.88, 0.03,
     {"g1": 0.18, "g2": 0.22, "g3": 0.27, "g4": 0.25, "g5": 0.24, "g6": 0.91,
      "g7": 0.89, "g8": 0.32, "g9": 0.19, "g10": 0.21, "g11": 0.17}),
    ("c05", "standards.example.test", "primary", "standard", 0.72, 0.70, 0.02,
     {"g1": 0.12, "g2": 0.44, "g3": 0.15, "g4": 0.13, "g5": 0.11, "g6": 0.62,
      "g7": 0.19, "g8": 0.14, "g9": 0.12, "g10": 0.10, "g11": 0.09}),
    ("c06", "ci.example-runner.test", "primary", "official_documentation", 0.78, 0.76, 0.02,
     {"g1": 0.13, "g2": 0.15, "g3": 0.22, "g4": 0.31, "g5": 0.26, "g6": 0.14,
      "g7": 0.21, "g8": 0.12, "g9": 0.20, "g10": 0.16, "g11": 0.90}),
    ("c07", "blog.someengineer.test", "secondary", "blog", 0.64, 0.61, 0.03,
     {"g1": 0.35, "g2": 0.33, "g3": 0.41, "g4": 0.29, "g5": 0.38, "g6": 0.31,
      "g7": 0.22, "g8": 0.66, "g9": 0.24, "g10": 0.27, "g11": 0.25}),
    ("c08", "blog.someengineer.test", "secondary", "blog", 0.58, 0.55, 0.04,
     {"g1": 0.24, "g2": 0.22, "g3": 0.28, "g4": 0.21, "g5": 0.23, "g6": 0.25,
      "g7": 0.19, "g8": 0.27, "g9": 0.71, "g10": 0.69, "g11": 0.20}),
    ("c09", "forum.example-qa.test", "community", "forum", 0.47, 0.44, 0.05,
     {"g1": 0.18, "g2": 0.16, "g3": 0.19, "g4": 0.15, "g5": 0.17, "g6": 0.14,
      "g7": 0.13, "g8": 0.16, "g9": 0.15, "g10": 0.12, "g11": 0.18}),
    ("c10", "forum.example-qa.test", "community", "forum", 0.41, 0.39, 0.04,
     {"g1": 0.15, "g2": 0.13, "g3": 0.17, "g4": 0.12, "g5": 0.14, "g6": 0.13,
      "g7": 0.11, "g8": 0.12, "g9": 0.13, "g10": 0.11, "g11": 0.15}),
    ("c11", "news.example-tech.test", "secondary", "news", 0.38, 0.36, 0.03,
     {"g1": 0.11, "g2": 0.10, "g3": 0.12, "g4": 0.11, "g5": 0.10, "g6": 0.12,
      "g7": 0.09, "g8": 0.11, "g9": 0.12, "g10": 0.13, "g11": 0.10}),
    ("c12", "news.example-tech.test", "secondary", "news", 0.34, 0.32, 0.03,
     {"g1": 0.10, "g2": 0.09, "g3": 0.11, "g4": 0.10, "g5": 0.09, "g6": 0.11,
      "g7": 0.08, "g8": 0.10, "g9": 0.11, "g10": 0.12, "g11": 0.09}),
    ("c13", "vendor.example-cdn2.test", "primary", "official_documentation", 0.69, 0.66, 0.03,
     {"g1": 0.52, "g2": 0.48, "g3": 0.44, "g4": 0.42, "g5": 0.40, "g6": 0.38,
      "g7": 0.36, "g8": 0.34, "g9": 0.32, "g10": 0.30, "g11": 0.28}),
    ("c14", "vendor.example-cdn2.test", "secondary", "marketing", 0.31, 0.29, 0.06,
     {"g1": 0.14, "g2": 0.12, "g3": 0.13, "g4": 0.11, "g5": 0.12, "g6": 0.10,
      "g7": 0.09, "g8": 0.11, "g9": 0.10, "g10": 0.21, "g11": 0.08}),
    ("c15", "aggregator.example-list.test", "community", "aggregator", 0.28, 0.26, 0.07,
     {"g1": 0.09, "g2": 0.08, "g3": 0.10, "g4": 0.09, "g5": 0.08, "g6": 0.09,
      "g7": 0.07, "g8": 0.08, "g9": 0.09, "g10": 0.10, "g11": 0.07}),
    ("c16", "spam.example-injected.test", "community", "blog", 0.55, 0.52, 0.93,
     {"g1": 0.30, "g2": 0.28, "g3": 0.31, "g4": 0.27, "g5": 0.29, "g6": 0.26,
      "g7": 0.24, "g8": 0.25, "g9": 0.23, "g10": 0.22, "g11": 0.21}),
]

# Distinct vocabulary per candidate so the 5-gram near-duplicate detector
# (Jaccard >= 0.86) never fires on this synthetic corpus.
WORDS = ("alpha bravo charlie delta echo foxtrot golf hotel india juliett kilo lima mike "
         "november oscar papa quebec romeo sierra tango uniform victor whiskey xray yankee "
         "zulu anchor beacon cipher dossier ember").split()

TOPIC_LINES = {
    "g1": "Apex domain records are delegated to the edge anycast address.",
    "g2": "Certificates are issued automatically and renewed before expiry.",
    "g3": "A purge request invalidates cached objects by path prefix.",
    "g4": "Each build produces an immutable, content-addressed artifact.",
    "g5": "A previous deploy can be re-pointed to in a single operation.",
    "g6": "Static assets are served with a long max-age and revalidation.",
    "g7": "The edge authenticates to object storage with a scoped credential.",
    "g8": "Redirect and rewrite rules are evaluated at the edge.",
    "g9": "Request logs and basic latency metrics are exported.",
    "g10": "Cost is driven by egress volume, request count and invalidations.",
    "g11": "The CI role needs deploy and purge permissions, nothing more.",
}


def body_for(idx, cid, cov, target_chars=2400):
    """Deterministic, distinct synthetic prose of roughly `target_chars`."""
    lead = [f"Synthetic document {cid}. This text is generated for regression tests "
            f"and describes no real product."]
    for rid in RIDS:
        weight = cov[rid]
        n = 1 + int(weight * 4)
        for k in range(n):
            lead.append(f"{TOPIC_LINES[rid]} ({cid}/{rid}/{k})")
    out = " ".join(lead)
    # Pad with a per-candidate deterministic word stream, unique per candidate.
    i = 0
    while len(out) < target_chars:
        w = WORDS[(idx * 7 + i * 3) % len(WORDS)]
        out += f" {w}{(idx * 31 + i) % 997}"
        i += 1
    return out[:target_chars]


def build_input():
    cands = []
    for idx, (cid, host, authority, stype, fit, useful, inj, cov) in enumerate(SPEC):
        text = body_for(idx, cid, cov)
        cands.append({
            "id": cid,
            "url": f"https://{host}/synthetic/{cid}",
            "title": f"Synthetic source {cid} — edge delivery notes",
            "authority": authority,
            "source_type": stype,
            "snippets": [{"section": "Synthetic body", "text": text}],
        })
    return {
        "mode": "shortlist",
        "query": QUERY,
        "criteria": ["primary source preferred", "covers the deploy lifecycle"],
        "requirements": REQUIREMENTS,
        "selection": {"max_candidates": 8, "target_context_chars": 50000,
                      "minimum_score": 0.25, "minimum_coverage_score": 0.4,
                      "max_per_domain": 4},
        "candidates": cands,
    }


def stub_transport():
    cov = {cid: {RIDS.index(rid): v for rid, v in c.items()}
           for (cid, _h, _a, _s, _f, _u, _i, c) in SPEC}
    fit = {cid: f for (cid, _h, _a, _s, f, _u, _i, _c) in SPEC}
    useful = {cid: u for (cid, _h, _a, _s, _f, u, _i, _c) in SPEC}
    inj = {cid: i for (cid, _h, _a, _s, _f, _u, i, _c) in SPEC}
    return rh.StubTransport(answer_fn=rh.rank_answer_fn(cov=cov, inj=inj, fit=fit, useful=useful),
                            model=tsc.MODEL, usage={"input_tokens": 0, "output_tokens": 0})


def run(obj, transport):
    saved = tsc.TRANSPORT
    saved_sleep, saved_mono = tsc.SLEEP, tsc.MONOTONIC
    clock = rh.Clock()
    tsc.set_transport(transport)
    tsc.SLEEP, tsc.MONOTONIC = clock.sleep, clock.monotonic
    try:
        return dw.rank(obj)
    finally:
        tsc.set_transport(saved)
        tsc.SLEEP, tsc.MONOTONIC = saved_sleep, saved_mono


def build_winner_pair():
    inp = {
        "query": "Which synthetic note best explains atomic deploys?",
        "criteria": ["explicit", "primary source"],
        "candidates": [
            {"id": "w1", "title": "Atomic deploy notes",
             "snippet": "Each build is immutable and the symlink flip is atomic."},
            {"id": "w2", "title": "Unrelated changelog",
             "snippet": "Adds a dark theme toggle to the settings page."},
            {"id": "w3", "title": "Partial notes",
             "snippet": "Mentions deploys but not atomicity or rollback."},
        ],
    }
    t = rh.StubTransport(answer_fn=rh.rank_answer_fn(
        fit={"w1": 0.95, "w2": 0.12, "w3": 0.55},
        useful={"w1": 0.93, "w2": 0.10, "w3": 0.50},
        inj={"w1": 0.02, "w2": 0.02, "w3": 0.03}),
        model=tsc.MODEL, usage={"input_tokens": 0, "output_tokens": 0})
    return inp, run(inp, t)


def write_json(name, obj):
    p = os.path.join(OUT, name)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=1, ensure_ascii=False, sort_keys=False)
        f.write("\n")
    return p


def main():
    os.makedirs(OUT, exist_ok=True)
    inp = build_input()
    result = run(inp, stub_transport())
    write_json("rank_shortlist_input.json", inp)
    write_json("rank_shortlist_output.json",
               {"workflow": "rank", "version": tsc.__version__, "advisory_only": True,
                "synthetic": True, "result": result})

    winp, wout = build_winner_pair()
    write_json("rank_winner_input.json", winp)
    write_json("rank_winner_output.json",
               {"workflow": "rank", "version": tsc.__version__, "advisory_only": True,
                "synthetic": True, "result": wout})

    # Gold labels: authored, not human-annotated. `highly_relevant` intentionally
    # contains four sources from one domain so that the documented default
    # max_per_domain=2 demonstrably recalls fewer of them than max_per_domain=4.
    gold = {
        "synthetic": True,
        "generated_by": "tests/generate_fixtures.py",
        "note": ("Fully synthetic labels over a generated corpus. These are NOT human "
                 "relevance judgements and carry no evaluation authority. They exist only "
                 "so the regression suite can assert a relative policy property."),
        "user_query": QUERY,
        "gold_sources": {
            "note": "authored labels, synthetic corpus",
            "highly_relevant": ["c01", "c02", "c03", "c04", "c06"],
            "partially_relevant": ["c05", "c07", "c08", "c13"],
            "irrelevant_or_noise": ["c09", "c10", "c11", "c12", "c14", "c15", "c16"],
        },
        "leakage_control": ("The requirements sent to the model are the same list used to "
                            "label coverage, so this fixture must never be cited as an "
                            "independent quality measurement."),
    }
    write_json("query_and_gold.json", gold)

    with open(os.path.join(OUT, "provenance.txt"), "w", encoding="utf-8") as f:
        f.write(
            "origin=synthetic\n"
            "generator=tests/generate_fixtures.py\n"
            "derived_from_real_corpus=no\n"
            "derived_from_real_api_transcript=no\n"
            "derived_from_production_log=no\n"
            "personal_data=none\n"
            "purpose=deterministic offline replay and selection-policy regressions\n")

    names = sorted(n for n in os.listdir(OUT) if n != "MANIFEST.sha256.json"
                   and not n.startswith("."))
    files = []
    agg = hashlib.sha256()
    for n in names:
        h = hashlib.sha256(open(os.path.join(OUT, n), "rb").read()).hexdigest()
        files.append({"name": n, "sha256": h})
        agg.update((n + ":" + h + "\n").encode())
    manifest = {
        "manifest_label": "synthetic-fixtures-frozen",
        "root": "tests/fixtures",
        "file_count": len(files),
        "files": files,
        "aggregate_sha256": agg.hexdigest(),
        "note": "Synthetic, public-safe replay inputs. Regenerate with tests/generate_fixtures.py.",
    }
    write_json("MANIFEST.sha256.json", manifest)
    print(json.dumps({"ok": True, "fixtures": len(files),
                      "shortlist_decision": result["decision"],
                      "selected": result["selected"],
                      "warnings": result["warnings"],
                      "winner_decision": wout["decision"],
                      "aggregate_sha256": manifest["aggregate_sha256"]}, indent=2))


if __name__ == "__main__":
    main()
