from pathlib import Path
from datetime import datetime,timezone
import subprocess,json,sys,hashlib
R=Path('/root/cs336/pa5-supplement'); B=Path('/root/pa5-supplement-setup/20261003-gpu-gate'); stage=sys.argv[1]
assert stage in ['smoke','pilot']
d=B/'runs'/f'20261003-{stage}-03'
assert not (d/'run-status.json').exists()
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip()=='f5f4050de424a2b371da83e792fa5a4a81279084'
assert not subprocess.check_output(['git','status','--porcelain'],cwd=R).strip()
assert json.loads((B/'weight-acceptance.json').read_text())['status']=='PASS'
if stage=='pilot':
 s=B/'runs/20261003-smoke-03'
 assert json.loads((s/'smoke-gate-check.json').read_text())['status']=='PASS'
 assert json.loads((s/'run-status.json').read_text())['exit_code']==0
start=datetime.now(timezone.utc).isoformat()
cmd=[str(R/'.venv/bin/python'),'-u','-m','cs336_alignment.qwen_baseline','run','--run-dir',str(d),'--model-path',str(R/'models/qwen-baseline-7b/d149729398750b98c0af14eb82c78cfe92750796')]
with (d/'run.log.txt').open('x') as f:
 p=subprocess.run(cmd,cwd=R,stdout=f,stderr=subprocess.STDOUT)
state={'stage':stage.upper(),'run_id':d.name,'start_time':start,'end_time':datetime.now(timezone.utc).isoformat(),'status':'completed' if p.returncode==0 else 'failed','exit_code':p.returncode,'actual_git_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip(),'manifest_sha256':hashlib.sha256((d/'manifest.json').read_bytes()).hexdigest(),'command':cmd,'directly_comparable_to_official':False}
with (d/'run-status.json').open('x') as f:json.dump(state,f,indent=2);f.write('\n')
print(json.dumps(state),flush=True)
sys.exit(p.returncode)
