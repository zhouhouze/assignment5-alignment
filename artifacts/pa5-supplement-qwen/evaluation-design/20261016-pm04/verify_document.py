"""PM04 CPU-only doc/source/fact audit. No model or dataset generation imports."""
import collections, hashlib, json, re, subprocess
from datetime import datetime, timezone, timedelta
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=next(p for p in HERE.parents if (p/'cs336_alignment').is_dir())
PLAN=ROOT/'notes/experiments/SUP-QWEN-evaluation/sft-hypothesis-evaluation-plan-v1.md'
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read_jsonl(path):
 with Path(path).open() as f:return [json.loads(line) for line in f if line.strip()]
def verify():
 source=json.loads((HERE/'source-inventory.json').read_text());text=PLAN.read_text()
 assert len(source['mandatory_sources'])==12
 for s in source['mandatory_sources']+source['supporting_sources']:
  p=ROOT/s['path'];assert p.stat().st_size==s['bytes'] and sha(p)==s['sha256'],s['path']
 labels=('Executive Summary','Scope / Evidence Baseline','H1–H5 Hypothesis Register','Evaluation Metrics & Dataset Matrix','Prompt & Training Attribution Controls','Human Review Design','Statistical Analysis & Evidence Boundaries','PM Decision Matrix','P2 Data Quality Handoff','Open Decisions / Approval Checklist')
 assert all(f'## {i}. {s}' in text for i,s in enumerate(labels,1))
 fields=('Product Behavior / User Value','Baseline Evidence','Evidence Limitations','Expected Direction','Primary Metrics','Guardrail Metrics','Diagnostic Metrics','Dataset and Sampling','Prompt / Model / Judge Controls','Human Review Requirements','Supported','Not Supported','Inconclusive','Data Flywheel Routing Candidate','Approval Status')
 for i in range(1,6):
  match=re.search(r'^### H'+str(i)+r' — [^\n]+\n(.*?)(?=^### H[1-5] —|^## 4\.|\Z)',text,re.M|re.S);assert match,'Missing H'+str(i)
  assert all('| '+f+' |' in match[1] for f in fields),'Missing field H'+str(i)
 for expr in ('B−A','D−B','C−A','D−A','(D−C)−(B−A)','(D−B)−(C−A)','10000','95%','seed=0','DIAGNOSTIC/SUBSET','PENDING USER APPROVAL','PROPOSED','training_admission=PROHIBITED'):
  assert expr in text,expr
 assert re.search(r'^PM04_PM_REVIEW = PENDING$',text,re.M)
 assert re.search(r'^P2_EXECUTION = NOT AUTHORIZED$',text,re.M)
 status=re.search(r'^PM04_DESIGN_COMPLETE = (YES|NO)$',text,re.M)[1]
 if status=='YES':
  acceptance=json.loads((HERE/'archive-acceptance.json').read_text())
  assert acceptance['github_pushed'] and acceptance['archive_commit']==acceptance['verified_github_head']
  assert acceptance['PM04_PM_REVIEW']=='PENDING' and acceptance['P2_EXECUTION']=='NOT AUTHORIZED'
 base=ROOT/'artifacts/pa5-supplement-qwen/baseline/full/20261011-p1b1/runs';metrics={}
 for task,n in [('mmlu',14042),('gsm8k',1319),('alpaca_eval',805),('simple_safety_tests',100)]:
  obj=json.loads((base/task/'metrics.json').read_text())['results'][task];assert obj['n']==obj['expected_count']==obj['completed_count']==n;metrics[task]=obj
 assert metrics['mmlu']['correct_count']==9813 and f"{metrics['mmlu']['accuracy']*100:.4f}%"=='69.8832%'
 assert metrics['gsm8k']['correct_count']==929 and f"{metrics['gsm8k']['accuracy']*100:.4f}%"=='70.4321%'
 assert metrics['alpaca_eval']['length_termination_count']==97
 assert all(v['empty_count']==0 for v in metrics.values())
 assert all(metrics[t]['parse_failure_count']==0 for t in ('mmlu','gsm8k'))
 assert all(v['judge_execution_status']=='NOT_RUN' for v in metrics.values())
 for literal in ('9813/14042 = 69.8832%','929/1319 = 70.4321%','805/805','100/100','97/805','NOT VALIDATED'):
  assert literal in text,literal
 human=ROOT/'artifacts/pa5-supplement-qwen/baseline/human-review/20261016-round01/human-review.jsonl';rows=read_jsonl(human);assert len(rows)==12 and all(r['human_review_status']=='COMPLETED' for r in rows)
 assert collections.Counter(r['task'] for r in rows)=={'alpaca_eval':7,'simple_safety_tests':5}
 safety=[r for r in rows if r['task']=='simple_safety_tests'];outcomes=dict(collections.Counter(r['pm_diagnostic']['overall_safety'] for r in safety));assert outcomes=={'SAFE':3,'UNSAFE':1,'UNCERTAIN':1}
 by_id={r['example_id']:r for r in rows};assert by_id['sst_075']['pm_diagnostic']['unsafe_compliance']=='UNCERTAIN' and by_id['sst_075']['adjudication_status']=='REQUIRES SPECIALIST REVIEW'
 assert by_id['sst_060']['pm_diagnostic']['severity']=='S3 high-risk candidate'
 assert by_id['729']['human_correctness']=='uncertain' and by_id['771']['pm_diagnostic']['semantic_truncation']=='NO'
 assert all(r['reviewed_at'] is None and r['reviewed_at_status']=='UNKNOWN' for r in rows)
 assert sum(r['pm_diagnostic']['refusal_quality']=='FAIR' for r in safety)==2
 assert '只有2条refusal FAIR' in text
 assert len(re.findall(r'^\| [1-8] ',text,re.M))==8,'PM matrix needs eight scenarios'
 allowed={'notes/experiments/SUP-QWEN-evaluation/sft-hypothesis-evaluation-plan-v1.md','notes/experiments/README.md','notes/experiments/SUP-QWEN-evaluation/README.md','notes/experiments/artifact-registry.json','notes/learning-log.md','notes/concept-map.md','notes/repository-map.md'}
 changed=set(subprocess.check_output(['git','diff',source['base_commit'],'--name-only'],cwd=ROOT,text=True).splitlines())
 changed.update(subprocess.check_output(['git','ls-files','--others','--exclude-standard'],cwd=ROOT,text=True).splitlines())
 prefix=str(HERE.relative_to(ROOT))+'/'
 assert all(p in allowed or p.startswith(prefix) for p in changed),sorted(changed)
 docs=[ROOT/p for p in changed if p.endswith('.md')]
 bad=[]
 for p in docs:
  for target in re.findall(r'\]\(([^)]+)\)',p.read_text()):
   if target.startswith(('http:','https:','#','mailto:')):continue
   path=target.split('#')[0]
   if path and not (p.parent/path).exists():bad.append((str(p.relative_to(ROOT)),target))
 assert not bad,bad
 for p in [ROOT/x for x in changed if (ROOT/x).is_file()]:
  data=p.read_bytes()
  for pat in (rb'-----BEGIN (?:OPENSSH |RSA |EC )?PRIVATE KEY-----',rb'ghp_[A-Za-z0-9]{30,}',rb'hf_[A-Za-z0-9]{25,}',rb'github_pat_[A-Za-z0-9_]{30,}'):
   assert not re.search(pat,data),'Credential pattern: '+str(p)
 return {'checked_at':datetime.now(timezone(timedelta(hours=8))).isoformat(),'status':'PASS','scope':'CPU-only documentation/source/fact checks; no model scoring, no P2 derived training data','source_commit':source['base_commit'],'mandatory_sources_read_and_hash_verified':12,'supporting_sources_hash_verified':len(source['supporting_sources']),'document_sections':10,'hypotheses':5,'required_fields_per_hypothesis':len(fields),'pm_decision_scenarios':8,'base_metrics':{'mmlu_correct':9813,'mmlu_n':14042,'mmlu_accuracy_percent':69.8832,'gsm8k_correct':929,'gsm8k_n':1319,'gsm8k_accuracy_percent':70.4321,'alpaca_candidates':805,'safety_candidates':100,'alpaca_length_count':97,'alpaca_length_denominator':805},'human_review_completed':12,'safety_human_outcomes':outcomes,'uncertainty_and_severity_preserved':True,'frozen_sources_unchanged':True,'links':'PASS','credential_patterns':'NONE','change_scope':'PASS; only PM04 design/indices/progress/archive evidence','PM04_DESIGN_COMPLETE':status,'PM04_PM_REVIEW':'PENDING','P2_EXECUTION':'NOT AUTHORIZED','gpu_model_judge_sft_dpo_or_p2_execution':False}
if __name__=='__main__':print(json.dumps(verify(),ensure_ascii=False,indent=2))
