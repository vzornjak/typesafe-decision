#!/usr/bin/env python3
"""Materialize locally licensed/bounded scored extracts from audited sources."""
import argparse,hashlib,json,re
from pathlib import Path
import importlib.util
ROOT=Path(__file__).resolve().parent; PUB=ROOT/'public'; PROV=ROOT/'builder-provenance'; CACHE=ROOT/'source-cache'; OUT=ROOT/'materialized-scored'
spec=importlib.util.spec_from_file_location('fetch',ROOT/'fetch_scored_sources.py');f=importlib.util.module_from_spec(spec);spec.loader.exec_module(f)
LIMIT={'public-domain':12000,'open-reuse':12000,'link-or-short-excerpt-only':1200,'unknown':1200}
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--start',type=int,default=0);ap.add_argument('--limit',type=int,default=160);a=ap.parse_args();OUT.mkdir(parents=True,exist_ok=True)
 jobs=[]
 for p in sorted(PUB.glob('p2-score-*.json')):
  task=json.load(open(p));plan=json.load(open(PROV/f"{task['task_id']}.sources.json"));
  for cand,meta in zip(task['candidates'],plan['candidates']):jobs.append((task,cand,meta))
 ok=bad=0
 for n,(task,cand,meta) in enumerate(jobs[a.start:a.start+a.limit],a.start+1):
  key=f"{task['task_id']}__{cand['candidate_id']}"; brow=CACHE/'browser-fallback'/f'{key}.json'; textp=CACHE/'browser-fallback'/f'{key}.txt'; shell=CACHE/f'{key}.json'; text='';transport='';source={}
  try:
   if brow.exists() and json.load(open(brow)).get('status')=='accepted' and textp.exists():
    source=json.load(open(brow));text=textp.read_text(encoding='utf-8');transport='browser'
   else:
    r,title,body,rawsha,rawbytes,ctype=f.fetch(meta['url']);text=f.excerpt(body,f.keywords(task));transport='shell'
    source={'requested_url':meta['url'],'final_url':r.url,'http_status':r.status_code,'content_type':ctype,'title':title,'raw_sha256':rawsha,'raw_bytes':rawbytes,'redirects':[x.url for x in r.history]}
    if r.status_code!=200 or len(text)<150:raise ValueError(f'invalid_refetch:{r.status_code}:{len(text)}')
   limit=LIMIT[meta['reuse_class']];text=text[:limit].strip()
   if len(text)<150:raise ValueError(f'materialized_too_short:{len(text)}')
   taskdir=OUT/task['task_id'];taskdir.mkdir(parents=True,exist_ok=True);(taskdir/f"{cand['candidate_id']}.txt").write_text(text,encoding='utf-8')
   row={'task_id':task['task_id'],'candidate_id':cand['candidate_id'],'requested_url':meta['url'],'final_url':source.get('final_url',meta['url']),'title':source.get('title',''),'reuse_class':meta['reuse_class'],'excerpt_limit':limit,'transport':transport,'content_chars':len(text),'content_sha256':hashlib.sha256(text.encode()).hexdigest(),'attribution':f"Source: {source.get('final_url',meta['url'])}; accessed during Phase 2 corpus build; reuse class: {meta['reuse_class']}."}
   (taskdir/f"{cand['candidate_id']}.json").write_text(json.dumps(row,ensure_ascii=False,indent=2)+'\n');ok+=1;status='accepted'
  except Exception as e:bad+=1;status=f'rejected:{type(e).__name__}:{e}'
  print(json.dumps({'n':n,'task':task['task_id'],'candidate':cand['candidate_id'],'status':status}),flush=True)
 print(json.dumps({'ok':bad==0,'accepted':ok,'rejected':bad}))
if __name__=='__main__':main()
