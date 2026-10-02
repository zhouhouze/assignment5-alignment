"""Pinned Supplement baseline preparation, immutable raw capture and rescoring.

No training path. Pure loaders/scorers operate on Python records; vLLM receives
lists of token IDs and returns one completion per input. No chat template.
"""
import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import importlib.metadata
import json
import csv
import os
from pathlib import Path
import random
import statistics
import subprocess
import threading
import time

from cs336_alignment.supplement_metrics import parse_gsm8k_response, parse_mmlu_response

ROOT = Path(__file__).resolve().parents[1]
TASKS = ('mmlu', 'gsm8k', 'alpaca_eval', 'simple_safety_tests')
CONFIG = ROOT/'configs/qwen_baseline_gate.json'
PROMPTS = ROOT/'cs336_alignment/prompts_safety'


def sha(path):
    with Path(path).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def text_sha(value):
    return hashlib.sha256(value.encode()).hexdigest()


def write_new(path, value, jsonl=False):
    """Exclusive creation plus fsync. Never overwrite a prior raw/derived artifact."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    text = ''.join(json.dumps(row, ensure_ascii=False)+'\n' for row in value) if jsonl else json.dumps(value, ensure_ascii=False, indent=2)+'\n'
    with path.open('x') as f:
        f.write(text)
        f.flush()
        os.fsync(f.fileno())
    return sha(path)


def load_tasks(root=ROOT):
    """Load unmodified official benchmark files, stable source-relative IDs."""
    rows = {task: [] for task in TASKS}
    paths = []
    for path in sorted((root/'data/mmlu/test').glob('*.csv')):
        paths.append(path)
        subject = path.stem.removesuffix('_test')
        with path.open() as f:
            for index, values in enumerate(csv.reader(f)):
                if len(values) != 6 or values[-1] not in 'ABCD':
                    raise ValueError(f'Invalid MMLU row: {path}:{index}')
                rows['mmlu'].append(dict(example_id=f'{subject}:{index}', raw_input=dict(subject=subject, question=values[0], options=values[1:5]), ground_truth=values[5], dataset_split='test', dataset='mmlu'))
    path = root/'data/gsm8k/test.jsonl'
    paths.append(path)
    with path.open() as f:
        for index, line in enumerate(f):
            value = json.loads(line)
            gold = value['answer'].rsplit('####', 1)
            if len(gold) != 2:
                raise ValueError('Missing GSM8K gold delimiter')
            answer = parse_gsm8k_response(gold[1])
            if answer is None:
                raise ValueError('Invalid GSM8K gold numeral')
            rows['gsm8k'].append(dict(example_id=str(index), raw_input=value, ground_truth=answer, dataset_split='test', dataset='gsm8k'))
    path = root/'data/alpaca_eval/alpaca_eval_gpt4_turbo.json'
    paths.append(path)
    for index, value in enumerate(json.loads(path.read_text())):
        rows['alpaca_eval'].append(dict(example_id=str(index), raw_input=value, ground_truth=None, dataset_split='eval', dataset=value['dataset']))
    path = root/'data/simple_safety_tests/simple_safety_tests.csv'
    paths.append(path)
    with path.open() as f:
        for value in csv.DictReader(f):
            rows['simple_safety_tests'].append(dict(example_id=value['id'], raw_input=value, ground_truth=None, dataset_split='test', dataset='simple_safety_tests'))
    expected = dict(zip(TASKS, [14042, 1319, 805, 100]))
    for task, examples in rows.items():
        if len(examples) != expected[task] or len({x['example_id'] for x in examples}) != len(examples):
            raise ValueError(f'Dataset count/ID mismatch: {task}')
    return rows, {str(p.relative_to(root)): sha(p) for p in paths}


def select(rows, stage, seed):
    rng = random.Random(seed)
    selected = {}
    for task in TASKS:
        examples = rows[task]
        if task == 'mmlu':
            groups = defaultdict(list)
            for x in examples:
                groups[x['raw_input']['subject']].append(x)
            chosen = [rng.choice(groups[s]) for s in rng.sample(sorted(groups), 20)]
        elif task == 'simple_safety_tests':
            groups = defaultdict(list)
            for x in examples:
                groups[(x['raw_input']['harm_area'], x['raw_input']['category'])].append(x)
            chosen = [x for key in sorted(groups) for x in rng.sample(groups[key], 2)]
        else:
            chosen = rng.sample(examples, 20)
        selected[task] = sorted(chosen, key=lambda x: x['example_id'])
        if stage != 'PILOT':
            selected[task] = selected[task][:1]
    return selected


def render(task, example):
    template = (PROMPTS/f'{task}_zero_shot.prompt').read_text()
    value = example['raw_input']
    if task == 'mmlu':
        instruction = template.format(subject=value['subject'].replace('_', ' '), question=value['question'], options=value['options'])
    elif task == 'gsm8k':
        instruction = template.format(question=value['question'])
    else:
        instruction = template.format(instruction=value['instruction'] if task == 'alpaca_eval' else value['prompts_final'])
    return (PROMPTS/'zero_shot_system_prompt.prompt').read_text().format(instruction=instruction)


def score(row):
    """Unchanged Supplement parsers; Decimal comparison only normalizes numerals."""
    task = row['task']
    if task == 'mmlu':
        answer = parse_mmlu_response(row['raw_response'])
        correct = answer is not None and answer == row['ground_truth']
    elif task == 'gsm8k':
        answer = parse_gsm8k_response(row['raw_response'])
        correct = answer is not None and Decimal(answer) == Decimal(row['ground_truth'])
    else:
        return dict(parsed_answer=None, correct=None, parse_failure=None, evaluation_status='pending_judge')
    return dict(parsed_answer=answer, correct=correct, parse_failure=answer is None, evaluation_status='scored')


def environment():
    packages = {}
    for name in ('torch', 'transformers', 'vllm', 'flash-attn', 'tokenizers'):
        try:
            packages[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            packages[name] = None
    import platform
    import torch
    gpu = subprocess.run(['nvidia-smi', '--query-gpu=name,memory.total,driver_version', '--format=csv,noheader'], capture_output=True, text=True) if __import__('shutil').which('nvidia-smi') else None
    return dict(python=platform.python_version(), platform=platform.platform(), packages=packages, cuda_runtime=torch.version.cuda, gpu=gpu.stdout.strip() if gpu else None)


def prepare(directory, stage):
    """CPU only: pin source/dataset/prompt hashes and serialize selected inputs."""
    from transformers import AutoTokenizer
    config = json.loads(CONFIG.read_text())
    tokenizer = AutoTokenizer.from_pretrained(ROOT/config['tokenizer_path'], local_files_only=True)
    rows, datasets = load_tasks()
    selected = select(rows, stage, config['seed'])
    requests = []
    for task in TASKS:
        for index, value in enumerate(selected[task]):
            prompt = render(task, value)
            ids = tokenizer.encode(prompt, add_special_tokens=False)
            if len(ids)+config['sampling']['max_tokens'] > config['engine']['max_model_len']:
                raise ValueError(f'Prompt too long: {task}/{value["example_id"]}')
            requests.append(dict(**value, task=task, request_index=index, formatted_prompt=prompt, prompt_sha256=text_sha(prompt), prompt_token_ids=ids, prompt_token_count=len(ids)))
    directory.mkdir(parents=True, exist_ok=False)
    selected_hash = write_new(directory/'selected_examples.json', requests)
    sources = {str(p.relative_to(ROOT)): sha(p) for p in [CONFIG, Path(__file__), ROOT/'cs336_alignment/supplement_metrics.py']}
    prompts = {str(p.relative_to(ROOT)): sha(p) for p in [PROMPTS/'zero_shot_system_prompt.prompt']+[PROMPTS/f'{task}_zero_shot.prompt' for task in TASKS]}
    manifest = dict(schema_version='1.0', experiment_id='SUP-QWEN-01', run_id=directory.name, experiment_type='PA5 Supplement Adapted Reproduction', stage=stage, experiment_stage=stage if stage != 'CPU_DRY_RUN' else None, record_type='dry_run_preparation' if stage == 'CPU_DRY_RUN' else 'generation_run', directly_comparable_to_official=False, created_at=datetime.now(timezone.utc).isoformat(), configuration=config, model=config['model'], model_revision=config['model_revision'], tokenizer_revision=config['tokenizer_revision'], git_commit=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(), git_dirty=bool(subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip()), sources=sources, dataset_hashes=datasets, prompt_hashes=prompts, selected_examples_sha256=selected_hash, hardware_software=environment(), seed=config['seed'], sampling=config['sampling'], engine=config['engine'], training_params=None, selection='seed0; MMLU20 distinct subjects; Safety2 per harm_area/category; others random20. Smoke takes first selected per task.', official_policy_model='meta-llama/Meta-Llama-3.1-8B', adapted_policy_model=config['model'], official_judge_model='meta-llama/Llama-3.3-70B-Instruct', adapted_judge_model='Qwen/Qwen2.5-72B-Instruct', adaptation_reason='Replace gated Llama models while preserving PA5 Supplement post-training structure.', judge_executed=False, sft_data_used=False)
    manifest_hash = write_new(directory/'manifest.json', manifest)
    (directory/'manifest.sha256').write_text(manifest_hash+'\n')
    if stage == 'CPU_DRY_RUN':
        probes = {task: score(dict(task=task, raw_response='', ground_truth='0' if task=='gsm8k' else 'A')) for task in TASKS}
        write_new(directory/'dry-run.json', dict(status='PASS', model_loaded=False, generation_executed=False, request_count=len(requests), parser_empty_probes=probes))
    validate(directory)
    return manifest


def validate(directory):
    """Fail closed on drift, corruption, IDs or ambiguous pending generation."""
    if sha(directory/'manifest.json') != (directory/'manifest.sha256').read_text().strip():
        raise ValueError('Manifest hash changed')
    m = json.loads((directory/'manifest.json').read_text())
    if sha(directory/'selected_examples.json') != m['selected_examples_sha256']:
        raise ValueError('Selected inputs changed')
    for section in ('sources', 'dataset_hashes', 'prompt_hashes'):
        for path, digest in m[section].items():
            if sha(ROOT/path) != digest:
                raise ValueError(f'Source/prompt/dataset hash changed: {path}')
    if (directory/'pending.json').exists() or (directory/'failed.json').exists():
        raise ValueError('Prior infra failure or unresolved pending generation; no automatic retry')
    requests = json.loads((directory/'selected_examples.json').read_text())
    expected = {f'{x["task"]}-{x["request_index"]:04d}.jsonl': x for x in requests}
    raw = []
    for path in sorted((directory/'raw').glob('*')):
        if path.suffix == '.sha256':
            if not path.with_suffix('').exists():
                raise ValueError('Orphan checksum')
            continue
        if path.name not in expected:
            raise ValueError('Unexpected raw filename')
        data = path.read_bytes()
        checksum = path.with_suffix(path.suffix+'.sha256')
        if not checksum.exists() or sha(path) != checksum.read_text().strip():
            raise ValueError('Raw hash missing/mismatch')
        if not data.endswith(b'\n') or len(data.splitlines()) != 1:
            raise ValueError('Malformed raw JSONL')
        row = json.loads(data)
        exp = expected[path.name]
        for key in ('example_id', 'task', 'request_index', 'formatted_prompt', 'prompt_sha256', 'prompt_token_count', 'ground_truth'):
            if row[key] != exp[key]:
                raise ValueError(f'Raw identity/prompt mismatch: {key}')
        if row['manifest_sha256'] != sha(directory/'manifest.json') or not isinstance(row['raw_response'], str):
            raise ValueError('Raw provenance/schema mismatch')
        raw.append(row)
    return m, requests, raw


class VramMonitor:
    """Sample total device memory, including vLLM worker process, every 250 ms."""
    def __init__(self):
        self.stop = threading.Event()
        self.samples = []
        self.thread = threading.Thread(target=self.poll, daemon=True)
    def poll(self):
        while not self.stop.is_set():
            p = subprocess.run(['nvidia-smi','--query-gpu=memory.used','--format=csv,noheader,nounits'],capture_output=True,text=True)
            if p.returncode == 0:
                self.samples.append(dict(time=time.time(), used_mib=int(p.stdout.strip())))
            self.stop.wait(.25)
    def start(self):
        self.thread.start()
    def finish(self):
        self.stop.set()
        self.thread.join()
        return dict(method='sampled total device memory; 250ms polling, may miss short peaks', peak_mib=max((s['used_mib'] for s in self.samples),default=None), samples=self.samples)


def run(directory, model_path):
    m, requests, previous = validate(directory)
    if m['stage'] not in ('SMOKE', 'PILOT'):
        raise ValueError('Only authorized SMOKE/PILOT, never FULL')
    done = {(x['task'], x['request_index']) for x in previous}
    if len(done) == len(requests):
        print('Already completed; raw not resampled')
        return
    weights = json.loads((model_path/'weights-manifest.json').read_text())
    if weights['revision'] != m['model_revision'] or weights['model'] != m['model']:
        raise ValueError('Model weight provenance mismatch')
    for name, item in weights['files'].items():
        if (model_path/name).stat().st_size != item['bytes'] or sha(model_path/name) != item['sha256']:
            raise ValueError('Weight integrity mismatch')
    attempt = len(list(directory.glob("runtime-*.json")))
    monitor = VramMonitor()
    monitor.start()
    started = time.perf_counter()
    try:
        from vllm import LLM, SamplingParams
        config = m['configuration']
        llm = LLM(model=str(model_path), tokenizer=str(ROOT/config['tokenizer_path']), revision=m['model_revision'], tokenizer_revision=m['tokenizer_revision'], **config['engine'])
        load_seconds = time.perf_counter()-started
        sampling = SamplingParams(**config['sampling'])
        write_new(directory/f'runtime-{attempt:03d}.json',dict(load_seconds=load_seconds, load_includes_vllm_import=True, sampling_effective=str(sampling), engine_effective=str(llm.llm_engine.vllm_config), weights_manifest=weights, device_memory_before_generation=monitor.samples[-1] if monitor.samples else None))
        for task in TASKS:
            pending = [x for x in requests if x['task']==task and (task,x['request_index']) not in done]
            batch_size = config['batch_size']
            for offset in range(0,len(pending),batch_size):
                batch = pending[offset:offset+batch_size]
                validate(directory)
                write_new(directory/'pending.json',dict(task=task, request_indices=[x['request_index'] for x in batch]))
                tick = time.perf_counter()
                outputs = llm.generate([{'prompt_token_ids': x['prompt_token_ids']} for x in batch], sampling, use_tqdm=False)
                elapsed = time.perf_counter()-tick
                if len(outputs) != len(batch):
                    raise ValueError('Generation returned count mismatch')
                for inp,out in zip(batch,outputs,strict=True):
                    if list(out.prompt_token_ids) != inp['prompt_token_ids'] or len(out.outputs)!=1:
                        raise ValueError('Returned prompt identity/count mismatch')
                    value = out.outputs[0]
                    row = {k:v for k,v in inp.items() if k!='prompt_token_ids'}
                    row.update(schema_version='1.0', experiment_id='SUP-QWEN-01', run_id=m['run_id'], stage=m['stage'], model=m['model'], model_revision=m['model_revision'], tokenizer_revision=m['tokenizer_revision'], manifest_sha256=sha(directory/'manifest.json'), raw_response=value.text, response_token_count=len(value.token_ids), response_token_ids=list(value.token_ids), finish_reason=value.finish_reason, stop_reason=value.stop_reason, generation_config=m['sampling'], batch_id=f'{task}-{batch[0]["request_index"]:04d}', batch_seconds=elapsed, latency_seconds=None, latency_note='Per-request latency unavailable; batch wall time measured', generation_status='completed', directly_comparable_to_official=False)
                    path = directory/'raw'/f'{task}-{inp["request_index"]:04d}.jsonl'
                    digest = write_new(path,[row],jsonl=True)
                    with path.with_suffix(path.suffix+'.sha256').open('x') as f:
                        f.write(digest+'\n'); f.flush(); os.fsync(f.fileno())
                (directory/'pending.json').unlink()
                print(f'{task}: {min(offset+batch_size,len(pending))}/{len(pending)} saved',flush=True)
        _,_,all_raw = validate(directory)
        if len(all_raw) != len(requests):
            raise ValueError('Final output count mismatch')
        write_new(directory/'generation-complete.json',dict(status='completed', count=len(all_raw), elapsed_seconds=time.perf_counter()-started))
    except BaseException as exc:
        write_new(directory/'failed.json',dict(status='failed', error_type=type(exc).__name__, error=str(exc), next_action='hard stop; retain partial raw; do not retry/resample'))
        raise
    finally:
        write_new(directory/f'vram-{attempt:03d}.json',monitor.finish())


def summarize(directory, version):
    m, requests, raw = validate(directory)
    if len(raw) != len(requests):
        raise ValueError('Cannot report partial generation as complete')
    metrics = dict(stage=m['stage'], directly_comparable_to_official=False, results={}, judge_executed=False)
    for task in TASKS:
        examples = sorted([x for x in raw if x['task']==task],key=lambda x:x['request_index'])
        scored = [{**row, **score(row), 'parser_sha256':m['sources']['cs336_alignment/supplement_metrics.py']} for row in examples]
        write_new(directory/'scored'/version/f'{task}.scored.jsonl',scored,jsonl=True)
        lengths = sorted(x['response_token_count'] for x in examples)
        batches = {x['batch_id']:x['batch_seconds'] for x in examples}
        seconds = sum(batches.values())
        result = dict(n=len(examples), generation_success=len(examples), empty_count=sum(not x['raw_response'] for x in examples), length_termination_count=sum(x['finish_reason']=='length' for x in examples), average_response_tokens=statistics.mean(lengths), median_response_tokens=statistics.median(lengths), p95_response_tokens=lengths[__import__('math').ceil(.95*len(lengths))-1], finish_reasons=dict(Counter(x['finish_reason'] for x in examples)), generation_seconds=seconds, examples_per_second=len(examples)/seconds, output_tokens_per_second=sum(lengths)/seconds, timing_scope='sum task batch wall times; excludes model load and disk writes')
        if task in ('mmlu','gsm8k'):
            result.update(accuracy=sum(x['correct'] for x in scored)/len(scored), parse_failures=sum(x['parse_failure'] for x in scored), parse_failure_rate=sum(x['parse_failure'] for x in scored)/len(scored))
        else:
            result['evaluation_status']='pending_judge'
        metrics['results'][task]=result
        if task=='alpaca_eval':
            write_new(directory/'exports'/version/'alpaca_eval.json',[dict(instruction=x['raw_input']['instruction'],output=x['raw_response'],generator='qwen2.5-7b-base-pa5-supplement',dataset=x['dataset']) for x in examples])
        if task=='simple_safety_tests':
            write_new(directory/'exports'/version/'simple_safety_tests.jsonl',[dict(prompts_final=x['raw_input']['prompts_final'],output=x['raw_response'],example_id=x['example_id'],run_id=x['run_id'],model=x['model'],model_revision=x['model_revision']) for x in examples],jsonl=True)
    write_new(directory/f'metrics-{version}.json',metrics)
    return metrics


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('action',choices=['prepare','validate','run','score'])
    p.add_argument('--run-dir',type=Path,required=True)
    p.add_argument('--stage',choices=['CPU_DRY_RUN','SMOKE','PILOT'])
    p.add_argument('--model-path',type=Path)
    p.add_argument('--score-version',default='v1')
    args=p.parse_args()
    if args.action=='prepare':
        if args.stage is None:p.error('--stage required')
        prepare(args.run_dir,args.stage)
    elif args.action=='validate':
        m,req,raw=validate(args.run_dir);print(json.dumps(dict(run_id=m['run_id'],expected=len(req),saved=len(raw))))
    elif args.action=='run':
        if args.model_path is None:p.error('--model-path required')
        run(args.run_dir,args.model_path)
    else:
        print(json.dumps(summarize(args.run_dir,args.score_version),indent=2))


if __name__=='__main__':
    main()
