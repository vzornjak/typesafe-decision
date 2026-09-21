#!/usr/bin/env python3
"""Supplementary gate: validate all 160 completed answers before historical output lock."""
import argparse,json,subprocess,sys
from pathlib import Path
from validate_outputs import validate
from scored_runner import preflight,ROOT

def main():
 p=argparse.ArgumentParser();p.add_argument('--outputs',required=True);p.add_argument('--actor',required=True);a=p.parse_args()
 try:
  preflight(); out=Path(a.outputs).resolve(); report=validate(out)
  if not report['ok']:
   print(json.dumps({'ok':False,'decision':'INCONCLUSIVE','validation':report},indent=2));return 1
  cmd=[sys.executable,str(ROOT/'tools/phase2.py'),'lock-outputs','--outputs',str(out),'--actor',a.actor]
  result=subprocess.run(cmd,capture_output=True,text=True,timeout=120)
  if result.returncode:print(result.stdout or result.stderr);return 1
  locked=json.loads(result.stdout)
  if not locked.get('ok') or locked.get('files')!=160:raise RuntimeError('output_lock_postcondition_failed')
  print(json.dumps(locked,indent=2));return 0
 except Exception as e:print(json.dumps({'ok':False,'error_type':type(e).__name__,'reason':str(e)}));return 1
if __name__=='__main__':sys.exit(main())
