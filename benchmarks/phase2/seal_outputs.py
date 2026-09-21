#!/usr/bin/env python3
"""A-002: the only authorized scored output seal, compatible with scoped Docker."""
import argparse,datetime as dt,hashlib,json,os,sys
from pathlib import Path
from validate_outputs import validate
from scored_runner import preflight,ROOT,REPO
from tools import phase2 as gate

def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def canonical(x):return json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()

def seal(out,actor):
 preflight();out=Path(out).resolve();lock=out/'outputs.lock.json';proof=out.parent/'strict-output-seal.json'
 if lock.exists() or proof.exists():raise ValueError('output_lock_already_exists')
 expected=set(gate.expected_output_names());actual={p.name for p in out.glob('*.json')}
 if actual!=expected or len(expected)!=160:raise ValueError('output_set_not_160')
 verdict=validate(out)
 if not verdict['ok']:raise ValueError('strict_output_validation_failed:'+str(verdict['errors'][:3]))
 rows=[{'path':n,'bytes':(out/n).stat().st_size,'sha256':digest(out/n)} for n in sorted(expected)]
 doc={'schema_version':2,'kind':'phase2_strict_output_lock','actor':actor,'created_at_utc':dt.datetime.now(dt.timezone.utc).isoformat(),
      'input_lock_sha256':digest(ROOT/'inputs.lock.json'),'runner_lock_sha256':digest(ROOT/'runner.lock.json'),
      'custody_manifest_sha256':digest(REPO/'CUSTODY-MANIFEST.json') if os.environ.get('PHASE2_SCOPED_RUNNER')=='1' else None,
      'files':rows,'aggregate_sha256':hashlib.sha256(canonical(rows)).hexdigest()}
 if os.environ.get('PHASE2_SCOPED_RUNNER')=='1' and doc['custody_manifest_sha256'] is None:raise ValueError('custody_manifest_missing')
 # Validate twice and reject any byte drift between inspection and lock creation.
 if not validate(out)['ok'] or any(digest(out/r['path'])!=r['sha256'] for r in rows):raise ValueError('outputs_changed_before_seal')
 with lock.open('x',encoding='utf-8') as f:json.dump(doc,f,indent=2,sort_keys=True);f.write('\n')
 with proof.open('x',encoding='utf-8') as f:json.dump({'kind':'phase2_strict_output_seal','output_lock_sha256':digest(lock),'input_lock_sha256':doc['input_lock_sha256'],'runner_lock_sha256':doc['runner_lock_sha256'],'custody_manifest_sha256':doc['custody_manifest_sha256'],'validated_outputs':160},f,indent=2,sort_keys=True);f.write('\n')
 return {'ok':True,'decision':'sealed','output_files':160,'output_lock_sha256':digest(lock)}
def main():
 p=argparse.ArgumentParser();p.add_argument('--outputs',required=True);p.add_argument('--actor',required=True);a=p.parse_args()
 try:result=seal(a.outputs,a.actor)
 except Exception as e:result={'ok':False,'decision':'INCONCLUSIVE','error_type':type(e).__name__,'reason':str(e)}
 print(json.dumps(result,indent=2));return 0 if result['ok'] else 1
if __name__=='__main__':sys.exit(main())
