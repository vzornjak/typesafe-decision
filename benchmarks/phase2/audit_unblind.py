#!/usr/bin/env python3
"""Mandatory Phase 2 pre-unblind gate; reject historical-lock-only bypass."""
import hashlib,json,sys
from pathlib import Path
from validate_outputs import validate
from tools import phase2 as gate

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def audit(out):
 out=Path(out).resolve();errors=[]; lock=out/'outputs.lock.json'; seal=out.parent/'strict-output-seal.json'
 if not lock.is_file():errors.append('historical_output_lock_missing')
 if not seal.is_file():errors.append('strict_output_seal_missing')
 if errors:return {'ok':False,'errors':errors}
 historic=json.loads(lock.read_text()); proof=json.loads(seal.read_text())
 if proof.get('kind')!='phase2_strict_output_seal':errors.append('seal_kind_invalid')
 if proof.get('output_lock_sha256')!=sha(lock):errors.append('seal_output_lock_hash_mismatch')
 if proof.get('input_lock_sha256')!=sha(gate.INPUT_LOCK):errors.append('seal_input_lock_hash_mismatch')
 for row in historic.get('files',[]):
  p=out/row['path']
  if not p.is_file() or sha(p)!=row['sha256']:errors.append('output_file_mismatch:'+row['path'])
 v=validate(out)
 if not v['ok']:errors.extend(v['errors'])
 if len(historic.get('files',[]))!=160:errors.append('output_count_invalid')
 return {'ok':not errors,'errors':errors,'output_files':len(historic.get('files',[]))}
if __name__=='__main__':
 x=audit(sys.argv[1]);print(json.dumps(x,indent=2));sys.exit(0 if x['ok'] else 1)
