#!/usr/bin/env python3
"""Analyze development-only Jev runs and frozen tuned configuration."""
import json
from pathlib import Path
from itertools import combinations

ROOT=Path(__file__).resolve().parent
RUNS=ROOT/"development"/"jev-outputs"
GOLD=ROOT/"development"/"sealed-gold"
PRICE=0.042

def load(p): return json.load(open(p,encoding="utf-8"))
def jaccard(a,b):
 a,b=set(a),set(b); return len(a&b)/len(a|b) if a|b else 1.0

def main():
 runs=[load(p) for p in sorted(RUNS.glob("*__rep*.json"))]
 gold={load(p)["task_id"]:load(p) for p in GOLD.glob("*.gold.json")}
 by={}
 for x in runs: by.setdefault(x["task_id"],[]).append(x)
 tasks=[]; all_j=[]; total_in=0; total_out=0
 for tid,rs in sorted(by.items()):
  sels=[r["result"]["selected"] for r in rs]; js=[jaccard(a,b) for a,b in combinations(sels,2)]; all_j+=js
  req=set(gold[tid]["required_source_ids"]); recalls=[len(set(s)&req)/len(req) for s in sels]
  usages=[r["result"].get("usage",{}) for r in rs]; total_in+=sum(u.get("input_tokens",0) for u in usages); total_out+=sum(u.get("output_tokens",0) for u in usages)
  tasks.append({"task_id":tid,"selections":sels,"pairwise_jaccard":js,"required_source_recall":recalls})
 report={"kind":"development_only_analysis","confirmatory_evidence":False,"tasks":tasks,
   "runs":len(runs),"jev_api_calls":sum(r["result"].get("api_calls",0) for r in runs),
   "jev_input_tokens":total_in,"jev_output_tokens_free":total_out,"estimated_jev_cost_usd":round(total_in/1_000_000*PRICE,8),
   "mean_pairwise_selection_jaccard":sum(all_j)/len(all_j),
   "all_default_required_source_recall":sum(t==1 for x in tasks for t in x["required_source_recall"])/len(runs)}
 p=ROOT/"development"/"analysis.json"; p.write_text(json.dumps(report,indent=2)+"\n"); print(json.dumps(report,indent=2))
if __name__=="__main__":main()
