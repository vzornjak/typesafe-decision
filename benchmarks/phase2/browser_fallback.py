#!/usr/bin/env python3
"""Browser-transport fallback for unresolved scored sources."""
import datetime as dt, hashlib, json, re, subprocess, time
from pathlib import Path

ROOT=Path(__file__).resolve().parent; CACHE=ROOT/"source-cache"; OUT=CACHE/"browser-fallback"; OUT.mkdir(parents=True,exist_ok=True)
ERROR=re.compile(r"\b(page not found|access denied|request access|just a moment|404)\b",re.I)

def call(action, **kw):
 obj={"action":action,"tool_title":"Phase 2 browser source fallback",**kw}
 r=subprocess.run(["minis-browser-use","--json",json.dumps(obj)],capture_output=True,text=True,timeout=60)
 if r.returncode: raise RuntimeError(r.stderr[-300:] or f"browser_rc_{r.returncode}")
 return json.loads(r.stdout)

def main():
 unresolved=[]
 for p in sorted(CACHE.glob("*.json")):
  x=json.load(open(p))
  if x.get("status")!="accepted": unresolved.append(x)
 for n,x in enumerate(unresolved,1):
  row={k:x.get(k) for k in ("task_id","candidate_id","requested_url","reuse_class")}; row["fetched_at_utc"]=dt.datetime.now(dt.timezone.utc).isoformat(); problems=[]
  try:
   nav=call("navigate",url=x["requested_url"]); read=call("get_readable")
   data=read.get("data",read); text=data.get("text","") or read.get("text",""); final=data.get("page_url") or nav.get("data",{}).get("page_url") or x["requested_url"]
   title=""; m=re.match(r"Title:\s*(.*?)\nText",text,re.S)
   if m: title=m.group(1).strip()
   body=text.split("Text",1)[1].lstrip(" (0123456789chars):\n") if "Text" in text else text
   body="\n".join(s.strip() for s in body.splitlines() if s.strip())[:12000]
   if len(body)<150: problems.append("browser_extract_too_short")
   if ERROR.search(title) or (len(body)<1500 and ERROR.search(body[:1000])): problems.append("browser_soft_error")
   row.update({"transport":"browser","final_url":final,"title":title,"extracted_chars":len(body),"content_sha256":hashlib.sha256(body.encode()).hexdigest(),"status":"accepted" if not problems else "rejected","problems":problems})
   if not problems: (OUT/f"{x['task_id']}__{x['candidate_id']}.txt").write_text(body,encoding="utf-8")
  except Exception as e: row.update({"transport":"browser","status":"rejected","problems":[f"{type(e).__name__}:{e}"]})
  (OUT/f"{x['task_id']}__{x['candidate_id']}.json").write_text(json.dumps(row,ensure_ascii=False,indent=2)+"\n")
  print(json.dumps({"n":n,"task":x['task_id'],"candidate":x['candidate_id'],"status":row['status'],"problems":row['problems']}),flush=True); time.sleep(.1)
 print(json.dumps({"ok":True,"attempted":len(unresolved)}))
if __name__=="__main__":main()
