#!/usr/bin/env python3
"""Create sealed development-only gold from synthetic task literals."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PUBLIC = ROOT / "public"
OUT = ROOT / "development" / "sealed-gold"
MAP = {
 "p2-dev-en-01": {"r01":["c01","c02"],"r02":["c03"],"r03":["c04"]},
 "p2-dev-en-02": {"r01":["c01"],"r02":["c02"],"r03":["c03"],"r04":["c04"],"r05":["c05"]},
 "p2-dev-hr-01": {"r01":["c01"],"r02":["c02"],"r03":["c03","c04"]},
 "p2-dev-hr-02": {"r01":["c01"],"r02":["c02"],"r03":["c03"],"r04":["c04"],"r05":["c05"]},
}

def substantive(text):
    marker = " The document is synthetic and was authored only for development-set harness testing;"
    return text.split(marker,1)[0]

def main():
    OUT.mkdir(parents=True, exist_ok=True); rows=[]
    for p in sorted(PUBLIC.glob("p2-dev-*.json")):
        task=json.load(open(p,encoding="utf-8")); tid=task["task_id"]; cmap={c["candidate_id"]:c for c in task["candidates"]}
        reqs=[]; required=[]
        for rid,cids in MAP[tid].items():
            spans=[]
            for cid in cids:
                text=substantive(cmap[cid]["content"]); start=cmap[cid]["content"].index(text); end=start+len(text)
                spans.append({"candidate_id":cid,"start":start,"end":end,"text_sha256":hashlib.sha256(text.encode()).hexdigest()})
                if cid not in required: required.append(cid)
            reqs.append({"requirement_id":rid,"supporting_source_ids":cids,"support_spans":spans})
        gold={"task_id":tid,"required_source_ids":required,"primary_source_ids":required,"requirements":reqs,"known_contradictions":[]}
        q=OUT/f"{tid}.gold.json"; q.write_text(json.dumps(gold,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        b=q.read_bytes(); rows.append({"path":q.name,"bytes":len(b),"sha256":hashlib.sha256(b).hexdigest()})
    manifest={"kind":"development_only_gold","confirmatory_evidence":False,"files":rows,
              "aggregate_sha256":hashlib.sha256(json.dumps(rows,sort_keys=True,separators=(",", ":")).encode()).hexdigest()}
    (OUT/"MANIFEST.json").write_text(json.dumps(manifest,indent=2)+"\n")
    print(json.dumps({"ok":True,"tasks":len(rows),"aggregate_sha256":manifest["aggregate_sha256"]}))
if __name__=="__main__": main()
