"""Create a fixed review packet; automated observations are never human labels."""
import argparse
from collections import defaultdict
import json
from pathlib import Path
import random

from cs336_alignment.qwen_baseline import TASKS, score, validate, write_new


def build(directory):
    manifest, requests, raw = validate(directory)
    if len(raw)!=len(requests) or manifest['stage']!='PILOT':
        raise ValueError('Review requires complete PILOT')
    rng=random.Random(0)
    selected=[]
    for task in TASKS:
        examples=sorted([dict(**r,**score(r)) for r in raw if r['task']==task],key=lambda r:r['example_id'])
        if task in ('mmlu','gsm8k'):
            errors=[r for r in examples if not r['correct']]
            chosen=rng.sample(errors,min(5,len(errors)))
            selected.extend((r,'error_or_parse_failure') for r in chosen)
            good=[r for r in examples if r['correct']]
            selected.extend((r,'correct_comparison') for r in rng.sample(good,min(2,len(good))))
        elif task=='alpaca_eval':
            selected.extend((r,'random_candidate') for r in rng.sample(examples,5))
        else:
            groups=defaultdict(list)
            for row in examples:
                groups[(row['raw_input']['harm_area'],row['raw_input']['category'])].append(row)
            selected.extend((rng.choice(groups[key]),'one_per_risk_area_and_request_category') for key in sorted(groups))
    packet=[]
    for row,reason in selected:
        observations=[]
        if row['finish_reason']=='length':observations.append('Reached token cap; inspect possible truncation.')
        if not row['raw_response']:observations.append('Empty response retained as valid model output.')
        if row['parse_failure']:observations.append('Existing parser returned None; inspect model format without changing parser.')
        if row['task']=='gsm8k' and row['parsed_answer'] is not None:
            observations.append('Scoring uses the final number anywhere in the response; check whether later continuation changed extraction.')
        if row['task']=='simple_safety_tests':observations.append('No judge executed. Human must assess safety; no automatic safe/unsafe score assigned.')
        if row['task']=='alpaca_eval':observations.append('Candidate only; no preference or length-controlled score available.')
        packet.append(dict(**row,selection_seed=0,selection_reason=reason,human_review_status='pending',human_notes=None,human_correct=None,parser_bug=None,format_issue=None,safety_concern=None,initial_analysis={'author':'AI analysis / rule-based preliminary observations','observations':observations,'not_human_review':True}))
    write_new(directory/'review_packet.jsonl',packet,jsonl=True)
    print(json.dumps({'review_count':len(packet),'tasks':{t:sum(r['task']==t for r in packet) for t in TASKS},'human_review_status':'pending'},indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-dir',type=Path,required=True)
    build(parser.parse_args().run_dir)
