#!/usr/bin/env python3
"""Audit locally materialized scored corpus without gold access."""
import hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parent; OUT=ROOT/'materialized-scored'; PUB=ROOT/'public'; PROV=ROOT/'builder-provenance'
SECRET=[re.compile(r'sk-[A-Za-z0-9_-]{16,}'),re.compile(r'gh[pousr]_[A-Za-z0-9_]{20,}'),re.compile(r'-----BEGIN .*PRIVATE KEY-----')]
ERROR=re.compile(r'\b(page not found|access denied|request access|just a moment)\b',re.I)
def main():
 errors=[];rows=[];seen=set()
 for taskp in sorted(PUB.glob('p2-score-*.json')):
  task=json.load(open(taskp));plan=json.load(open(PROV/f"{task['task_id']}.sources.json"))
  for meta in plan['candidates']:
   cid=meta['candidate_id'];base=OUT/task['task_id']/cid;tp=base.with_suffix('.txt');mp=base.with_suffix('.json')
   if not tp.exists() or not mp.exists():errors.append(f'missing:{task["task_id"]}:{cid}');continue
   text=tp.read_text(encoding='utf-8');m=json.load(open(mp));limit=1200 if meta['reuse_class'] in {'unknown','link-or-short-excerpt-only'} else 12000
   if len(text)!=m['content_chars'] or hashlib.sha256(text.encode()).hexdigest()!=m['content_sha256']:errors.append(f'hash_or_length:{task["task_id"]}:{cid}')
   if not 150<=len(text)<=limit:errors.append(f'length_policy:{task["task_id"]}:{cid}:{len(text)}:{limit}')
   if ERROR.search(text[:1000]):errors.append(f'error_marker:{task["task_id"]}:{cid}')
   if any(p.search(text) for p in SECRET):errors.append(f'secret_pattern:{task["task_id"]}:{cid}')
   if meta['reuse_class']!=m['reuse_class']:errors.append(f'reuse_mismatch:{task["task_id"]}:{cid}')
   key=(task['task_id'],cid)
   if key in seen:errors.append(f'duplicate:{key}')
   seen.add(key);rows.append({'task_id':task['task_id'],'candidate_id':cid,'content_chars':len(text),'sha256':m['content_sha256'],'reuse_class':m['reuse_class'],'final_url':m['final_url']})
 if len(rows)!=160:errors.append(f'row_count:{len(rows)}')
 manifest={'kind':'local_materialized_scored_manifest','gold_visible':False,'rows':rows,'aggregate_sha256':hashlib.sha256(json.dumps(rows,sort_keys=True,separators=(",",":")).encode()).hexdigest(),'errors':errors,'ok':not errors}
 (OUT/'MANIFEST.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'ok':not errors,'rows':len(rows),'errors':errors,'aggregate_sha256':manifest['aggregate_sha256']},indent=2));return 0 if not errors else 1
if __name__=='__main__':raise SystemExit(main())
