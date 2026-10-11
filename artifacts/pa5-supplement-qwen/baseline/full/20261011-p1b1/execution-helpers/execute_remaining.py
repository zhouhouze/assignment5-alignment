"""One approved sequential workflow. Calls existing prepare/run/score/backup APIs.
No inference implementation, changed protocol, automatic resume, or extra task.
"""
import datetime,hashlib,json,os,shlex,signal,subprocess,sys,time
from pathlib import Path
REPO=Path('/Users/hr/Documents/Lesson/assignment5-alignment/tmp/pa5-supplement')
BASE=Path('/Users/hr/Documents/Lesson/pa5-experiment-backups'); SESSION=BASE/'full/p1b1-20261011-session'
REMOTE='/root/cs336/pa5-supplement'; PY=REMOTE+'/.venv/bin/python'
PREFIX='qwen-full-20261011T034800Z'; COMMIT='47ae79f3f1c5fdf390ef23bfc9f8bd41b23d2726'
DEADLINE=datetime.datetime.fromisoformat('2026-10-11T13:59:25+08:00').timestamp()
SSH=['ssh','-F','/dev/null','-o','BatchMode=yes','-o','ConnectTimeout=10','-S','/tmp/pa5-ssh-backup-live','-p','32124','root@180.127.11.177']
ENV='cd '+shlex.quote(REMOTE)+' && PYTHONDONTWRITEBYTECODE=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 '
backup_pids={}; active_guard=None

def stamp():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def event(status,**values):
 v={'at':stamp(),'status':status,**values};line=json.dumps(v,ensure_ascii=False)
 with (SESSION/'workflow-events.jsonl').open('a') as f:f.write(line+'\n');f.flush();os.fsync(f.fileno())
 print(line,flush=True)
def save(name,value):
 with (SESSION/name).open('x') as f:json.dump(value,f,ensure_ascii=False,indent=2);f.flush();os.fsync(f.fileno())
def cloud(script,timeout=600):
 p=subprocess.run(SSH+[ENV+shlex.quote(PY)+' -'],input=script,text=True,capture_output=True,timeout=timeout)
 if p.returncode:raise RuntimeError(f'Cloud command failed {p.returncode}: {p.stdout[-3000:]} {p.stderr[-3000:]}')
 return p.stdout

def args(task):
 run=PREFIX+'-'+task
 return [sys.executable,'scripts/qwen_artifact_backup.py','pull','--host','root@180.127.11.177','--port','32124','--control-path','/tmp/pa5-ssh-backup-live','--remote-python',PY,'--remote-script',REMOTE+'/scripts/qwen_artifact_backup.py','--run-dir','/root/pa5-supplement-setup/full/'+run,'--store',str(BASE/'full'/run),'--ack-path','/root/pa5-supplement-setup/backup-health/'+run+'.json','--timeout','180']
def local(command,name,timeout=600):
 with (SESSION/name).open('xb') as f:p=subprocess.run(command,cwd=REPO,stdout=f,stderr=subprocess.STDOUT,timeout=timeout)
 if p.returncode:raise RuntimeError(f'Local command failed {p.returncode}; see {name}')
def start_worker(task):
 command=['/usr/bin/caffeinate','-i']+args(task)+['--cycles','0','--interval','60']
 with (SESSION/f'backup-{task}-worker.log').open('xb') as log:
  p=subprocess.Popen(command,cwd=REPO,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
 backup_pids[task]=p.pid;save(f'worker-{task}.json',{'pid':p.pid,'command':command,'run_id':PREFIX+'-'+task})
def stop_worker(task):
 # Wait for an idle interval, rather than interrupting a transfer under fsync.
 store=BASE/'full'/(PREFIX+'-'+task)
 end=time.time()+190
 while time.time()<end:
  lines=(store/'backup-events.jsonl').read_text().splitlines()
  if lines and json.loads(lines[-1])['status'] in ('SUCCESS','FAILED'):break
  time.sleep(1)
 else:raise RuntimeError('Backup not idle within transfer timeout')
 os.killpg(backup_pids[task],signal.SIGTERM)
 time.sleep(1)
 event('BACKUP_WORKER_STOPPED',task=task,pid=backup_pids[task])
def start_monitor(task):
 with (SESSION/f'telemetry-{task}.log').open('xb') as f:
  p=subprocess.Popen([sys.executable,str(SESSION/'monitor_live.py'),PREFIX+'-'+task,task],cwd=REPO,stdin=subprocess.DEVNULL,stdout=f,stderr=subprocess.STDOUT,start_new_session=True)
 save(f'monitor-{task}.json',{'pid':p.pid})
def prepare_launch(task):
 global active_guard
 if DEADLINE-time.time()<1800:raise RuntimeError('Insufficient remaining common generation window')
 run='/root/pa5-supplement-setup/full/'+PREFIX+'-'+task
 output=cloud(f"""import subprocess,sys
assert subprocess.check_output(['git','status','--porcelain'],text=True).strip()==''
assert subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()=={COMMIT!r}
assert not subprocess.check_output(['nvidia-smi','--query-compute-apps=pid','--format=csv,noheader'],text=True).strip()
subprocess.run([sys.executable,'-m','cs336_alignment.qwen_baseline','prepare','--stage','full','--task',{task!r},'--run-id',{(PREFIX+'-'+task)!r},'--output-dir','/root/pa5-supplement-setup/full','--dataset-root',{REMOTE!r},'--config','configs/qwen_baseline_gate.json'],check=True)
""")
 save(f'prepare-{task}.json',{'at':stamp(),'output':output})
 local(args(task),f'initial-backup-{task}.log')
 local([sys.executable,'scripts/qwen_artifact_backup.py','status','--store',str(BASE/'full'/(PREFIX+'-'+task)),'--max-age','180'],f'initial-status-{task}.json')
 start_worker(task)
 record=json.loads(cloud(f"""import datetime,json,subprocess,sys,time
from pathlib import Path
from scripts.qwen_backup_guard import healthy
run=Path({run!r});ack=Path('/root/pa5-supplement-setup/backup-health')/(run.name+'.json')
healthy(ack,run,180)
assert not subprocess.check_output(['nvidia-smi','--query-compute-apps=pid','--format=csv,noheader'],text=True).strip()
seconds=int({DEADLINE!r}-time.time());assert seconds>1200
command=['/usr/bin/timeout','--signal=TERM','--kill-after=40s',str(seconds),sys.executable,'scripts/qwen_backup_guard.py','--ack-file',str(ack),'--run-dir',str(run),'--max-age','180','--poll','5','--',sys.executable,'-m','cs336_alignment.qwen_baseline','run','--run-dir',str(run),'--model-path',{(REMOTE+'/models/qwen-baseline-7b/d149729398750b98c0af14eb82c78cfe92750796')!r},'--approve-full','--max-seconds',str(seconds)]
(run/'logs').mkdir(exist_ok=True)
with (run/'logs/generation.log').open('xb') as f:p=subprocess.Popen(command,stdin=subprocess.DEVNULL,stdout=f,stderr=subprocess.STDOUT,start_new_session=True,close_fds=True)
print(json.dumps({{'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'timeout_pid':p.pid,'command':command,'run_id':run.name,'shared_generation_deadline':{DEADLINE!r},'run_code_commit':{COMMIT!r}}}))
"""))
 save(f'launch-{task}.json',record);active_guard=record['timeout_pid'];start_monitor(task)
 event('GENERATION_STARTED',task=task,**record)
def wait_raw(task):
 file=SESSION/f'telemetry-{task}.jsonl'
 while time.time()<DEADLINE+50:
  if file.exists():
   v=json.loads(file.read_text().splitlines()[-1])
   status=v.get('progress',{}).get('status')
   if status=='RAW_COMPLETE':return
   if status=='FAILED':raise RuntimeError(f'Generation failed: {v}')
  time.sleep(5)
 raise RuntimeError('Common generation deadline reached; retain PARTIAL')
def finalize(task):
 global active_guard
 run='/root/pa5-supplement-setup/full/'+PREFIX+'-'+task
 # Only proceed once the actual runner and GPU workers have exited.
 for _ in range(36):
  v=json.loads(cloud(f"""import json,subprocess
p=subprocess.run(['ps','-p',{str(active_guard)!r},'-o','stat='],capture_output=True,text=True)
print(json.dumps({{'guard_stat':p.stdout.strip(),'compute':subprocess.check_output(['nvidia-smi','--query-compute-apps=pid','--format=csv,noheader'],text=True).strip()}}))
""",timeout=30))
  if not v['guard_stat'] or v['guard_stat'].startswith('Z'):
   if v['compute']:raise RuntimeError('GPU compute remained after this task guard exited')
   break
  time.sleep(5)
 else:raise RuntimeError('Runner did not terminate after RAW_COMPLETE')
 active_guard=None
 output=cloud(f"""import json,subprocess,sys
from pathlib import Path
from cs336_alignment import qwen_baseline as b
run=Path({run!r})
m,inputs,raw=b.validate_full(run)
assert len(raw)==m['expected_count']
with Path('/root/pa5-supplement-setup/'+run.name+'-score-v1.log').open('xb') as f:
 subprocess.run([sys.executable,'-m','cs336_alignment.qwen_baseline','score','--run-dir',str(run),'--score-version','v1'],stdout=f,stderr=subprocess.STDOUT,check=True)
m,inputs,raw=b.validate_full(run)
print(json.dumps({{'status':'PASS','raw_count':len(raw),'manifest':m['run_id'],'metrics':json.loads((run/'finalized/v1/metrics.json').read_text()),'integrity':json.loads((run/'finalized/v1/checks/integrity-report.json').read_text()),'offline_recomputation':json.loads((run/'finalized/v1/checks/recomputation-report.json').read_text())}}))
""",timeout=600)
 save(f'cloud-final-{task}.json',json.loads(output))
 stop_worker(task)
 local(args(task)+['--quiescent'],f'final-backup-{task}.log')
 local([sys.executable,'scripts/qwen_artifact_backup.py','status','--store',str(BASE/'full'/(PREFIX+'-'+task))],f'final-backup-status-{task}.json')
 latest=json.loads((BASE/'full'/(PREFIX+'-'+task)/'LATEST.json').read_text())
 snapshot=BASE/'full'/(PREFIX+'-'+task)/'snapshots'/(latest['snapshot_id']+'.json')
 snap=json.loads(snapshot.read_text());assert snap['quiescent'] and not snap['deferred']
 destination=BASE/'restored'/(PREFIX+'-'+task)
 local([sys.executable,'scripts/qwen_artifact_backup.py','restore','--store',str(BASE/'full'/(PREFIX+'-'+task)),'--destination',str(destination)],f'restore-{task}.log')
 sys.path.insert(0,str(REPO))
 from cs336_alignment import qwen_baseline as b
 m,inputs,raw=b.validate_full(destination)
 from cs336_alignment.qwen_baseline_audit import recompute
 actual=recompute(destination);saved=json.loads((destination/'finalized/v1/metrics.json').read_text())['results'];assert actual==saved
 for name,value in snap['files'].items():assert b.sha(destination/name)==value['sha256']
 assert len(raw)==m['expected_count']==snap['raw_count']
 save(f'restore-validation-{task}.json',{'at':stamp(),'status':'PASS','run_id':m['run_id'],'expected':len(inputs),'actual':len(raw),'snapshot_id':latest['snapshot_id'],'snapshot_sha256':hashlib.sha256(snapshot.read_bytes()).hexdigest(),'source_backup_restored_sha256_equal':True,'verified_files':len(snap['files']),'logical_bytes':sum(v['bytes'] for v in snap['files'].values()),'quiescent':True,'deferred':[],'restored_path':str(destination),'offline_recomputation':'PASS','core_runner_validation':'PASS'})
 event('TASK_COMPLETE_BACKUP_RESTORED',task=task,raw_count=len(raw),snapshot_id=latest['snapshot_id'])

try:
 backup_pids['mmlu']=json.loads((SESSION/'worker-mmlu.json').read_text())['pid']
 active_guard=24722
 save('launch-mmlu.json',json.loads(cloud("from pathlib import Path\nprint(Path('/root/pa5-supplement-setup/p1b1-launch-mmlu.json').read_text())")))
 for task in ('mmlu','gsm8k','alpaca_eval','simple_safety_tests'):
  if task!='mmlu':prepare_launch(task)
  wait_raw(task);finalize(task)
 event('ALL_FOUR_TASKS_COMPLETE',count=16266,judge='NOT_RUN',training='NOT_RUN',next='AI initial analysis and Git archival; stop after P1B-1')
except BaseException as e:
 event('WORKFLOW_HARD_STOP',error=repr(e),active_timeout_pid=active_guard)
 if active_guard:
  try:cloud(f'import os,signal\nos.kill({active_guard},signal.SIGTERM)',timeout=30)
  except Exception as stop_error:event('STOP_REQUEST_FAILED_GUARD_ACK_PROTECTION_REMAINS',error=repr(stop_error))
 raise
