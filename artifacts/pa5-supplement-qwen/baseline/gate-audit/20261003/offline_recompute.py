"""Independent CPU recomputation from saved raw; never generate or modify raw."""
from pathlib import Path
from collections import Counter
from decimal import Decimal
import argparse,json,hashlib,math
from cs336_alignment.supplement_metrics import parse_mmlu_response,parse_gsm8k_response

def main():
 p=argparse.ArgumentParser();p.add_argument('run_dir',type=Path);a=p.parse_args();d=a.run_dir
 raw_files=sorted((d/'raw').glob('*.jsonl'))
 before={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in raw_files}
 selected=json.loads((d/'selected_examples.json').read_text());manifest=json.loads((d/'manifest.json').read_text())
 expected={(r['task'],r['example_id']) for r in selected}
 rows=[json.loads(f.read_text()) for f in raw_files]
 assert len(rows)==len(expected)==len(selected)
 assert {(r['task'],r['example_id']) for r in rows}==expected
 summary=json.loads((d/'metrics-v1.json').read_text()); results={}
 for task in summary['results']:
  rs=[r for r in rows if r['task']==task]; n=len(rs); ls=sorted(r['response_token_count'] for r in rs)
  assert n==(1 if manifest['stage']=='SMOKE' else 20)
  assert all(len(r['response_token_ids'])==r['response_token_count'] for r in rs)
  scored={x['example_id']:x for x in map(json.loads,(d/'scored/v1'/f'{task}.scored.jsonl').read_text().splitlines())}
  assert len(scored)==n
  correct=0;failures=0
  for r in rs:
   ans=parse_mmlu_response(r['raw_response']) if task=='mmlu' else parse_gsm8k_response(r['raw_response']) if task=='gsm8k' else None
   ok=(ans is not None and (ans==r['ground_truth'] if task=='mmlu' else Decimal(ans)==Decimal(r['ground_truth']))) if task in ['mmlu','gsm8k'] else None
   assert scored[r['example_id']]['parsed_answer']==ans and scored[r['example_id']]['correct']==ok
   correct+=bool(ok);failures+=ans is None
  batches={}
  for r in rs:
   if r['batch_id'] in batches: assert batches[r['batch_id']]==r['batch_seconds']
   batches[r['batch_id']]=r['batch_seconds']
  sec=sum(batches.values())
  out={'n':n,'generation_success':n,'empty_count':sum(r['raw_response']=='' for r in rs),'length_termination_count':sum(r['finish_reason']=='length' for r in rs),'average_response_tokens':sum(ls)/n,'median_response_tokens':ls[n//2] if n%2 else (ls[n//2-1]+ls[n//2])/2,'p95_response_tokens':ls[math.ceil(.95*n)-1],'max_response_tokens':max(ls),'finish_reasons':dict(Counter(r['finish_reason'] for r in rs)),'generation_seconds':sec,'examples_per_second':n/sec,'output_tokens_per_second':sum(ls)/sec,'generation_success_rate':1.0,'stop_reasons':dict(Counter(str(r['stop_reason']) for r in rs))}
  if task in ['mmlu','gsm8k']:out.update(accuracy=correct/n,correct_count=correct,wrong_count=n-correct,parse_failures=failures,parse_failure_rate=failures/n,wrong_count_includes_parse_failures=True)
  for key,val in summary['results'][task].items():
   if key in ['timing_scope','evaluation_status']:continue
   assert key in out,(task,key)
   assert math.isclose(out[key],val,rel_tol=1e-12,abs_tol=1e-12) if isinstance(val,float) else out[key]==val,(task,key,out[key],val)
  results[task]=out
 after={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in raw_files};assert before==after
 result={'recomputation_check':'PASS','stage':manifest['stage'],'directly_comparable_to_official':False,'independent_of_runner_summarize':True,'parsers':'unchanged Supplement parsers','raw_unchanged':True,'raw_count':len(rows),'results':results,'raw_sha256':before}
 with (d/'offline-recomputation.json').open('x') as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
 print(json.dumps({k:v for k,v in result.items() if k!='raw_sha256'},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
