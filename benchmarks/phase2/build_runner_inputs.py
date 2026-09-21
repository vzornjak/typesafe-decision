#!/usr/bin/env python3
"""Build the local runner-visible scored bundle from audited materialization."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent; PUB=ROOT/'public'; MAT=ROOT/'materialized-scored'; OUT=ROOT/'runner-inputs'; PROV=ROOT/'builder-provenance'
def main():
 OUT.mkdir(parents=True,exist_ok=True);rows=[]
 for p in sorted(PUB.glob('p2-score-*.json')):
  task=json.load(open(p));plan=json.load(open(PROV/f"{task['task_id']}.sources.json")); candidates=[]
  for c,m in zip(task['candidates'],plan['candidates']):
   text=(MAT/task['task_id']/f"{c['candidate_id']}.txt").read_text(encoding='utf-8');meta=json.load(open(MAT/task['task_id']/f"{c['candidate_id']}.json"))
   candidates.append({'candidate_id':c['candidate_id'],'url':meta['final_url'],'title':meta['title'] or c['title'],'domain':meta['final_url'].split('/')[2].removeprefix('www.'),'published_at_if_observable':None,'content':text,'content_chars':len(text)})
  out={k:task[k] for k in ('task_id','language','domain','complexity','query','requirements')}|{'candidates':candidates}
  if sum(x['content_chars'] for x in candidates)>120000:raise ValueError(f"context ceiling: {task['task_id']}")
  q=OUT/f"{task['task_id']}.json";q.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');b=q.read_bytes();rows.append({'path':q.name,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()})
 manifest={'kind':'local_runner_visible_scored_bundle','gold_visible':False,'tasks':16,'candidates':160,'files':rows,'aggregate_sha256':hashlib.sha256(json.dumps(rows,sort_keys=True,separators=(",",":")).encode()).hexdigest()}
 (OUT/'MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n');print(json.dumps({'ok':True,'tasks':16,'candidates':160,'aggregate_sha256':manifest['aggregate_sha256']},indent=2))
if __name__=='__main__':main()
