#!/usr/bin/env python3
"""Fetch only source-plan amendment rows and update local checkpoint."""
import importlib.util,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('f',ROOT/'fetch_scored_sources.py');f=importlib.util.module_from_spec(spec);spec.loader.exec_module(f)
changes=json.load(open(ROOT/'builder-provenance'/__import__('os').environ.get('PHASE2_AMENDMENT','source-plan-amendment-01.json')))['changes']
for n,ch in enumerate(changes,1):
 task=json.load(open(ROOT/'public'/f"{ch['task_id']}.json")); cand=next(x for x in task['candidates'] if x['candidate_id']==ch['candidate_id'])
 meta=next(x for x in json.load(open(ROOT/'builder-provenance'/f"{ch['task_id']}.sources.json"))['candidates'] if x['candidate_id']==ch['candidate_id'])
 cand['url']=meta['url']; cand['domain']=meta['url'].split('/')[2].removeprefix('www.')
 row={'task_id':task['task_id'],'candidate_id':cand['candidate_id'],'requested_url':meta['url'],'reuse_class':meta['reuse_class'],'fetched_at_utc':f.dt.datetime.now(f.dt.timezone.utc).isoformat()}
 try:
  r,title,text,rawsha,rawbytes,ctype=f.fetch(meta['url']);ex=f.excerpt(text,f.keywords(task));problems=[]
  if r.status_code!=200:problems.append(f'http_{r.status_code}')
  if len(ex)<f.MIN_EXTRACT:problems.append('extract_too_short')
  preview=(title+'\n'+ex)[:3000]
  if f.SOFT.search(preview) and (len(ex)<1500 or f.re.search(r'\b(page not found|access denied|request access|just a moment|404)\b',title,f.re.I)):problems.append('soft_block_or_error_marker')
  row.update({'http_status':r.status_code,'final_url':r.url,'content_type':ctype,'title':title,'raw_sha256':rawsha,'raw_bytes':rawbytes,'extracted_chars':len(ex),'redirects':[x.url for x in r.history],'status':'accepted' if not problems else 'rejected','problems':problems})
  if not problems:cand.update({'url':r.url,'title':title or cand['title'],'domain':r.url.split('/')[2].removeprefix('www.'),'content':ex,'content_chars':len(ex)})
 except Exception as e:row.update({'status':'rejected','problems':[f'{type(e).__name__}:{e}']})
 (ROOT/'source-cache'/f"{task['task_id']}__{cand['candidate_id']}.json").write_text(json.dumps(row,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({'n':n,'task':task['task_id'],'candidate':cand['candidate_id'],'status':row['status'],'problems':row['problems']}))
