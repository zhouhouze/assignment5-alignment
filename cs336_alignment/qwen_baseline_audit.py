"""Independent disk-only metric recomputation; no runner/model imports.

This deliberately shares only the frozen parsers and sealed-file reader with
the runner, not its score/aggregation functions or in-memory generation state.
"""
from collections import Counter
from decimal import Decimal
import math
import statistics

from cs336_alignment.qwen_baseline_storage import read_raw
from cs336_alignment.supplement_metrics import parse_gsm8k_response, parse_mmlu_response


def recompute(directory):
    tasks = {}
    seen = set()
    for path in sorted((directory/'raw').glob('*.jsonl')):
        r = read_raw(path)
        identity = (r['task'], r['example_id'])
        if identity in seen:
            raise ValueError(f'Duplicate ID in independent audit: {path}:1')
        seen.add(identity)
        tasks.setdefault(r['task'], []).append(r)
    result = {}
    for task, rows in tasks.items():
        n = len(rows)
        tokens = [r['response_token_count'] for r in rows]
        batches = {}
        correct = failures = empty = spaces = 0
        for r in rows:
            empty += r['raw_response'] == ''
            spaces += r['raw_response'] != '' and r['raw_response'].strip() == ''
            key = (r['run_id'], r['attempt_id'], task, r['batch_id'])
            if key in batches and batches[key] != r['batch_seconds']:
                raise ValueError('Conflicting timing in independent audit')
            batches[key] = r['batch_seconds']
            if task == 'mmlu':
                answer = parse_mmlu_response(r['raw_response'])
                failures += answer is None
                correct += answer is not None and answer == r['ground_truth']
            elif task == 'gsm8k':
                answer = parse_gsm8k_response(r['raw_response'])
                failures += answer is None
                correct += answer is not None and Decimal(answer) == Decimal(r['ground_truth'])
        seconds = math.fsum(batches.values())
        values = dict(n=n, expected_count=n, completed_count=n, empty_count=empty, whitespace_only_count=spaces,
            blank_rate=(empty+spaces)/n, length_termination_count=len([r for r in rows if r['finish_reason'] == 'length']),
            average_response_tokens=sum(tokens)/n, median_response_tokens=statistics.median(tokens),
            p95_response_tokens=sorted(tokens)[math.ceil(n*.95)-1], finish_reasons=dict(Counter(r['finish_reason'] for r in rows)),
            generation_seconds=seconds, examples_per_second=n/seconds if seconds else None,
            output_tokens_per_second=sum(tokens)/seconds if seconds else None,
            timing_scope='sum unique recorded batch wall times; excludes load/write and lost unpersisted batches; not per-request latency',
            metric_status='MOCK_TEST_ONLY' if rows[0]['mode'] == 'MOCK_TEST_ONLY' else 'FULL',
            judge_execution_status='NOT_RUN', lc_validation_status='NOT_VALIDATED', confidence_interval=None)
        if task in ('mmlu', 'gsm8k'):
            values.update(correct_count=correct, incorrect_count=n-correct, accuracy=correct/n,
                accuracy_numerator=correct, accuracy_denominator=n, accuracy_unit='fraction',
                parse_failure_count=failures, parse_failure_rate=failures/n)
        else:
            values['evaluation_status'] = 'pending_judge'
        result[task] = values
    return result
