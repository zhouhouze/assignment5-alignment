"""Read-only telemetry for the existing approved runner and backup processes."""
import argparse,datetime,json,os,shlex,subprocess,time
from pathlib import Path
p=argparse.ArgumentParser(); p.add_argument('run_id'); p.add_argument('task'); a=p.parse_args()
base=Path('/Users/hr/Documents/Lesson/pa5-experiment-backups/full'); session=base/'p1b1-20261011-session'
query="""import json,os,shutil,subprocess,time
from pathlib import Path
from datetime import datetime,timezone
run=Path(%r)
ack=Path('/root/pa5-supplement-setup/backup-health')/(run.name+'.json')
v={'at':datetime.now(timezone.utc).isoformat(),'progress':json.loads((run/'progress.json').read_text()),'disk_free_bytes':shutil.disk_usage(run).free,'inodes_free':os.statvfs(run).f_favail,'gpu':subprocess.check_output(['nvidia-smi','--query-gpu=utilization.gpu,memory.used,memory.total','--format=csv,noheader,nounits'],text=True).strip(),'raw_files_observed':sum(1 for _ in (run/'raw').glob('*.jsonl')),'attempts_end':[json.loads(x.read_text()) for x in (run/'attempts').glob('*/end.json')]}
if ack.exists():
 v['ack']=json.loads(ack.read_text());v['ack_age_seconds']=time.time()-datetime.fromisoformat(v['ack']['verified_at']).timestamp()
print(json.dumps(v))
""" % ('/root/pa5-supplement-setup/full/'+a.run_id)
ssh=['ssh','-F','/dev/null','-o','BatchMode=yes','-o','ConnectTimeout=10','-S','/tmp/pa5-ssh-backup-live','-p','32124','root@180.127.11.177','/root/cs336/pa5-supplement/.venv/bin/python -']
start=time.time(); initial=None; peak=0
for i in range(200):
 tick=time.monotonic()
 try:
  r=subprocess.run(ssh,input=query,text=True,capture_output=True,timeout=30,check=True);v=json.loads(r.stdout)
  v['task']=a.task;v['run_id']=a.run_id;v['monitor_elapsed_seconds']=time.time()-start
  n=v['progress']['completed_count']; total=v['progress']['expected_count']
  if n and initial is None:initial=(time.time(),n)
  speed=None if initial is None or time.time()-initial[0]<1 else (n-initial[1])/(time.time()-initial[0])
  v['observed_examples_per_second_including_io']=speed
  v['estimated_task_remaining_seconds']=None if not speed else (total-n)/speed
  peak=max(peak,int(v['gpu'].split(',')[1].strip())); v['monitor_peak_gpu_mib']=peak
  latest=base/a.run_id/'LATEST.json'; v['latest_verified_snapshot']=json.loads(latest.read_text()) if latest.exists() else None
  v['current_prepaid_lease_fee_cny']=12.64;v['budget_limit_cny']=20
  v['estimated_incremental_gpu_cost_since_1137_cny']=max(0,time.time()-datetime.datetime.fromisoformat('2026-10-11T11:37:00+08:00').timestamp())*3.16/3600
 except Exception as e:v={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'task':a.task,'run_id':a.run_id,'telemetry_error':repr(e)}
 line=json.dumps(v,ensure_ascii=False)
 with (session/f'telemetry-{a.task}.jsonl').open('a') as f:f.write(line+'\n');f.flush();os.fsync(f.fileno())
 print(line,flush=True)
 if v.get('progress',{}).get('status') in ('RAW_COMPLETE','FAILED'):break
 time.sleep(max(1,55-(time.monotonic()-tick)))
