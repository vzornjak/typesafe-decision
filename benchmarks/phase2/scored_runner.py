#!/usr/bin/env python3
"""Scored Phase 2 runner: locked inputs, uniform arms, no gold access."""
import argparse, hashlib, json, math, os, random, subprocess, sys, time
from pathlib import Path
ROOT=Path(__file__).resolve().parent; REPO=ROOT.parent.parent
sys.path.insert(0,str(REPO/'scripts'))
import decision_workflows as dw
import ts_common as tsc
from tools import phase2 as gate
ARMS=('A_no_rank','B_winner_top8','C_shortlist_default','D_shortlist_tuned')

def sha(b): return hashlib.sha256(b).hexdigest()
def load(p): return json.loads(Path(p).read_text(encoding='utf-8'))
def schedule():
 return [(t.stem,arm,rep) for t in sorted(gate.RUNNER_INPUTS.glob('p2-score-*.json')) for arm in ARMS for rep in ([0] if arm==ARMS[0] else [1,2,3])]
def seed(task,arm,rep):
 return int.from_bytes(hashlib.sha256(f'phase2-v1-candidate-order:{task}:{arm}:{rep}'.encode()).digest()[:8],'big')
def candidates(task,arm,rep):
 c=list(task['candidates'])
 if arm!='A_no_rank': random.Random(seed(task['task_id'],arm,rep)).shuffle(c)
 return c
def rank_request(task,cands,arm,design):
 obj={'query':task['query'],'candidates':[{'id':c['candidate_id'],'title':c['title'],'url':c['url'],'domain':c['domain'],'text':c['content']} for c in cands]}
 if arm in ('C_shortlist_default','D_shortlist_tuned'):
  obj.update(mode='shortlist',requirements=task['requirements'],selection=design['arms'][arm]['selection'])
 return obj

def choose(task,cands,arm,design,rank_fn):
 if arm=='A_no_rank': return [c['candidate_id'] for c in cands],None,[]
 result=rank_fn(rank_request(task,cands,arm,design)); warnings=result.get('warnings',[])
 if result.get('model_requested')!= 'jev-1.13.0' or result.get('models_served')!=['jev-1.13.0']:
  raise RuntimeError('jev_model_contract_failed')
 rows=result.get('ranking',[]); ids={c['candidate_id'] for c in cands}
 if len(rows)!=len(cands) or {r.get('id') for r in rows}!=ids:raise RuntimeError('incomplete_or_duplicate_ranking')
 if arm=='B_winner_top8':
  if result.get('mode')!='winner':raise RuntimeError('wrong_winner_mode')
  eligible=[r for r in rows if r.get('eligible') is True]
  chosen=[r['id'] for r in sorted(eligible,key=lambda r:(-r['score'],r['id']))[:design['arms'][arm]['k']]]
  if len(chosen)!=design['arms'][arm]['k']:raise RuntimeError('winner_not_exact_top_k')
 else:
  if result.get('mode')!='shortlist' or result.get('decision')!='selected': raise RuntimeError('shortlist_did_not_select')
  if result.get('selection')!=design['arms'][arm]['selection']:raise RuntimeError('shortlist_config_drift')
  chosen=result['selected']
 if not chosen or len(chosen)!=len(set(chosen)) or not set(chosen)<=ids: raise RuntimeError('invalid_selected_ids')
 return chosen,result,warnings

def prompt(task,selected):
 byid={c['candidate_id']:c for c in task['candidates']}
 tmpl=(ROOT/'prompts/main-user-template.md').read_text(encoding='utf-8')
 req='\n'.join(f"{i}. {r['text']}" for i,r in enumerate(task['requirements'],1))
 sources='\n\n'.join(f"[{cid}] {byid[cid]['title']}\nURL: {byid[cid]['url']}\n{byid[cid]['content']}" for cid in selected)
 return tmpl.replace('{{query}}',task['query']).replace('{{requirements_numbered}}',req).replace('{{candidate_sources_with_exact_ids}}',sources)

def parse_main_response(response,execution):
 if not isinstance(response,dict) or response.get('ok') is not True:raise RuntimeError('main_response_not_ok')
 data=response.get('data')
 if not isinstance(data,dict):raise RuntimeError('main_data_missing')
 model=data.get('model_id');usage=data.get('usage');text=data.get('output_text');stop=data.get('stop_reason')
 if model!=execution['main']['model']:raise RuntimeError('main_model_drift')
 if not isinstance(text,str) or not text.strip():raise RuntimeError('main_output_missing')
 if stop!='end_turn':raise RuntimeError('main_stop_not_end_turn')
 if not isinstance(usage,dict) or any(type(usage.get(k)) is not int or usage[k]<0 for k in ('input_tokens','output_tokens')):
  raise RuntimeError('main_usage_missing_or_invalid')
 return text,usage,model

def main_call(prompt_text,execution):
 if os.environ.get('PHASE2_MAIN_TRANSPORT')=='minis_relay':
  import main_relay
  main_call.last_usage=None
  try:return main_relay.call(prompt_text,execution,(ROOT/'prompts/main-system.md').read_text(encoding='utf-8'))
  except main_relay.RelayError as e:
   main_call.last_usage=e.usage
   raise RuntimeError('main_relay_'+str(e)) from None
 if os.environ.get('PHASE2_MAIN_TRANSPORT')=='anthropic_direct':
  import main_anthropic
  main_call.last_usage=None
  try:
   return main_anthropic.call(prompt_text,execution,(ROOT/'prompts/main-system.md').read_text(encoding='utf-8'))
  except main_anthropic.MainTransportError as e:
   main_call.last_usage=e.usage
   raise RuntimeError('main_transport_'+str(e)) from None
 payload={'messages':[{'role':'user','content':prompt_text}]}
 import tempfile
 with tempfile.TemporaryDirectory(prefix='p2-main-') as td:
  inp=Path(td)/'input.json';inp.write_text(json.dumps(payload,ensure_ascii=False),encoding='utf-8')
  env={k:v for k,v in os.environ.items() if not any(s in k.upper() for s in ('GOLD','CURATOR','SEALED'))}
  p=subprocess.run(['minis-model-use','run','--model',execution['main']['model'],'--provider',execution['main']['provider'],'--input',str(inp),'--system-file',str(ROOT/'prompts/main-system.md'),'--max-tokens',str(execution['main']['max_output_tokens']),'--temperature',str(execution['main']['temperature'])],capture_output=True,text=True,env=env,timeout=600)
  if p.returncode: raise RuntimeError(f'main_cli_failed:{p.returncode}')
  try:response=json.loads(p.stdout)
  except (ValueError,TypeError):raise RuntimeError('main_unparseable_usage_unknown')
  data=(response or {}).get('data') if isinstance(response,dict) else None
  raw_usage=(data or {}).get('usage') if isinstance(data,dict) else None
  if isinstance(raw_usage,dict) and all(type(raw_usage.get(k)) is int and raw_usage[k]>=0 for k in ('input_tokens','output_tokens')):
   main_call.last_usage=raw_usage
  return parse_main_response(response,execution)

def preflight():
 if not gate.INPUT_LOCK.exists(): raise RuntimeError('missing_input_lock')
 lock=load(gate.INPUT_LOCK)
 if os.environ.get('PHASE2_SCOPED_RUNNER')=='1':
  import scoped_inputs
  commit=os.environ.get('PHASE2_ATTESTED_COMMIT')
  if not commit:raise RuntimeError('missing_attested_runner_commit')
  try:scoped_inputs.verify(REPO,REPO/'CUSTODY-MANIFEST.json',gate.INPUT_LOCK,commit)
  except ValueError as e:raise RuntimeError('scoped_input_mismatch:'+str(e)) from None
 else:
  if gate.verify_lock(gate.INPUT_LOCK,gate.ROOT): raise RuntimeError('input_lock_mismatch')
 # The original immutable input lock predates this executable. A supplementary
 # runner lock binds the audited code without rewriting that historical lock.
 runner_lock=ROOT/'runner.lock.json'
 if not runner_lock.exists(): raise RuntimeError('missing_runner_lock')
 rlock=load(runner_lock)
 if rlock.get('input_lock_sha256')!=sha(gate.INPUT_LOCK.read_bytes()): raise RuntimeError('runner_input_lock_mismatch')
 if os.environ.get('PHASE2_SCOPED_RUNNER')=='1':
  commit=os.environ.get('PHASE2_ATTESTED_COMMIT')
 else:
  commit=subprocess.check_output(['git','-C',str(REPO),'rev-parse','HEAD'],text=True).strip()
 if rlock.get('git_commit')!=commit:
  raise RuntimeError('runner_commit_mismatch')
 for name,h in rlock.get('files',{}).items():
  if not (ROOT/name).is_file() or sha((ROOT/name).read_bytes())!=h: raise RuntimeError('runner_file_mismatch:'+name)
 if not {'scored_runner.py','cost_model.py','tests_cost_model.py','COST-GATE-AMENDMENT.md','scoped_inputs.py','main_relay.py','relay_minis.py','main_anthropic.py','tests_main_anthropic.py','lock_runner.py','validate_outputs.py','seal_outputs.py','main-cli-contract.fixture.json','tools/phase2.py','config/execution.json','config/design.json','config/decision-gates.json','config/tuned-arm.json','prompts/main-system.md','prompts/main-user-template.md','../../archi.ai','../../scripts/decision_workflows.py','../../scripts/ts_common.py'}<=set(rlock.get('files',{})):
  raise RuntimeError('incomplete_runner_lock')
 if os.environ.get('PHASE2_SCOPED_RUNNER')!='1' and subprocess.check_output(['git','-C',str(REPO),'status','--porcelain'],text=True).strip():
  raise RuntimeError('runner_worktree_dirty')
 paths={r['path'] for r in lock['files']}
 required={f'runner-inputs/{tid}.json' for tid,_,_ in schedule()}
 if not required<=paths:raise RuntimeError('runner_inputs_not_locked')
 if len(schedule())!=160:raise RuntimeError('invalid_schedule')
 if any(k for k in os.environ if 'GOLD' in k.upper() or 'SEALED' in k.upper()): raise RuntimeError('gold_environment_exposure')
 return lock

def artifact(task,arm,rep,design,execution,rank_fn,main_fn,attempt=None):
 attempt = attempt if attempt is not None else {}
 started=time.monotonic(); cands=candidates(task,arm,rep); t0=time.monotonic()
 def recorded_rank(request):
  result=rank_fn(request);attempt['ranking']=result;return result
 selected,ranking,warnings=choose(task,cands,arm,design,recorded_rank); jev_ms=round((time.monotonic()-t0)*1000)
 attempt['selected_ids']=selected;attempt['jev_ms']=jev_ms
 if main_fn is main_call: main_call.last_usage=None
 text=prompt(task,selected); prompt_hash=sha(text.encode()); t1=time.monotonic()
 if arm=='A_no_rank' and sum(c['content_chars'] for c in task['candidates'])>design['arms'][arm]['candidate_content_ceiling_chars']:
  raise RuntimeError('baseline_candidate_ceiling_exceeded')
 if len(text)>150000:raise RuntimeError('main_prompt_ceiling_exceeded')
 answer,main_usage,model=main_fn(text,execution);main_ms=round((time.monotonic()-t1)*1000)
 attempt['main_usage']=main_usage;attempt['main_model']=model;attempt['main_ms']=main_ms
 if not isinstance(answer,str) or not answer.strip():raise RuntimeError('empty_main_answer')
 ju=(ranking or {}).get('total_usage') or (ranking or {}).get('usage') or {}
 if arm!='A_no_rank' and any(type(ju.get(k)) is not int or ju[k]<0 for k in ('input_tokens','output_tokens')):
  raise RuntimeError('jev_usage_missing_or_invalid')
 return {'task_id':task['task_id'],'arm_id':arm,'repetition':rep,
  'selection':{'selected_ids':selected,'candidate_order':[c['candidate_id'] for c in cands],
     'prompt_sha256':prompt_hash,'ranking':ranking,'status':'completed'},
  'answer':answer,'models':{'jev_requested':None if arm=='A_no_rank' else 'jev-1.13.0',
     'jev_served':None if arm=='A_no_rank' else 'jev-1.13.0','main':model},
  'usage':{'jev_input_tokens':0 if arm=='A_no_rank' else ju.get('input_tokens'),
    'jev_output_tokens':0 if arm=='A_no_rank' else ju.get('output_tokens'),
    'main_input_tokens':main_usage['input_tokens'],'main_output_tokens':main_usage['output_tokens'],
    'main_cache_read_input_tokens':main_usage.get('cache_read_input_tokens',0),
    'main_cache_creation_input_tokens':main_usage.get('cache_creation_input_tokens',0)},
  'accounting_status':'complete' if arm=='A_no_rank' or ((ranking or {}).get('api_attempts')==(ranking or {}).get('api_responses_received')==(ranking or {}).get('api_calls')) else 'unknown',
  'accounting_attempts':[{'status':'accepted','usage_complete':True}] if arm=='A_no_rank' else [{'status':'accepted' if (ranking or {}).get('api_attempts')==(ranking or {}).get('api_responses_received')==(ranking or {}).get('api_calls') else 'unknown','usage_complete':(ranking or {}).get('api_attempts')==(ranking or {}).get('api_responses_received')==(ranking or {}).get('api_calls')}],
  'timing':{'jev_ms':jev_ms if arm!='A_no_rank' else 0,'main_ms':main_ms,'end_to_end_ms':round((time.monotonic()-started)*1000)},
  'warnings':warnings}

def execute(out,rank_fn=dw.rank,main_fn=main_call,dry_run=False):
 lock=preflight();design=load(ROOT/'config/design.json');execution=load(ROOT/'config/execution.json')
 if out.exists() and any(out.iterdir()):raise RuntimeError('output_directory_not_empty')
 if (out.parent/'scored-decisions.jsonl').exists():raise RuntimeError('decision_log_path_not_empty')
 out.mkdir(parents=True,exist_ok=True)
 os.environ['TYPESAFE_DECISION_LOG']=str(out.parent/'scored-decisions.jsonl')
 for tid,arm,rep in schedule():
  task=load(gate.RUNNER_INPUTS/f'{tid}.json');attempt={}
  try:
   row=artifact(task,arm,rep,design,execution,rank_fn,main_fn,attempt)
  except Exception as e:
   ranking=attempt.get('ranking') or {}; billed=ranking.get('total_usage') or ranking.get('usage') or {}
   mu=attempt.get('main_usage') or (getattr(main_call,'last_usage',None) if main_fn is main_call else None)
   row={'task_id':tid,'arm_id':arm,'repetition':rep,
        'selection':{'selected_ids':attempt.get('selected_ids',[]),'candidate_order':[c['candidate_id'] for c in candidates(task,arm,rep)],
                     'prompt_sha256':None,'ranking':ranking or None,'status':'failed',
                     'error_type':type(e).__name__,'reason_code':'scored_run_failed'},
        'answer':'','models':{'jev_requested':None if arm=='A_no_rank' else 'jev-1.13.0',
                            'jev_served':(ranking.get('models_served') or [None])[0],
                            'main':attempt.get('main_model')},
        'accounting_status':'unknown',
  'accounting_attempts':[],
  'usage':{'jev_input_tokens':billed.get('input_tokens'),'jev_output_tokens':billed.get('output_tokens'),
                 'main_input_tokens':mu.get('input_tokens') if isinstance(mu,dict) else None,
                 'main_output_tokens':mu.get('output_tokens') if isinstance(mu,dict) else None,
                 'main_cache_read_input_tokens':mu.get('cache_read_input_tokens') if isinstance(mu,dict) else None,
                 'main_cache_creation_input_tokens':mu.get('cache_creation_input_tokens') if isinstance(mu,dict) else None},
        'timing':{'jev_ms':attempt.get('jev_ms'),'main_ms':attempt.get('main_ms'),'end_to_end_ms':None},
        'warnings':['scored_run_failed','usage_unknown_if_null']}
  name=f'{tid}__{arm}__rep{rep}.json';p=out/name
  with p.open('x',encoding='utf-8') as f:json.dump(row,f,ensure_ascii=False,indent=2);f.write('\n')
  print(json.dumps({'output':name,'completed':len(list(out.glob("*.json"))),'total':160,'status':row['selection']['status']}),flush=True)
 return {'ok':True,'outputs':len(list(out.glob('*.json'))),'input_lock_sha256':sha(gate.INPUT_LOCK.read_bytes())}

def cli():
 p=argparse.ArgumentParser();p.add_argument('--outputs',required=True);p.add_argument('--dry-run',action='store_true');a=p.parse_args()
 if a.dry_run:
  lock=preflight(); print(json.dumps({'ok':True,'scheduled':len(schedule()),'input_lock_sha256':sha(gate.INPUT_LOCK.read_bytes())}));return 0
 result=execute(Path(a.outputs).resolve());print(json.dumps(result));return 0
if __name__=='__main__':
 try:sys.exit(cli())
 except Exception as e:print(json.dumps({'ok':False,'error_type':type(e).__name__,'reason':str(e)}));sys.exit(1)
