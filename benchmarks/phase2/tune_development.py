#!/usr/bin/env python3
"""Select tuned shortlist config using development outputs only."""
import itertools
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent
PUB=ROOT/"public"; RUNS=ROOT/"development"/"jev-outputs"; GOLD=ROOT/"development"/"sealed-gold"
OUT=ROOT/"config"/"tuned-arm.json"
GRID={
 "max_candidates":[5,6,8], "target_context_chars":[4000,8000,50000],
 "minimum_score":[0.2,0.25,0.35], "minimum_coverage_score":[0.4,0.5,0.6], "max_per_domain":[1,2]
}

def load(p): return json.load(open(p,encoding="utf-8"))

def select(rows,candidates,requirements,cfg):
 import sys
 sys.path.insert(0,str(ROOT.parent.parent/"scripts")); import decision_workflows as dw
 return dw.shortlist(rows,candidates,requirements,cfg)

def main():
 tasks={load(p)["task_id"]:load(p) for p in PUB.glob("p2-dev-*.json")}
 gold={load(p)["task_id"]:load(p) for p in GOLD.glob("*.gold.json")}
 runs=[load(p) for p in RUNS.glob("*__rep*.json")]
 if len(tasks)!=4 or len(gold)!=4 or len(runs)!=12: raise SystemExit("incomplete development artifacts")
 results=[]
 keys=list(GRID)
 for vals in itertools.product(*(GRID[k] for k in keys)):
  cfg=dict(zip(keys,vals)); recalls=[]; required=[]; sizes=[]; complete=True
  for run in runs:
   tid=run["task_id"]; t=tasks[tid]; out=select(run["result"]["ranking"],
      [{"id":c["candidate_id"],"url":c["url"],"title":c["title"],"domain":c["domain"],"text":c["content"]} for c in t["candidates"]],t["requirements"],cfg)
   selected=set(out["selected"]); req=set(gold[tid]["required_source_ids"])
   required.append(len(selected&req)/len(req)); sizes.append(len(selected))
   covered=sum(any(cid in selected for cid in r["supporting_source_ids"]) for r in gold[tid]["requirements"])
   recalls.append(covered/len(gold[tid]["requirements"])); complete &= out["decision"]=="selected"
  results.append({"configuration":cfg,"mean_requirement_coverage":sum(recalls)/len(recalls),
                  "mean_required_source_recall":sum(required)/len(required),"mean_selected":sum(sizes)/len(sizes),"all_selected":complete})
 results.sort(key=lambda x:(-x["mean_requirement_coverage"],-x["mean_required_source_recall"],x["mean_selected"],
                            x["configuration"]["max_candidates"],x["configuration"]["target_context_chars"],
                            x["configuration"]["minimum_coverage_score"],x["configuration"]["minimum_score"],x["configuration"]["max_per_domain"]))
 best=results[0]
 doc={"schema_version":1,"status":"frozen_from_synthetic_development_set","selection_rule":"maximize mean requirement coverage, then required-source recall, then minimize selected count; deterministic config tie-break",
      "grid":GRID,"development_tasks":4,"development_runs":12,"best":best,"top_five":results[:5],"confirmatory_evidence":False}
 OUT.write_text(json.dumps(doc,indent=2)+"\n"); print(json.dumps({"ok":True,"best":best,"configs":len(results)},indent=2))
if __name__=="__main__": main()
