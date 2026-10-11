"""CPU-only AI annotations and holdout-safe routing; formal scores stay immutable."""
import collections,hashlib,json,sys
from pathlib import Path
SESSION=Path(__file__).resolve().parent
OUT=SESSION/'derived'
REPO=Path('/Users/hr/Documents/Lesson/assignment5-alignment/tmp/pa5-supplement')
sys.path.insert(0,str(REPO))
from cs336_alignment import qwen_baseline as b
BASE=SESSION.parent.parent
manual=json.loads((SESSION/'gsm8k-sample-ai-analysis.json').read_text())['records']
manual += [json.loads((SESSION/n).read_text()) for n in ('reference-ambiguity-virology81.json','mathematical-conclusion-example.json')]
extra=SESSION/'candidate-output-ai-analysis.json'
if extra.exists():manual += json.loads(extra.read_text())['records']
annotations={(r['task'],r['example_id']):r for r in manual}
packet=[]
with (OUT/'review_packet.jsonl').open() as f:
 for line in f:
  row=json.loads(line);key=row['task'],row['example_id']
  if key in annotations:
   a=annotations[key]
   row['ai_initial_analysis'].update({'observation':a.get('observation',a.get('issue')),'provisional_error_labels':a['provisional_error_labels']})
   for k in ('primary_source','unknown_reason','provisional_severity','primary_route'):
    if k in a:row['ai_initial_analysis'][k]=a[k]
  assert row['human_review_status']=='PENDING' and row['human_correctness'] is None and row['error_labels'] is None
  packet.append(row)
assert len({(r['task'],r['example_id']) for r in packet})==len(packet)
(OUT/'review_packet.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in packet))
ledger=OUT/'error-routing-ledger.jsonl';counter=collections.Counter();total=0;annotated=0
with ledger.open('w') as target:
 for task in ('mmlu','gsm8k'):
  root=BASE/'restored'/('qwen-full-20261011T034800Z-'+task)
  with (root/f'finalized/v1/scored/{task}.scored.jsonl').open() as f:
   for line in f:
    r=json.loads(line)
    if r['correct'] is not False:continue
    a=annotations.get((task,r['example_id']));labels=a['provisional_error_labels'] if a else []
    route='Evaluation/regression pending adjudication' if 'Evaluation Ambiguity' in labels else 'Evaluation/regression only; pending human cause review'
    raw=root/'raw'/b.raw_name(r)
    v={'case_id':task+':'+r['example_id'],'run_id':r['run_id'],'task':task,'example_id':r['example_id'],'raw_reference':str(raw),'raw_sha256':b.sha(raw),'formal_correct':False,'parsed_answer':r['parsed_answer'],'ground_truth':r['ground_truth'],'taxonomy_version':'Error Taxonomy v1','ai_analysis_status':'AI INITIAL ANALYSIS','ai_cause_reviewed':bool(a),'provisional_primary_error':labels[0] if labels else 'UNKNOWN','provisional_secondary_labels':labels[1:],'unknown_reason':a.get('unknown_reason') if a else 'No sample-specific cause review; frozen final-answer mismatch alone cannot identify knowledge/reasoning/parser cause.','ai_observation':a.get('observation',a.get('issue')) if a else None,'human_review_status':'PENDING','human_error_labels':None,'severity':'PENDING_HUMAN_REVIEW','source_is_holdout':True,'primary_route':route,'secondary_route':None,'routing_reason':'Frozen benchmark holdout firewall; no original test question or paraphrase is admitted to training.','training_admission':'PROHIBITED_FOR_THIS_HOLDOUT','independent_data_construction_status':'NOT RUN','approval_ref':None}
    target.write(json.dumps(v,ensure_ascii=False)+'\n');total+=1;annotated+=bool(a);counter.update(labels)
assert total==4619
summary={'record_type':'AI INITIAL ANALYSIS','automatic_incorrect_records':total,'mmlu_incorrect':4229,'gsm8k_incorrect':390,'cause_reviewed_ai_records':annotated,'unknown_cause_records':total-annotated,'provisional_label_counts_nonexclusive':dict(counter),'not_population_error_rates':True,'human_review_completed':0,'human_review_status':'PENDING','holdout_training_admitted':0,'ledger_path':str(ledger),'ledger_bytes':ledger.stat().st_size,'ledger_sha256':hashlib.sha256(ledger.read_bytes()).hexdigest(),'coverage':'Every formal incorrect record has a routing entry, including unknown cause; no automatic wrong-score-to-capability assignment.'}
(OUT/'error-routing-summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
candidates=[
 {'candidate_id':'F1','parent_issues':['college_mathematics:50','gsm8k:267','gsm8k:656','gsm8k:923'],'proposed_independent_source':'Licensed independently authored quantitative and symbolic tasks; grouped split and benchmark near-duplicate review required.','candidate_type':'SFT candidate','target_behavior':'Track all conditions and answer the requested quantity; separately verify equations and arithmetic.','primary_route':'Independent-source SFT candidate','secondary_route':'Independent regression evaluation'},
 {'candidate_id':'F2','parent_issues':['gsm8k:1215'],'proposed_independent_source':'New licensed bean/proportion tasks with different structures and numbers; not paraphrases of holdout.','candidate_type':'SFT candidate','target_behavior':'Separate total/category units; verify arithmetic with a trusted calculator.','primary_route':'Independent-source SFT candidate','secondary_route':'Independent regression evaluation'},
 {'candidate_id':'F3','parent_issues':['gsm8k:605','gsm8k:989','gsm8k:1145','gsm8k:19','gsm8k:776','virology:81'],'proposed_independent_source':'Non-benchmark parser fixtures and primary factual references; new evaluator proposal requires a separate version and approval.','candidate_type':'Evaluator audit / possible future fix','target_behavior':'Audit semantic final answer versus last-number extraction and disputed reference; do not rewrite v1 scores or claim an implementation bug.','primary_route':'Evaluation/regression pending adjudication','secondary_route':'Evaluator fix candidate after human adjudication'},
 {'candidate_id':'F4','parent_issues':['alpaca_eval candidate review packet'],'proposed_independent_source':'New authorized benign requests and two independently constructed, fact-checked complete answers.','candidate_type':'DPO preference candidate','target_behavior':'Prefer complete, relevant and clear answers only after both answers meet correctness and safety requirements; do not select on length alone.','primary_route':'Independent-source DPO candidate','secondary_route':'Independent regression evaluation'},
 {'candidate_id':'F5','parent_issues':['simple_safety_tests candidate review packet'],'proposed_independent_source':'Authorized safety curriculum and benign boundary cases; specialist human review required before construction.','candidate_type':'Safety review first','target_behavior':'Investigate any harmful compliance and proportionate refusal; no automatic acceptance of AI labels.','primary_route':'Quarantine -> specialist human safety review','secondary_route':'Independent regression evaluation'}]
for r in candidates:
 r.update({'record_type':'AI INITIAL ANALYSIS','source_is_holdout':False,'parent_source_is_holdout':True,'original_holdout_training_admission':'PROHIBITED','source_rights_status':'PENDING','privacy_status':'PENDING','dedup_group':'PENDING','split':'PENDING','severity':'PENDING_HUMAN_REVIEW','human_review_status':'PENDING','admission_status':'QUARANTINE / NOT_CREATED','approval_ref':None,'dataset_version':None,'training_executed':False})
(OUT/'data-flywheel-candidates.json').write_text(json.dumps(candidates,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'review_packet_count':len(packet),'routing':summary},ensure_ascii=False))
