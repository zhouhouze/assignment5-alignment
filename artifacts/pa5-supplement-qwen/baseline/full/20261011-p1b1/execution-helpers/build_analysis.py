"""Derived CPU reporting from verified restored full artifacts. Never alters raw."""
import collections,hashlib,json,math,random,sys
from pathlib import Path
REPO=Path('/Users/hr/Documents/Lesson/assignment5-alignment/tmp/pa5-supplement');sys.path.insert(0,str(REPO))
from cs336_alignment import qwen_baseline as b
from cs336_alignment import qwen_baseline_storage as st
BASE=Path('/Users/hr/Documents/Lesson/pa5-experiment-backups');SESSION=BASE/'full/p1b1-20261011-session'
OUT=SESSION/'derived';OUT.mkdir(exist_ok=False)
PREFIX='qwen-full-20261011T034800Z';all_rows={};results={};runtime={}
for task in b.TASKS:
 root=BASE/'restored'/(PREFIX+'-'+task)
 m,inputs,rows=b.validate_full(root);assert len(rows)==m['expected_count']==b.FULL_COUNTS[task]
 scored=[json.loads(line) for line in (root/f'finalized/v1/scored/{task}.scored.jsonl').open()]
 assert len(scored)==len(rows)
 metrics=json.loads((root/'finalized/v1/metrics.json').read_text())['results'][task]
 all_rows[task]=scored;results[task]=metrics
 end=[json.loads(p.read_text()) for p in (root/'attempts').glob('*/end.json')]
 start=[json.loads(p.read_text()) for p in (root/'attempts').glob('*/start.json')]
 runtime[task]={'starts':[{k:s.get(k) for k in ('start_time','run_code_commit','git_dirty','reserved_seconds')} for s in start],'ends':end,'vram':[json.loads(p.read_text()) for p in (root/'attempts').glob('*/vram.json')],'model_load_seconds':[json.loads(p.read_text())['load_seconds'] for p in (root/'attempts').glob('*/runtime.json')]}
subjects=collections.defaultdict(list)
for r in all_rows['mmlu']:subjects[r['raw_input']['subject']].append(r)
subject_metrics={s:{'n':len(rows),'correct':sum(r['correct'] for r in rows),'accuracy':sum(r['correct'] for r in rows)/len(rows),'parse_failures':sum(r['parse_failure'] for r in rows)} for s,rows in sorted(subjects.items())}
assert sum(v['n'] for v in subject_metrics.values())==14042
assert sum(v['correct'] for v in subject_metrics.values())==results['mmlu']['correct_count']
diagnostics={}
for task,rows in all_rows.items():
 lengths=[r['response_token_count'] for r in rows];bounds=[('zero',0,0),('1_to_32',1,32),('33_to_128',33,128),('129_to_256',129,256),('257_to_511',257,511),('512',512,512)]
 hist={label:sum(lo<=x<=hi for x in lengths) for label,lo,hi in bounds};assert sum(hist.values())==len(rows)
 batches={r['batch_id']:r['batch_seconds'] for r in rows};ts=sorted(batches.values())
 diagnostics[task]={'n':len(rows),'token_count_sum':sum(lengths),'min_response_tokens':min(lengths),'max_response_tokens':max(lengths),'token_length_histogram':hist,'empty_response_rate':results[task]['empty_count']/len(rows),'whitespace_only_count':results[task]['whitespace_only_count'],'max_token_termination_rate':results[task]['length_termination_count']/len(rows),'finish_reasons':results[task]['finish_reasons'],'batch_count':len(ts),'batch_latency_mean_seconds':math.fsum(ts)/len(ts),'batch_latency_median_seconds':(ts[(len(ts)-1)//2]+ts[len(ts)//2])/2,'batch_latency_p95_seconds':ts[math.ceil(.95*len(ts))-1],'request_latency_status':'NOT RUN','evaluation_protocol_id':'SUP-QWEN-EVAL-v1','not_human_review':True}
review=[];selection=[];rng=random.Random(0);seen=set()
def sample(task,rows,n,reason):
 pool=sorted([r for r in rows if (task,r['example_id']) not in seen],key=lambda r:r['example_id'])
 chosen=rng.sample(pool,min(n,len(pool)))
 selection.append({'task':task,'stratum':reason,'eligible_after_previous_strata':len(pool),'requested':n,'selected_ids':[r['example_id'] for r in chosen]})
 for r in chosen:
  seen.add((task,r['example_id']))
  if r.get('parse_failure'):observation='冻结 parser 未能提取最终答案；保留为错误并待复核格式及原文。不能据此断言 parser 实现错误。'
  elif r.get('correct') is False:observation=f"冻结 parser 提取 {r.get('parsed_answer')}，与 ground truth {r['ground_truth']} 不同；知识/推理/计算等具体成因待原文审查。"
  elif r.get('correct') is True:observation='最终提取答案匹配 ground truth；不代表解释或推理已验证正确。'
  else:observation='仅候选回答；Judge NOT RUN，不给正式胜率或 Safety Rate。'
  if r['finish_reason']=='length':observation+=' finish_reason=length；语义是否未完成需另行阅读，不自动等同截断。'
  root=BASE/'restored'/(PREFIX+'-'+task);raw=root/'raw'/b.raw_name(r)
  review.append({'run_id':r['run_id'],'task':task,'example_id':r['example_id'],'raw_reference':str(raw),'raw_sha256':b.sha(raw),'selection_seed':0,'selection_reason':reason,'prompt':r['formatted_prompt'],'raw_input':r['raw_input'],'raw_response':r['raw_response'],'ground_truth':r['ground_truth'],'automated_score':{k:r.get(k) for k in ('parsed_answer','correct','parse_failure','evaluation_status')},'response_token_count':r['response_token_count'],'finish_reason':r['finish_reason'],'automatic_score_status':'COMPLETE' if task in ('mmlu','gsm8k') else 'NOT RUN','ai_analysis_status':'AI INITIAL ANALYSIS','ai_initial_analysis':{'author':'Codex / AI INITIAL ANALYSIS','not_human_review':True,'observation':observation,'provisional_error_labels':[]},'human_review_status':'PENDING','human_correctness':None,'error_labels':None,'human_notes':None,'reviewer_id':None,'reviewed_at':None,'rubric_version':'SUP-QWEN-EVAL-v1 / Error Taxonomy v1','disagreement':None,'source_is_holdout':True,'training_admission':'PROHIBITED_FOR_THIS_HOLDOUT'})
for task in ('mmlu','gsm8k'):
 rows=all_rows[task]
 sample(task,[r for r in rows if r['correct'] is False],10,'random_incorrect_seed0')
 sample(task,[r for r in rows if r['correct'] is True],2,'correct_control_seed0')
 sample(task,[r for r in rows if r['parse_failure']],2,'parse_failure_diagnostic_seed0')
 sample(task,[r for r in rows if r['finish_reason']=='length'],2,'length_diagnostic_seed0')
sample('alpaca_eval',all_rows['alpaca_eval'],5,'random_open_task_seed0')
sample('alpaca_eval',[r for r in all_rows['alpaca_eval'] if r['finish_reason']=='length'],2,'length_diagnostic_seed0')
sample('alpaca_eval',[r for r in all_rows['alpaca_eval'] if r['example_id']=='0'],1,'targeted_factual_reference_diagnostic_not_random')
safety=collections.defaultdict(list)
for r in all_rows['simple_safety_tests']:safety[r['raw_input']['harm_area']].append(r)
for area,rows in sorted(safety.items()):sample('simple_safety_tests',rows,2,'harm_area_'+area+'_seed0')
for name,value in [('combined-metrics.json',results),('subject-metrics.json',subject_metrics),('subject-summary.json',{'subject_n':len(subject_metrics),'micro_accuracy':results['mmlu']['accuracy'],'macro_accuracy':sum(v['accuracy'] for v in subject_metrics.values())/len(subject_metrics),'micro_is_primary':True,'macro_is_diagnostic':True}),('diagnostics.json',diagnostics),('runtime-details.json',runtime),('review-selection.json',{'seed':0,'algorithm':'Python random.Random(0); TASK order and successive fixed strata; sorted example_id pools; without replacement within each task','strata':selection,'count':len(review),'human_review_status':'PENDING','human_review_completed':0,'not_population_error_rate':True,'original_pilot_packet_unchanged':True})]:
 (OUT/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
(OUT/'review_packet.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in review))
print(json.dumps({'count':16266,'metrics':results,'review_count':len(review),'subject_count':len(subject_metrics),'out':str(OUT)},ensure_ascii=False))
