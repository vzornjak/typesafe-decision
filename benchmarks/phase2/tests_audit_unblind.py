#!/usr/bin/env python3
"""Negative test: historical output lock alone cannot pass strict pre-unblind gate."""
import hashlib,json,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parent;sys.path.insert(0,str(ROOT))
import audit_unblind as a

def main():
 checks=[]
 with tempfile.TemporaryDirectory() as td:
  out=Path(td)/'outputs';out.mkdir()
  lock={'files':[]}
  (out/'outputs.lock.json').write_text(json.dumps(lock))
  x=a.audit(out);assert not x['ok'] and 'strict_output_seal_missing' in x['errors'];checks.append('historical-only lock rejected')
  seal={'kind':'phase2_strict_output_seal','output_lock_sha256':hashlib.sha256((out/'outputs.lock.json').read_bytes()).hexdigest(),'input_lock_sha256':'wrong'}
  (Path(td)/'strict-output-seal.json').write_text(json.dumps(seal))
  x=a.audit(out);assert not x['ok'] and 'seal_input_lock_hash_mismatch' in x['errors'];checks.append('wrong input hash rejected')
 print(json.dumps({'ok':True,'tests':len(checks),'checks':checks}));return 0
if __name__=='__main__':sys.exit(main())
