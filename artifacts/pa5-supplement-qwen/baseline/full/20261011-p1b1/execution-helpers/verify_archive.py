import gzip,hashlib,json,re,subprocess,datetime
from pathlib import Path
R=Path('/Users/hr/Documents/Lesson/assignment5-alignment/tmp/pa5-supplement');S=Path(__file__).resolve().parent;A=R/'artifacts/pa5-supplement-qwen/baseline/full/20261011-p1b1'
count=0
for line in (A/'SHA256SUMS').open():
 expected,relative=line.strip().split(maxsplit=1);p=R/relative;assert hashlib.sha256(p.read_bytes()).hexdigest()==expected;count+=1
parsed=0
for p in A.rglob('*'):
 if not p.is_file():continue
 data=gzip.decompress(p.read_bytes()) if p.suffix=='.gz' else p.read_bytes()
 name=p.name.removesuffix('.gz')
 if name.endswith('.json'):json.loads(data);parsed+=1
 elif name.endswith('.jsonl'):
  for line in data.split(b'\n'):
   if line:json.loads(line)
  parsed+=1
packet=[]
with (A/'analysis/review_packet.jsonl').open() as f:
 for line in f:packet.append(json.loads(line))
assert len(packet)==44
for row in packet:
 assert row['human_review_status']=='PENDING' and all(row[k] is None for k in ('human_correctness','error_labels','human_notes','reviewer_id','reviewed_at'))
 raw=Path(row['raw_reference']);assert hashlib.sha256(raw.read_bytes()).hexdigest()==row['raw_sha256']
 with raw.open() as f:original=json.loads(next(f))
 assert row['raw_response']==original['raw_response'] and row['prompt']==original['formatted_prompt'] and row['raw_input']==original['raw_input']
 assert row['training_admission']=='PROHIBITED_FOR_THIS_HOLDOUT'
ledger=gzip.decompress((A/'analysis/error-routing-ledger.jsonl.gz').read_bytes());rows=[json.loads(line) for line in ledger.split(b'\n') if line]
assert len(rows)==4619 and len({r['case_id'] for r in rows})==4619
assert all(r['training_admission']=='PROHIBITED_FOR_THIS_HOLDOUT' and r['human_review_status']=='PENDING' for r in rows)
changed=sorted(set(subprocess.check_output(['git','diff','--name-only'],cwd=R,text=True).splitlines()+subprocess.check_output(['git','diff','--cached','--name-only'],cwd=R,text=True).splitlines()))
assert all(n.startswith(('notes/','artifacts/pa5-supplement-qwen/baseline/full/20261011-p1b1/')) for n in changed),changed
newdocs=[p for p in (R/'notes/experiments/SUP-QWEN-evaluation').glob('*.md') if p.name in ('p1b-full-baseline-report.md','qwen-base-behavior-profile.md','p1b-runtime-cost-report.md')]
links=[]
for p in newdocs+[R/x for x in changed if x.endswith('.md')]:
 for target in re.findall(r'\]\(([^)]+)\)',p.read_text()):
  if target.startswith(('https:','http:','#','mailto:')):continue
  file=target.split('#')[0]
  if file and not (p.parent/file).exists():links.append((str(p.relative_to(R)),target))
assert not links,links
patterns=[rb'-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----',rb'github_pat_[A-Za-z0-9_]{30,}',rb'ghp_[A-Za-z0-9]{30,}',rb'hf_[A-Za-z0-9]{25,}',rb'(?i)(?:password|passwd|api_key|access_token)\s*[=:]\s*[\"\x27][^\"\x27\r\n]{6,}']
findings=[]
for p in list(A.rglob('*'))+newdocs+[R/x for x in changed]:
 if not p.is_file():continue
 data=gzip.decompress(p.read_bytes()) if p.suffix=='.gz' else p.read_bytes()
 if any(re.search(x,data) for x in patterns):findings.append(str(p.relative_to(R)))
assert not findings,findings
result={'checked_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'PASS','evidence_sha_files':count,'parsed_json_jsonl_artifacts':parsed,'review_original_response_prompt_input_sha_matches':len(packet),'human_review_completed':0,'error_routing_unique_records':len(rows),'holdout_training_admitted':0,'broken_local_links':links,'secret_pattern_findings':findings,'frozen_or_runtime_source_edits':False,'checks':'Small archive checksum/JSON/physical-LF review provenance/holdout routing/links/secret patterns; real full Runner+recomputation/restore checks are separate evidence.'}
(S/'archive-validation.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
