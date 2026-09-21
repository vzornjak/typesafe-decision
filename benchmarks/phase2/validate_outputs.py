#!/usr/bin/env python3
"""Additional fail-closed Phase 2 output validation; does not edit input-locked tool."""
import json,re,hashlib
from pathlib import Path
from tools import phase2 as gate
import scored_runner as runner

def validate(out):
 out=Path(out); expected=set(gate.expected_output_names())
 actual={p.name for p in out.glob('*.json')}
 errors=[]
 if actual!=expected:errors.append('output_set_mismatch')
 for name in sorted(actual):
  if name not in expected:continue
  try:
   row=json.loads((out/name).read_text(encoding='utf-8'))
   task,arm,rep=name[:-5].split('__')
   if row.get('task_id')!=task or row.get('arm_id')!=arm or row.get('repetition')!=int(rep[3:]):errors.append('identity:'+name)
   if row.get('selection',{}).get('status') not in ('completed','failed'):errors.append('status:'+name)
   for key in ('answer','models','usage','timing','warnings'):
    if key not in row:errors.append('missing_'+key+':'+name)
   if not row.get('answer','').strip():errors.append('empty_answer:'+name)
   if row.get('selection',{}).get('status')=='failed':errors.append('failed_run_requires_inconclusive:'+name)
   if row.get('selection',{}).get('status')=='completed':
    usage=row.get('usage',{});models=row.get('models',{});sel=row.get('selection',{})
    if not isinstance(usage,dict) or any(type(usage.get(k)) is not int or usage[k]<0 for k in ('jev_input_tokens','jev_output_tokens','main_input_tokens','main_output_tokens','main_cache_read_input_tokens','main_cache_creation_input_tokens')):errors.append('invalid_usage:'+name)
    attempts=row.get('accounting_attempts')
    if row.get('accounting_status')!='complete' or not isinstance(attempts,list) or not attempts or any(not isinstance(a,dict) or a.get('status')!='accepted' or a.get('usage_complete') is not True for a in attempts):
     errors.append('incomplete_accounting:'+name)
    if models.get('main')!='claude-opus-5':errors.append('main_model_drift:'+name)
    if arm!='A_no_rank' and models.get('jev_served')!='jev-1.13.0':errors.append('jev_model_drift:'+name)
    if not isinstance(sel.get('prompt_sha256'),str) or len(sel['prompt_sha256'])!=64:errors.append('prompt_hash_missing:'+name)
    if not isinstance(sel.get('selected_ids'),list) or not sel['selected_ids']:errors.append('selection_missing:'+name)
    else:
     source=gate.RUNNER_INPUTS/(task+'.json')
     if source.exists():
      locked=json.loads(source.read_text(encoding='utf-8'))
      allowed={c['candidate_id'] for c in locked['candidates']}
      if locked['task_id']!=task or len(sel['selected_ids'])!=len(set(sel['selected_ids'])) or not set(sel['selected_ids'])<=allowed:
       errors.append('selected_ids_invalid:'+name)
      else:
       expected_hash=hashlib.sha256(runner.prompt(locked,sel['selected_ids']).encode()).hexdigest()
       if sel.get('prompt_sha256')!=expected_hash:errors.append('prompt_hash_mismatch:'+name)
       expected_order=[c['candidate_id'] for c in runner.candidates(locked,arm,int(rep[3:]))]
       if sel.get('candidate_order')!=expected_order:errors.append('candidate_order_mismatch:'+name)
     else:errors.append('locked_task_missing:'+name)
  except Exception as e:errors.append('invalid_json:'+name+':'+type(e).__name__)
 return {'ok':not errors,'errors':errors,'files':len(actual)}
if __name__=='__main__':
 import sys
 result=validate(sys.argv[1]);print(json.dumps(result,indent=2));sys.exit(0 if result['ok'] else 1)
