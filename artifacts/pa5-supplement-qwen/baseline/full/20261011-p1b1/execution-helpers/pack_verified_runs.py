"""Portable copy of already verified restored runs; all tar members rehashed."""
import datetime,hashlib,json,os,tarfile
from pathlib import Path
base=Path('/Users/hr/Documents/Lesson/pa5-experiment-backups');session=base/'full/p1b1-20261011-session';prefix='qwen-full-20261011T034800Z'
archive=session/(prefix+'-verified-runs.tar.gz');expected={};total=0
with tarfile.open(archive,'x:gz',compresslevel=6) as tar:
 for task in ('mmlu','gsm8k','alpaca_eval','simple_safety_tests'):
  run=prefix+'-'+task; store=base/'full'/run
  verified=json.loads((session/f'restore-validation-{task}.json').read_text());assert verified['status']=='PASS'
  pointer=json.loads((store/'LATEST.json').read_text()); snapshot=json.loads((store/'snapshots'/(pointer['snapshot_id']+'.json')).read_text())
  assert snapshot['quiescent'] and not snapshot['deferred']
  for relative,item in sorted(snapshot['files'].items()):
   path=base/'restored'/run/relative;assert path.is_file() and not path.is_symlink()
   name=run+'/'+relative;expected[name]=item['sha256'];total+=item['bytes'];tar.add(path,arcname=name,recursive=False)
with archive.open('rb') as f:os.fsync(f.fileno())
directory_fd=os.open(archive.parent,os.O_RDONLY)
try:os.fsync(directory_fd)
finally:os.close(directory_fd)
seen=set()
with tarfile.open(archive,'r:gz') as tar:
 for member in tar:
  assert member.isfile() and member.name in expected and member.name not in seen
  with tar.extractfile(member) as f:assert hashlib.file_digest(f,'sha256').hexdigest()==expected[member.name]
  seen.add(member.name)
assert seen==set(expected)
with archive.open('rb') as f:checksum=hashlib.file_digest(f,'sha256').hexdigest()
record={'created_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'path':str(archive),'bytes':archive.stat().st_size,'sha256':checksum,'logical_bytes':total,'member_count':len(seen),'tar_member_sha256_verification':'PASS','includes':'All four complete quiescent run artifacts, raw/scored/metrics/manifests/logs/attempts/checksums; no model weights, caches or credentials','run_code_commit':'47ae79f3f1c5fdf390ef23bfc9f8bd41b23d2726','restore':'Verify archive SHA256, extract to a NEW empty directory; use original runner at recorded commit with pinned config/benchmark/tokenizer assets to validate each run. Existing CAS stores and independently restored copies remain preserved.'}
(session/'portable-archive.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n');print(json.dumps(record))
