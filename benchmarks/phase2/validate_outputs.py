#!/usr/bin/env python3
"""Additional fail-closed Phase 2 output validation; does not edit input-locked tool."""
import json,re
from pathlib import Path
from tools import phase2 as gate

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
    if not isinstance(usage,dict) or any(type(usage.get(k)) is not int or usage[k]<0 for k in ('jev_input_tokens','jev_output_tokens','main_input_tokens','main_output_tokens')):errors.append('invalid_usage:'+name)
    if models.get('main')!='claude-opus-5':errors.append('main_model_drift:'+name)
    if arm!='A_no_rank' and models.get('jev_served')!='jev-1.13.0':errors.append('jev_model_drift:'+name)
    if not isinstance(sel.get('prompt_sha256'),str) or len(sel['prompt_sha256'])!=64:errors.append('prompt_hash_missing:'+name)
    if not isinstance(sel.get('selected_ids'),list) or not sel['selected_ids']:errors.append('selection_missing:'+name)
  except Exception as e:errors.append('invalid_json:'+name+':'+type(e).__name__)
 return {'ok':not errors,'errors':errors,'files':len(actual)}
if __name__=='__main__':
 import sys
 result=validate(sys.argv[1]);print(json.dumps(result,indent=2));sys.exit(0 if result['ok'] else 1)
