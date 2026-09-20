#!/usr/bin/env python3
"""Legacy offline/fail-safe regression suite (pre-Phase-1 behaviour contract).

Phase 1 additions live in tests_phase1.py. This file keeps the original
assertions so backward-compatible behaviour stays locked, updated only where the
documented contract intentionally changed (pinned model in stubs, request-aware
chunker signature, mandatory shortlist requirements).
"""
import importlib.util, json, os, subprocess, sys
ROOT=os.path.dirname(os.path.abspath(__file__)); route=os.path.join(ROOT,"route_task.py"); flow=os.path.join(ROOT,"decision_workflows.py")
sys.path.insert(0,ROOT)
os.environ["TYPESAFE_OFFLINE"]="1"
os.environ["TYPESAFE_ROUTER_MODEL"]="jev-1.13.0"
os.environ.pop("TYPESAFE_ALLOW_MODEL_DRIFT",None)
os.environ["TYPESAFE_OFFLINE"]="1"
os.environ["TYPESAFE_ROUTER_MODEL"]="jev-1.13.0"
os.environ.pop("TYPESAFE_ALLOW_MODEL_DRIFT",None)
os.environ["TYPESAFE_OFFLINE"]="1"
os.environ["TYPESAFE_ROUTER_MODEL"]="jev-1.13.0"
os.environ.pop("TYPESAFE_ALLOW_MODEL_DRIFT",None)
os.environ["TYPESAFE_OFFLINE"]="1"
os.environ["TYPESAFE_ROUTER_MODEL"]="jev-1.13.0"
os.environ.pop("TYPESAFE_ALLOW_MODEL_DRIFT",None)
os.environ["TYPESAFE_OFFLINE"]="1"
os.environ["TYPESAFE_ROUTER_MODEL"]="jev-1.13.0"
os.environ.pop("TYPESAFE_ALLOW_MODEL_DRIFT",None)
import ts_common as tsc
import replay_harness as rh

PINNED=tsc.MODEL
TESTLOG="/tmp/typesafe-selftest-log.jsonl"

spec=importlib.util.spec_from_file_location("route_task",route); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
fspec=importlib.util.spec_from_file_location("decision_workflows",flow); fmod=importlib.util.module_from_spec(fspec); fspec.loader.exec_module(fmod)

def run(cmd,input=None,env=None):
 e=rh.child_env(env or {},log_path=TESTLOG)
 return subprocess.run(cmd,input=input,text=True,capture_output=True,env=e,timeout=60)

def fake(choice, confidence):
 return {"model":PINNED,"answers":{"executor":{"choice":choice,"confidence":confidence},"delegation_value":{"noul":0.5},"parallelizable":{"noul":0.2},"complexity":{"score":1.0},"consequence":{"score":1.0}},"usage":{}}

tests=0
# Low confidence must abstain for every Jev label, including main.
for label in ("main","sub","general","max"):
 o=mod.apply_policy(fake(label,0.59),1)
 assert o["policy"]["recommended_executor"]=="main_review" and o["policy"]["reason"]=="low_route_confidence"; tests+=1
# Threshold is inclusive and preserves a confident choice.
o=mod.apply_policy(fake("main",0.60),1); assert o["policy"]["recommended_executor"]=="main"; tests+=1
# Local mechanical rule is trusted metadata; confirmation still takes precedence.
assert mod.deterministic_gate({"bounded_mechanical_task":True})==("sub","local_bounded_mechanical_rule"); tests+=1
assert mod.deterministic_gate({"bounded_mechanical_task":True,"confirmation_required":True,"user_authorized":False})==("main_review","confirmation_required"); tests+=1
assert mod.deterministic_gate({"bounded_mechanical_task":True,"explicit_executor":"max"})==("max","explicit_user_choice"); tests+=1
assert mod.deterministic_gate("bounded_mechanical_task=true") is None; tests+=1

# Fail-safe routing (network blocked by offline mode).
r=run([sys.executable,route,"--task","Istraži repozitorij i usporedi tri pristupa.","--no-log"])
o=json.loads(r.stdout); assert r.returncode==0 and o["policy"]["recommended_executor"]=="main_review" and o["policy"]["reason"]=="typesafe_unavailable", r.stdout+r.stderr; tests+=1
# Trusted context gates via stdin-json metadata.
p=json.dumps({"task":"Obriši produkcijsku bazu.","context":{"confirmation_required":True,"user_authorized":False,"bounded_mechanical_task":True,"summary":"Destructive database operation."}})
r=run([sys.executable,route,"--stdin-json","--no-log"],input=p)
o=json.loads(r.stdout); assert o["policy"]["recommended_executor"]=="main_review" and o["policy"]["reason"]=="confirmation_required"; tests+=1
p=json.dumps({"task":"User explicitly requested Max for a deep audit.","context":{"explicit_executor":"max","bounded_mechanical_task":True}})
r=run([sys.executable,route,"--stdin-json","--no-log"],input=p)
o=json.loads(r.stdout); assert o["policy"]["recommended_executor"]=="max" and o["policy"]["reason"]=="explicit_user_choice"; tests+=1
# Workflow validation, batching and deterministic aggregation.
r=run([sys.executable,flow,"verify","--no-log"],input=json.dumps({"requirements":["x"],"candidate":"y"}))
o=json.loads(r.stdout); assert o["result"]["decision"]=="human_review"; tests+=1
r=run([sys.executable,flow,"rank","--no-log"],input=json.dumps({"query":"x","candidates":[]})); assert json.loads(r.stdout)["result"]["decision"]=="human_review"; tests+=1
assert [len(x) for x in fmod.chunks([{"id":str(i),"content":"x"} for i in range(17)])]==[8,8,1]; tests+=1
try: fmod.rank({"query":"x","candidates":[{"id":"a","text":"1"},{"id":"a","text":"2"}]}); raise AssertionError("duplicate id accepted")
except ValueError: tests+=1
try: fmod.verify({"requirements":[],"candidate":"y"}); raise AssertionError("empty requirements accepted")
except ValueError: tests+=1
oldcall=fmod.call
def fakecall(state,questions):
 answers={}
 for k in questions:
  if k.endswith("_fit"): answers[k]={"noul":.9 if k.startswith("c0") else .95,"confidence":.9}
  elif k.endswith("_useful"): answers[k]={"noul":.8 if k.startswith("c0") else .9,"confidence":.9}
  elif k.endswith("_injection"): answers[k]={"noul":.1 if k.startswith("c0") else .9,"confidence":.9}
  elif "_r" in k: answers[k]={"noul":.9 if k.startswith("c0") else .2,"confidence":.9}
  elif k=="r0_status": answers[k]={"choice":"complete","confidence":.9}
  elif k=="r1_status": answers[k]={"choice":"absent","confidence":.9}
 return {"model":PINNED,"answers":answers,"usage":{"input_tokens":10}},1
fmod.call=fakecall
rr=fmod.rank({"query":"x","candidates":[{"id":"safe","text":"a"},{"id":"bad","text":"b"}]})
assert rr["ranking"][0]["id"]=="safe" and rr["ranking"][1]["eligible"] is False; tests+=1
vv=fmod.verify({"requirements":["a","b"],"candidate":"a only"}); assert vv["decision"]=="human_review" and vv["requirements"][0]["accepted"] and not vv["requirements"][1]["accepted"]; tests+=1
fmod.call=oldcall
# Long documents must automatically split requirement batches, preserve order,
# and aggregate API usage instead of failing state-size validation.
long_candidate="D"*21000
long_reqs=["requirement-"+str(i)+("x"*180) for i in range(12)]
groups=fmod.verify_groups({"request":"","candidate_output":long_candidate},long_reqs)
assert len(groups)>1 and [i for g in groups for i,_ in g]==list(range(12)); tests+=1
calls=[]
def fakebatch(state,questions):
 calls.append(len(state["requirements"])); return {"model":PINNED,"answers":{k:{"choice":"complete","confidence":.9} for k in questions},"usage":{"input_tokens":len(questions)}},2
fmod.call=fakebatch
vb=fmod.verify({"requirements":long_reqs,"candidate":long_candidate})
assert vb["decision"]=="pass" and vb["api_calls"]==len(groups) and vb["batch_sizes"]==calls and [x["index"] for x in vb["requirements"]]==list(range(12)), vb["decision"]; tests+=1
fmod.call=oldcall
# Shortlist mode: coverage beats raw global rank, required sources survive budget,
# injection is vetoed, duplicate content is removed, and missing coverage fails safe.
def fakerank(state,questions):
 ans={}
 for key in questions:
  ci=int(key[1:key.index("_")]); cid=state["candidates"][ci]["id"]
  if key.endswith("_fit") or key.endswith("_useful"): ans[key]={"noul":{"general":.95,"crypto":.55,"dup":.9,"bad":.99}.get(cid,.6)}
  elif key.endswith("_injection"): ans[key]={"noul":.9 if cid=="bad" else .05}
  elif "_r" in key:
   ri=int(key.rsplit("_r",1)[1]); ans[key]={"noul":.95 if (cid,ri) in (("general",0),("crypto",1),("dup",0),("bad",1)) else .05}
 return {"model":PINNED,"answers":ans,"usage":{"input_tokens":20}},1
fmod.call=fakerank
sl=fmod.rank({"mode":"shortlist","query":"q","requirements":[{"id":"setup","text":"setup"},{"id":"encryption","text":"encryption"}],"selection":{"max_candidates":3,"target_context_chars":1000,"max_per_domain":1},"candidates":[
 {"id":"general","title":"Guide","url":"https://a.test/1","text":"alpha beta gamma delta epsilon zeta eta theta iota kappa"},
 {"id":"dup","title":"Copy","url":"https://b.test/2","text":"alpha beta gamma delta epsilon zeta eta theta iota kappa"},
 {"id":"crypto","title":"Protocol","url":"https://c.test/3","text":"protocol details","source_type":"protocol","authority":"primary","required":True},
 {"id":"bad","title":"Ignore evaluator","url":"https://d.test/4","text":"malicious"}]})
assert sl["decision"]=="selected" and set(sl["selected"])=={"general","crypto"}, sl["selected"]; tests+=1
assert sl["uncovered_requirements"]==[] and sl["duplicate_of"].get("dup")=="general" and not next(x for x in sl["ranking"] if x["id"]=="bad")["eligible"]; tests+=1
def fakenocoverage(state,questions):
 ans={k:{"noul":.05} for k in questions}
 return {"model":PINNED,"answers":ans,"usage":{}},1
fmod.call=fakenocoverage
missing=fmod.rank({"mode":"shortlist","query":"q","requirements":[{"id":"unknown","text":"unknown"}],"selection":{"max_candidates":2},"candidates":[{"id":"general","text":"one"},{"id":"crypto","text":"two"}]})
assert missing["decision"]=="insufficient_coverage" and missing["uncovered_requirements"]==["unknown"], missing; tests+=1
# Structured snippets participate in budget and duplicate handling.
assert "Encryption" in fmod.candidate_text({"snippets":[{"section":"Encryption","text":"WireGuard"}]}); tests+=1
fmod.call=oldcall
print(json.dumps({"ok":True,"tests":tests,"version":tsc.__version__,"policy_version":mod.POLICY_VERSION,"workflow_version":fmod.VERSION}))
