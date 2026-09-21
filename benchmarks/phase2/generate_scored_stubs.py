#!/usr/bin/env python3
"""Parse the reviewed markdown proposal into runner-visible scored task stubs."""
import json
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parent
SOURCE=ROOT/"source-proposal.md"
OUT=ROOT/"public"
DOMAIN_MAP={
 "Software / technical documentation":"software_technical",
 "Public policy / regulation":"public_policy_regulation",
 "Science / health evidence":"science_health",
 "Consumer / product comparison":"consumer_product",
}

def main():
 text=SOURCE.read_text(encoding="utf-8")
 scored=text.split("# B. Scored zadaci",1)[1].split("# Napomene o licenciranju",1)[0]
 domain=None; tasks=[]
 lines=scored.splitlines(); i=0
 while i<len(lines):
  line=lines[i]
  if line.startswith("## "):
   d=line[3:].strip()
   if d in DOMAIN_MAP: domain=DOMAIN_MAP[d]
  m=re.match(r"### \d+\. `([^`]+)`",line)
  if not m: i+=1; continue
  opaque=m.group(1); block=[]; i+=1
  while i<len(lines) and not lines[i].startswith("### ") and not (lines[i].startswith("## ") and lines[i][3:].strip() in DOMAIN_MAP):
   block.append(lines[i]); i+=1
  s="\n".join(block)
  lang=re.search(r"\*\*Jezik:\*\* (HR|EN)",s).group(1).lower()
  complexity=re.search(r"\*\*Složenost:\*\* (Moderate|Complex)",s).group(1).lower()
  query=re.search(r"\*\*Prirodni korisnički upit:\*\*\s+“(.+?)”",s,re.S).group(1).strip()
  reqpart=s.split("**Zahtjevi izvedeni iz upita:**",1)[1].split("**Kandidatski izvori:**",1)[0]
  reqs=[re.sub(r"^\d+\.\s*","",x).strip() for x in reqpart.splitlines() if re.match(r"\s*\d+\. ",x)]
  urlpart=s.split("**Kandidatski izvori:**",1)[1]
  urls=re.findall(r"https://\S+",urlpart)
  seq=sum(1 for t in tasks if t['language']==lang)+1
  tid=f"p2-score-{lang}-{seq:02d}"
  candidates=[]
  for n,url in enumerate(urls,1):
   url=url.rstrip(').,')
   host=re.sub(r'^www\.','',url.split('/')[2].lower())
   placeholder=f"PENDING VERIFIED PUBLIC EXTRACT FOR {opaque} CANDIDATE {n}. This placeholder is not valid benchmark content and must be replaced before input lock."
   candidates.append({"candidate_id":f"c{n:02d}","url":url,"title":f"Pending source {n}","domain":host,
                      "published_at_if_observable":None,"content":placeholder,"content_chars":len(placeholder)})
  tasks.append({"task_id":tid,"language":lang,"domain":domain,"complexity":complexity,"query":query,
                "requirements":[{"id":f"r{n:02d}","text":r} for n,r in enumerate(reqs,1)],"candidates":candidates,
                "_builder_provenance":{"opaque_proposal_id":opaque,"status":"pending_source_audit_and_extract"}})
 for t in tasks:
  # Provenance is kept separately because the public schema intentionally forbids it.
  prov=t.pop('_builder_provenance'); p=OUT/f"{t['task_id']}.json"; p.write_text(json.dumps(t,ensure_ascii=False,indent=2)+"\n")
  (OUT/f"{t['task_id']}.builder.json").write_text(json.dumps(prov,indent=2)+"\n")
 print(json.dumps({"ok":True,"scored_tasks":len(tasks),"hr":sum(t['language']=='hr' for t in tasks),"en":sum(t['language']=='en' for t in tasks)},indent=2))
if __name__=="__main__": main()
