#!/usr/bin/env python3
"""Fetch public scored sources and create bounded, reproducible no-gold extracts."""
import argparse, datetime as dt, hashlib, json, re, time
from pathlib import Path
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup

ROOT=Path(__file__).resolve().parent; PUB=ROOT/"public"; PROV=ROOT/"builder-provenance"; CACHE=ROOT/"source-cache"
UA="typesafe-decision-phase2-source-builder/1.0 (+https://github.com/vzornjak/typesafe-decision)"
MAX_DOWNLOAD=5_000_000; MAX_EXTRACT=12000; MIN_EXTRACT=150
SOFT=re.compile(r"\b(page not found|access denied|request access|just a moment|enable javascript|404)\b",re.I)

def clean_html(data):
 soup=BeautifulSoup(data,"html.parser")
 for x in soup(["script","style","noscript","svg","nav","footer","header","form"]): x.decompose()
 title=(soup.title.get_text(" ",strip=True) if soup.title else "")
 blocks=[]
 for node in soup.find_all(["h1","h2","h3","p","li","td","th","pre"]):
  s=" ".join(node.get_text(" ",strip=True).split())
  if len(s)>=25: blocks.append(s)
 seen=set(); uniq=[]
 for s in blocks:
  key=s.casefold()
  if key not in seen: seen.add(key); uniq.append(s)
 return title,"\n".join(uniq)

def fetch(url):
 last = None
 for attempt in range(3):
  try:
   r=requests.get(url,headers={"User-Agent":UA,"Accept":"text/html,text/plain;q=0.9,*/*;q=0.1"},timeout=30,allow_redirects=True,stream=True)
   break
  except (requests.ConnectionError, requests.Timeout, requests.exceptions.SSLError) as e:
   last = e
   if attempt == 2: raise
   time.sleep(1.0 * (attempt + 1))
 raw=b""
 for chunk in r.iter_content(65536):
  raw+=chunk
  if len(raw)>MAX_DOWNLOAD: break
 ctype=r.headers.get("content-type","").split(";",1)[0].lower()
 if ctype in {"text/html","application/xhtml+xml"}: title,text=clean_html(raw)
 elif ctype.startswith("text/"): title=""; text=raw.decode(r.encoding or "utf-8",errors="replace")
 else: title=""; text=""
 text="\n".join(x.strip() for x in text.splitlines() if x.strip())
 return r,title,text,hashlib.sha256(raw).hexdigest(),len(raw),ctype

def keywords(task):
 stop={"and","the","for","with","from","that","this","what","how","koje","kako","koji","treba","objasniti","usporediti","describe","explain","compare","include"}
 s=task["query"]+" "+" ".join(x["text"] for x in task["requirements"])
 return {w.casefold() for w in re.findall(r"[A-Za-zÀ-ž0-9-]{4,}",s) if w.casefold() not in stop}

def excerpt(text,keys):
 paras=[p for p in text.splitlines() if len(p)>=40]
 ranked=[]
 for i,p in enumerate(paras):
  words={w.casefold() for w in re.findall(r"[A-Za-zÀ-ž0-9-]{4,}",p)}; score=len(words&keys)
  ranked.append((-score,i,p))
 chosen=sorted(ranked)[:min(80,len(ranked))]
 chosen=sorted(chosen,key=lambda x:x[1]); out=[]; size=0
 for _,_,p in chosen:
  if size+len(p)+1>MAX_EXTRACT: continue
  out.append(p); size+=len(p)+1
 return "\n".join(out)

def main():
 ap=argparse.ArgumentParser(); ap.add_argument("--start",type=int,default=0); ap.add_argument("--limit",type=int,default=160); args=ap.parse_args()
 CACHE.mkdir(parents=True,exist_ok=True); jobs=[]
 for p in sorted(PUB.glob("p2-score-*.json")):
  task=json.load(open(p)); plan=json.load(open(PROV/f"{task['task_id']}.sources.json"));
  for cand,meta in zip(task["candidates"],plan["candidates"]): jobs.append((p,task,cand,meta))
 selected=jobs[args.start:args.start+args.limit]; changed={}; reports=[]
 for n,(p,task,cand,meta) in enumerate(selected,args.start+1):
  row={"task_id":task["task_id"],"candidate_id":cand["candidate_id"],"requested_url":meta["url"],"reuse_class":meta["reuse_class"],"fetched_at_utc":dt.datetime.now(dt.timezone.utc).isoformat()}
  try:
   r,title,text,rawsha,rawbytes,ctype=fetch(meta["url"]); ex=excerpt(text,keywords(task))
   row.update({"http_status":r.status_code,"final_url":r.url,"content_type":ctype,"title":title,"raw_sha256":rawsha,"raw_bytes":rawbytes,"extracted_chars":len(ex),"redirects":[x.url for x in r.history]})
   problems=[]
   if r.status_code!=200: problems.append(f"http_{r.status_code}")
   if ctype not in {"text/html","application/xhtml+xml","text/plain"}: problems.append("unsupported_content_type")
   if len(ex)<MIN_EXTRACT: problems.append("extract_too_short")
   preview=(title+"\n"+ex)[:3000]
   if SOFT.search(preview) and (len(ex)<1500 or re.search(r"\b(page not found|access denied|request access|just a moment|404)\b",title,re.I)):
    problems.append("soft_block_or_error_marker")
   row["status"]="accepted" if not problems else "rejected"; row["problems"]=problems
   if not problems:
    cand.update({"url":r.url,"title":title or cand["title"],"domain":re.sub(r'^www\.','',urlparse(r.url).hostname or cand["domain"]),"content":ex,"content_chars":len(ex)})
   (CACHE/f"{task['task_id']}__{cand['candidate_id']}.json").write_text(json.dumps(row,ensure_ascii=False,indent=2)+"\n")
  except Exception as e: row.update({"status":"rejected","problems":[f"{type(e).__name__}:{e}"]}); (CACHE/f"{task['task_id']}__{cand['candidate_id']}.json").write_text(json.dumps(row,ensure_ascii=False,indent=2)+"\n")
  changed[p]=task; reports.append(row); print(json.dumps({"n":n,"task":task["task_id"],"candidate":cand["candidate_id"],"status":row["status"],"problems":row.get("problems")}),flush=True); time.sleep(.15)
 for p,task in changed.items(): p.write_text(json.dumps(task,ensure_ascii=False,indent=2)+"\n")
 print(json.dumps({"ok":True,"attempted":len(reports),"accepted":sum(x['status']=='accepted' for x in reports),"rejected":sum(x['status']!='accepted' for x in reports)}))
if __name__=="__main__": main()
