"""P1B-0.5 live SSH acceptance: synthetic writes + existing CPU MOCK restore.

No generation/prepare/score calls. Requires an authenticated SSH master. All
new remote files are under --remote-work and all Mac files under --backup-root.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shlex
import subprocess
import sys
import tarfile
import time
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts import qwen_artifact_backup as b


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for flag in ('host', 'control-path', 'remote-work', 'backup-root', 'existing-mock', 'report'):
        p.add_argument('--'+flag, required=True)
    p.add_argument('--port', required=True, type=int)
    args = p.parse_args()
    uid = uuid.uuid4().hex[:10]
    remote = args.remote_work+'/live-'+uid
    local = Path(args.backup_root)/('live-'+uid); local.mkdir(parents=True, exist_ok=False)
    helpers = args.remote_work+'/scripts'
    ssh = ['ssh', '-F', '/dev/null', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=10',
        '-S', args.control_path, '-p', str(args.port), args.host]

    def code(source):
        r = subprocess.run(ssh+['python3 -'], input=source.encode(), capture_output=True, timeout=60, check=True)
        return json.loads(r.stdout)

    def pull(run, store, cycles=1, interval=2, ack=None, quiescent=False, fail_network=False):
        a = argparse.Namespace(host=args.host, port=args.port, control_path=args.control_path,
            remote_python='python3', remote_script=helpers+'/qwen_artifact_backup.py', run_dir=run,
            store=str(store), interval=interval, cycles=cycles, timeout=180, quiescent=quiescent, ack_path=ack)
        if fail_network:
            a.host='root@127.0.0.1'; a.port=1; a.control_path=str(local/'nonexistent-ssh-master')
        b.pull(a)

    fixture, ack = remote+'/MOCK_TEST_ONLY', remote+'/backup-ack.json'
    setup = f'''
import sys, json, subprocess
from pathlib import Path
sys.path.insert(0, {helpers!r})
import qwen_artifact_backup as b
root=Path({fixture!r}); root.mkdir(parents=True, exist_ok=False)
(root/'raw').mkdir(); (root/'logs').mkdir()
b.atomic(root/'manifest.json', b.json_bytes(dict(mode='MOCK_TEST_ONLY', purpose='backup fixture; no model')))
b.atomic(root/'manifest.sha256', (b.digest_file(root/'manifest.json')+'\\n').encode())
b.atomic(root/'selected_examples.json', b.json_bytes([]))
def row(n):
    value=dict(example_id=str(n), raw_response='MOCK / TEST_ONLY', mode='MOCK_TEST_ONLY')
    import hashlib
    seal=b.sha(json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode())
    b.atomic(root/'raw'/f'{{n}}.jsonl',b.json_bytes(dict(**value,record_sha256=seal)))
row(1)
(root/'raw/.pending-demo').write_text('{{"not_complete":')
(root/'logs/generation.log').write_text('CPU backup fixture only\\n')
print(json.dumps(dict(status='FIXTURE_CREATED',root=str(root))))
'''
    result = dict(record_type='P1B_0_5_LIVE_SSH_CPU_ACCEPTANCE', created_at=b.now(),
        source_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        source_dirty=bool(subprocess.check_output(['git','status','--porcelain'],text=True).strip()),
        source_sha256={n:b.digest_file(Path(__file__).resolve().parent/n) for n in
            ('qwen_artifact_backup.py','qwen_backup_guard.py','verify_qwen_backup.py')},
        local_root=str(local), remote_root=remote, generation_executed=False, gpu_model_loaded=False,
        formal_full_completed=0, formal_full_expected=16266)
    try:
        result['setup'] = code(setup)
        store = local/'fixture-store'
        pull(fixture, store, ack=ack)
        initial = b.latest(store)[0]
        assert initial['raw_count']==1 and 'raw/.pending-demo' in initial['skipped']
        producer = setup[setup.index('def row(n):'):setup.index('row(1)')]+'''
import time
for n in range(2,7):
    time.sleep(.7)
    row(n)
    b.atomic(root/'progress.json',b.json_bytes(dict(mode='MOCK_TEST_ONLY',count=n)),replace=True)
    with (root/'logs/generation.log').open('a') as f: f.write(str(n)+'\\n'); f.flush()
'''
        guard_child = "import os,time;from pathlib import Path;Path("+repr(remote+'/guard-child.pid')+").write_text(str(os.getpid()));time.sleep(60)"
        launch = f'''
import subprocess,json,sys
from pathlib import Path
root=Path({fixture!r})
producer={('import sys,json\nfrom pathlib import Path\nsys.path.insert(0,'+repr(helpers)+')\nimport qwen_artifact_backup as b\nroot=Path('+repr(fixture)+')\n'+producer)!r}
with open({(remote+'/producer.log')!r},'xb') as f:
    a=subprocess.Popen(['python3','-c',producer],stdin=subprocess.DEVNULL,stdout=f,stderr=f,start_new_session=True)
with open({(remote+'/guard.log')!r},'xb') as f:
    c=subprocess.Popen(['python3',{(helpers+'/qwen_backup_guard.py')!r},'--ack-file',{ack!r},'--run-dir',{fixture!r},'--max-age','4','--poll','.2','--','python3','-c',{guard_child!r}],stdin=subprocess.DEVNULL,stdout=f,stderr=f,start_new_session=True)
print(json.dumps(dict(producer_pid=a.pid,guard_pid=c.pid)))
'''
        result['cpu_processes'] = code(launch)
        pull(fixture, store, cycles=4, interval=2, ack=ack)
        live = b.latest(store)[0]
        assert live['raw_count']==6
        # Stop refreshing intentionally; the unrelated real GPU is never touched.
        time.sleep(5)
        result['guard_expiry'] = code(f'''
from pathlib import Path
import json,os
base=Path({remote!r}); pid=int((base/'guard-child.pid').read_text())
try: os.kill(pid,0); alive=True
except ProcessLookupError: alive=False
text=(base/'guard.log').read_text()
assert not alive and 'invalid/stale' in text,text
assert (base/'producer.log').read_text()=='',(base/'producer.log').read_text()
print(json.dumps(dict(status='PASS',owned_cpu_child_stopped=True,guard_log=text)))
''')
        before = (store/'LATEST.json').read_bytes()
        try:
            pull(fixture, store, fail_network=True)
            raise AssertionError('Network failure was not detected')
        except subprocess.CalledProcessError:
            assert (store/'LATEST.json').read_bytes()==before
        code(setup[setup.index('def row(n):'):setup.index('row(1)')].join(
            [f'import sys,json\nfrom pathlib import Path\nsys.path.insert(0,{helpers!r})\nimport qwen_artifact_backup as b\nroot=Path({fixture!r})\n','row(7)\nprint(json.dumps(dict(status="APPENDED_SEVENTH_CPU_RECORD")))']))
        pull(fixture, store)
        value, _ = b.latest(store)
        assert value['raw_count']==7
        events = [json.loads(x) for x in (store/'backup-events.jsonl').read_text().splitlines()]
        assert events[-1]['copied_objects']==1 and any(x['status']=='FAILED' for x in events)
        resumed_delta = events[-1]['copied_objects']
        pull(fixture, store, quiescent=True)
        final_fixture = b.latest(store)[0]
        assert final_fixture['raw_count']==7 and 'raw/.pending-demo' in final_fixture['files']
        events = [json.loads(x) for x in (store/'backup-events.jsonl').read_text().splitlines()]
        result['fixture'] = dict(status='PASS', raw_counts=[x['raw_count'] for x in events if x['status']=='SUCCESS'],
            resumed_raw_delta_objects=resumed_delta, final_pending_evidence_objects=events[-1]['copied_objects'], network_failure_logged=True,
            previous_snapshot_retained=True, restore=b.restore(store, local/'restored-fixture'), events=events)
        # Reuse yesterday's existing, complete CPU Mock, without any runner execution.
        full_store = local/'existing-full-mock-store'
        pull(args.existing_mock, full_store, quiescent=True)
        restored = local/'restored-full-mock'
        proof = b.restore(full_store, restored)
        assert proof['raw_count']==16266
        archive = local/'restored-full-mock.tar.gz'
        with tarfile.open(archive,'x:gz') as tar: tar.add(restored,arcname='restored-full-mock')
        subprocess.run(['scp','-F','/dev/null','-o','BatchMode=yes','-o','ControlPath='+args.control_path,
            '-P',str(args.port),str(archive),args.host+':'+remote+'/restored-full-mock.tar.gz'],check=True,timeout=180)
        result['restored_runner_validation'] = code(f'''
import json,tarfile,sys,os
from pathlib import Path
os.chdir('/root/cs336/pa5-supplement');sys.path.insert(0,str(Path.cwd()))
with tarfile.open({(remote+'/restored-full-mock.tar.gz')!r},'r:gz') as tar:tar.extractall({remote!r},filter='data')
from cs336_alignment import qwen_baseline as b
m,requests,raw=b.validate(Path({(remote+'/restored-full-mock')!r}))
assert m['mode']=='MOCK_TEST_ONLY' and len(raw)==len(requests)==16266 and 'vllm' not in sys.modules
print(json.dumps(dict(status='PASS',mode=m['mode'],inputs=len(requests),raw=len(raw),finalized_verified=True,vllm_imported=False,generation_executed=False)))
''')
        result['existing_full_mock'] = dict(status='PASS',backup_store=str(full_store),restore=proof,
            transport_bytes=archive.stat().st_size,transport_sha256=b.digest_file(archive),
            latest_pointer_sha256=b.digest_file(full_store/'LATEST.json'),
            snapshot_manifest_sha256=b.latest(full_store)[1]['sha256'])
        result['status']='PASS'
    except BaseException as exc:
        result.update(status='FAILED',error_type=type(exc).__name__,error=str(exc))
        raise
    finally:
        b.atomic(Path(args.report), b.json_bytes(result))
        print(json.dumps(dict(status=result['status'],report=args.report,local_root=str(local))))


if __name__ == '__main__':
    main()
