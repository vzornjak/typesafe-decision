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
   if row.get('selection',{}).get('status')=='completed' and not row.get('answer','').strip():errors.append('empty_completed_answer:'+name)
  except Exception as e:errors.append('invalid_json:'+name+':'+type(e).__name__)
 return {'ok':not errors,'errors':errors,'files':len(actual)}
if __name__=='__main__':
 import sys
 print(json.dumps(validate(sys.argv[1]),indent=2))
