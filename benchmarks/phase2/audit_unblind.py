#!/usr/bin/env python3
"""A-002 evaluator gate: a historical outputs.lock alone never authorizes gold access."""
import hashlib,json,sys
from pathlib import Path
from validate_outputs import validate
from tools import phase2 as gate
from scored_runner import ROOT,REPO

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def canonical(x):return json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()
def audit(out):
 out=Path(out).resolve();errors=[];lock=out/'outputs.lock.json';seal=out.parent/'strict-output-seal.json'
 if not lock.is_file():errors.append('strict_output_lock_missing')
 if not seal.is_file():errors.append('strict_output_seal_missing')
 if errors:return {'ok':False,'decision':'unblind_forbidden','errors':errors}
 try:
  doc=json.loads(lock.read_text());proof=json.loads(seal.read_text())
  if doc.get('kind')!='phase2_strict_output_lock' or doc.get('schema_version')!=2:errors.append('historical_output_lock_not_authorized')
  if proof.get('kind')!='phase2_strict_output_seal' or proof.get('output_lock_sha256')!=sha(lock):errors.append('seal_hash_mismatch')
  if not gate.INPUT_LOCK.is_file() or doc.get('input_lock_sha256')!=sha(gate.INPUT_LOCK) or proof.get('input_lock_sha256')!=doc.get('input_lock_sha256'):errors.append('input_lock_mismatch')
  if not (ROOT/'runner.lock.json').is_file() or doc.get('runner_lock_sha256')!=sha(ROOT/'runner.lock.json') or proof.get('runner_lock_sha256')!=doc.get('runner_lock_sha256'):errors.append('runner_lock_mismatch')
  c=doc.get('custody_manifest_sha256')
  if c is not None:
   path=REPO/'CUSTODY-MANIFEST.json'
   if not path.is_file() or c!=sha(path) or proof.get('custody_manifest_sha256')!=c:errors.append('custody_manifest_mismatch')
  rows=doc.get('files',[])
  expected=set(gate.expected_output_names());actual={p.name for p in out.glob('*.json') if p.name!='outputs.lock.json'}
  if len(rows)!=160 or len({r['path'] for r in rows})!=160 or {r['path'] for r in rows}!=expected or actual!=expected:errors.append('output_set_mismatch')
  for row in rows:
   p=out/row['path']
   if not p.is_file() or p.stat().st_size!=row['bytes'] or sha(p)!=row['sha256']:errors.append('output_file_mismatch:'+row['path'])
  if hashlib.sha256(canonical(rows)).hexdigest()!=doc.get('aggregate_sha256'):errors.append('aggregate_mismatch')
  verdict=validate(out)
  if not verdict['ok']:errors.extend(verdict['errors'])
 except Exception as e:errors.append('audit_error:'+type(e).__name__)
 return {'ok':not errors,'decision':'unblind_allowed' if not errors else 'unblind_forbidden','errors':errors,'output_files':160 if not errors else 0}
if __name__=='__main__':
 x=audit(sys.argv[1]);print(json.dumps(x,indent=2));sys.exit(0 if x['ok'] else 1)
