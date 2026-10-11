"""Collect small evidence only after the four completed independent restores."""
import datetime,gzip,hashlib,json,shutil,subprocess
from pathlib import Path
S=Path(__file__).resolve().parent
B=S.parent.parent
R=Path('/Users/hr/Documents/Lesson/assignment5-alignment/tmp/pa5-supplement')
A=R/'artifacts/pa5-supplement-qwen/baseline/full/20261011-p1b1'
TASKS=('mmlu','gsm8k','alpaca_eval','simple_safety_tests')
PREFIX='qwen-full-20261011T034800Z'; COMMIT='47ae79f3f1c5fdf390ef23bfc9f8bd41b23d2726'
assert 'ALL_FOUR_TASKS_COMPLETE' in (S/'workflow-events.jsonl').read_text()
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip()==COMMIT
assert subprocess.check_output(['git','status','--porcelain'],cwd=R,text=True).strip()==''
assert json.loads((S/'portable-archive.json').read_text())['tar_member_sha256_verification']=='PASS'
assert (S/'derived/error-routing-summary.json').is_file()
A.mkdir(parents=True,exist_ok=False)
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def copy(src,dest):
 target=A/dest;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,target)
def zipped(src,dest):
 target=A/dest;target.parent.mkdir(parents=True,exist_ok=True)
 with target.open('wb') as f:
  with gzip.GzipFile(filename='',fileobj=f,mode='wb',mtime=0) as z:z.write(src.read_bytes())
 assert gzip.decompress(target.read_bytes())==src.read_bytes()
external=[];restores={}
for task in TASKS:
 run=PREFIX+'-'+task; root=B/'restored'/run;store=B/'full'/run
 cert=json.loads((S/f'restore-validation-{task}.json').read_text());assert cert['status']=='PASS' and cert['quiescent'] and not cert['deferred']
 restores[task]=cert
 for src,dest in [('manifest.json','manifest-initial.json'),('manifest.sha256','manifest-initial.sha256'),('input-check.json','input-check.json'),('progress.json','progress-final.json'),('finalized/v1/manifest-final.json','manifest-final.json'),('finalized/v1/metrics.json','metrics.json'),('finalized/v1/checks/integrity-report.json','integrity-report.json'),('finalized/v1/checks/recomputation-report.json','recomputation-report.json'),('finalized/v1/SHA256SUMS','full-bundle-SHA256SUMS'),('logs/generation.log','generation.log')]:copy(root/src,f'runs/{task}/{dest}')
 inventory=root/'finalized/v1/checks/source-inventory.json';zipped(inventory,f'runs/{task}/source-inventory.json.gz')
 pointer=json.loads((store/'LATEST.json').read_text());snapshot=store/'snapshots'/(pointer['snapshot_id']+'.json')
 assert sha(snapshot)==cert['snapshot_sha256']
 zipped(snapshot,f'runs/{task}/quiescent-source-snapshot.json.gz')
 copy(store/'backup-events.jsonl',f'runs/{task}/backup-events.jsonl')
 for log in S.glob(f'*{task}*.json'):
  if log.name.startswith(('launch-','prepare-','restore-validation-','final-backup-status-','cloud-final-','initial-status-','worker-','monitor-')):copy(log,'session-evidence/'+log.name)
 copy(S/f'telemetry-{task}.jsonl',f'session-evidence/telemetry-{task}.jsonl')
 for name in (f'score-{task}.log',):
  if (S/name).exists():copy(S/name,'session-evidence/'+name)
 external.append({'artifact_name':run+' quiescent snapshot manifest','storage_location':str(snapshot),'bytes':snapshot.stat().st_size,'sha256':sha(snapshot),'created_at':cert['at'],'run_id':run,'source_commit':COMMIT,'storage':'Mac CAS snapshot + all referenced objects','restored_path':str(root),'logical_artifact_bytes':cert['logical_bytes'],'durability':'VERIFIED_MAC_COPY_AND_INDEPENDENT_RESTORE; same Mac disk is not offsite redundancy','restore':'Preserve entire sibling store including objects/snapshots/LATEST; original scripts/qwen_artifact_backup.py restore --store STORE --destination NEW_DIR. Validate from source commit with pinned assets. Portable tar is another verified representation.'})
for name in ('console-check.json','resource-preflight.json','execution-session.json','workflow-events.jsonl','cpu-analysis-reader-fix.json','reference-ambiguity-virology81.json','mathematical-conclusion-example.json','gsm8k-sample-ai-analysis.json','candidate-output-ai-analysis.json','close-resource-check.json','historical-preservation-check.json'):
 if (S/name).exists():copy(S/name,'session-evidence/'+name)
for name in ('execute_remaining.py','monitor_live.py','build_analysis.py','augment_analysis.py','pack_verified_runs.py','collect_archive.py'):
 copy(S/name,'execution-helpers/'+name)
for p in sorted((S/'derived').iterdir()):
 if p.name not in ('runtime-details.json','error-routing-ledger.jsonl'):copy(p,'analysis/'+p.name)
zipped(S/'derived/error-routing-ledger.jsonl','analysis/error-routing-ledger.jsonl.gz')
portable=json.loads((S/'portable-archive.json').read_text());copy(S/'portable-archive.json','portable-archive.json')
external.append({'artifact_name':'Four verified Qwen FULL runs portable archive','storage_location':portable['path'],'bytes':portable['bytes'],'sha256':portable['sha256'],'created_at':portable['created_at'],'run_id':PREFIX,'source_commit':COMMIT,'storage':'local_archive_outside_repository','restore':portable['restore'],'durability':'Mac archive independently member-hash verified; no cloud-release recovery guarantee'})
(A/'external-artifacts.json').write_text(json.dumps(external,ensure_ascii=False,indent=2)+'\n')
(A/'restore-summary.json').write_text(json.dumps(restores,ensure_ascii=False,indent=2)+'\n')
(A/'README.md').write_text('''# P1B-1 real FULL evidence\n\nFour task-specific runs; run_code_commit `47ae79f3f1c5fdf390ef23bfc9f8bd41b23d2726`. Adapted reproduction, directly_comparable_to_official=false. Original manifests and formal metrics are copied byte-for-byte; AI INITIAL ANALYSIS and human PENDING are separate.\n\n- `runs/*/source-inventory.json.gz` and `quiescent-source-snapshot.json.gz` decompress to the exact original cloud/backup JSON; they enumerate external artifact bytes/SHA.\n- `full-bundle-SHA256SUMS` refers to paths in the **external full finalized bundle**, not this reduced Git directory. `SHA256SUMS` at this evidence root covers files actually included here.\n- Raw/scored/selected inputs/attempt details/complete VRAM samples remain in verified Mac CAS, independent restored directories and portable archive. See external-artifacts.json and the repository registry. Downloadable weights/tokenizer/config/environment are pinned, not archived as weights.\n- `execution-helpers/` records external orchestration/reporting source used this session; it was outside the clean inference tree and is **not** falsely attributed to run_code_commit. It calls the existing runner/backup implementation, implements no new inference path and must not be rerun as a new experiment without authorization.\n- `analysis/review_packet.jsonl`: preserve exact raw original response, reference and frozen score; human fields null/PENDING. Use physical LF JSONL iteration, not Unicode str.splitlines().\n- All holdout questions stay evaluation-only. Routing ledger labels are provisional where examined, UNKNOWN elsewhere; no SFT/DPO/Judge was run.\n\nReports: ../../../../../notes/experiments/SUP-QWEN-evaluation/p1b-full-baseline-report.md and qwen-base-behavior-profile.md.\n''')
print(json.dumps({'archive_path':str(A),'files':sum(p.is_file() for p in A.rglob('*')),'bytes':sum(p.stat().st_size for p in A.rglob('*') if p.is_file())}))
