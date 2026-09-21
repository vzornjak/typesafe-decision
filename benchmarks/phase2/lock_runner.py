#!/usr/bin/env python3
"""Create and verify supplementary runner lock without rewriting input lock."""
import hashlib,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent; REPO=ROOT.parent.parent
FILES=('scored_runner.py','cost_model.py','tests_cost_model.py','COST-GATE-AMENDMENT.md','scoped_inputs.py','tests_scoped_inputs.py','main_relay.py','relay_minis.py','tests_relay.py','main_anthropic.py','tests_main_anthropic.py','tests_scored_runner.py','tests_output_seal.py','validate_outputs.py','seal_outputs.py','main-cli-contract.fixture.json','lock_runner.py','tools/phase2.py','config/execution.json','config/design.json','config/decision-gates.json','config/tuned-arm.json','prompts/main-system.md','prompts/main-user-template.md','schemas/run-output.schema.json','../../archi.ai','../../scripts/decision_workflows.py','../../scripts/ts_common.py')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 path=ROOT/'runner.lock.json';inp=ROOT/'inputs.lock.json'
 if path.exists() or not inp.exists():raise RuntimeError('existing_runner_lock_or_missing_input_lock')
 import importlib.util
 spec=importlib.util.spec_from_file_location('phase2_gate',ROOT/'tools/phase2.py');g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
 if g.verify_lock(inp,ROOT):raise RuntimeError('input_lock_mismatch')
 status=subprocess.check_output(['git','-C',str(REPO),'status','--porcelain'],text=True).strip()
 if status:raise RuntimeError('git_worktree_not_clean')
 commit=subprocess.check_output(['git','-C',str(REPO),'rev-parse','HEAD'],text=True).strip()
 doc={'kind':'phase2_supplementary_runner_lock','input_lock_sha256':sha(inp),'git_commit':commit,'files':{n:sha(ROOT/n) for n in FILES}}
 path.write_text(json.dumps(doc,indent=2,sort_keys=True)+'\n',encoding='utf-8')
 print(json.dumps({'ok':True,'git_commit':commit,'input_lock_sha256':doc['input_lock_sha256'],'locked_files':len(FILES)}))
if __name__=='__main__':
 try:main()
 except Exception as e:print(json.dumps({'ok':False,'error_type':type(e).__name__,'reason':str(e)}));sys.exit(1)
