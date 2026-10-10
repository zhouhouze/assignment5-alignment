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
import math
import os
from pathlib import Path
import random
import statistics
import subprocess
import threading
import time
import uuid
from types import SimpleNamespace

from cs336_alignment.supplement_metrics import parse_gsm8k_response, parse_mmlu_response
from cs336_alignment import qwen_baseline_storage as storage

ROOT = Path(__file__).resolve().parents[1]
TASKS = ('mmlu', 'gsm8k', 'alpaca_eval', 'simple_safety_tests')
CONFIG = ROOT/'configs/qwen_baseline_gate.json'
PROMPTS = ROOT/'cs336_alignment/prompts_safety'
PROTOCOL_COMMIT = '09c18e7d4e966264f994f8ce2fc5deb1b385a937'
PROTOCOL = 'notes/experiments/SUP-QWEN-evaluation/evaluation-protocol-v1.md'
DECISIONS = 'notes/experiments/SUP-QWEN-evaluation/evaluation-decision-log.md'
PILOT = 'artifacts/pa5-supplement-qwen/baseline/pilot/20261003-pilot-03/manifest.json'
FULL_COUNTS = dict(zip(TASKS, [14042, 1319, 805, 100]))


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
    """FULL preserves source order; legacy SMOKE/PILOT retain seeded selection."""
    stage = stage.upper()
    if stage == 'FULL':
        return {task: list(rows[task]) for task in TASKS}
    if stage not in ('CPU_DRY_RUN', 'SMOKE', 'PILOT'):
        raise ValueError(f'Unknown stage: {stage}')
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


def prepare(directory, stage, **full_options):
    """CPU only: pin source/dataset/prompt hashes and serialize selected inputs."""
    stage = stage.upper()
    if stage == 'FULL':
        return prepare_full(directory, **full_options)
    if full_options:
        raise ValueError('Full options require --stage full')
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
    if json.loads((directory/'manifest.json').read_text()).get('schema_version') == '2.0':
        return validate_full(directory)
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


def run(directory, model_path=None, **full_options):
    if json.loads((directory/'manifest.json').read_text()).get('schema_version') == '2.0':
        return run_full(directory, model_path, **full_options)
    if full_options:
        raise ValueError('Full options cannot be used with legacy runs')
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
    if json.loads((directory/'manifest.json').read_text()).get('schema_version') == '2.0':
        return finalize_full(directory, version)
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


def frozen_bytes(path):
    return subprocess.check_output(['git', 'show', f'{PROTOCOL_COMMIT}:{path}'], cwd=ROOT)


def git_state():
    return dict(run_code_commit=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
                git_dirty=bool(subprocess.check_output(['git', 'status', '--porcelain'], cwd=ROOT, text=True).strip()))


def now():
    return datetime.now(timezone.utc).isoformat()


def full_pins(config, dataset_root):
    """Check current inputs against P0 Git objects, including relocated assets."""
    fixed = json.loads(frozen_bytes('configs/qwen_baseline_gate.json'))
    for key in fixed:
        if key != 'tokenizer_path' and config.get(key) != fixed[key]:
            raise ValueError(f'Frozen configuration drift: {key}')
    if set(config) != set(fixed):
        raise ValueError('Unexpected configuration keys')
    tracked = [PROTOCOL, DECISIONS, 'notes/experiments/SUP-QWEN-evaluation/evaluation-metrics-spec.md',
               'cs336_alignment/supplement_metrics.py']
    tracked += [str(p.relative_to(ROOT)) for p in sorted(PROMPTS.glob('*.prompt'))]
    hashes = {}
    for relative in tracked:
        expected = hashlib.sha256(frozen_bytes(relative)).hexdigest()
        if sha(ROOT/relative) != expected:
            raise ValueError(f'Frozen protocol/prompt/parser drift: {relative}')
        hashes[relative] = expected
    datasets = json.loads(frozen_bytes(PILOT))['dataset_hashes']
    for relative, expected in datasets.items():
        if sha(dataset_root/relative) != expected:
            raise ValueError(f'Dataset drift: {relative}')
    inventory = json.loads(frozen_bytes('artifacts/pa5-supplement-qwen/preflight/20261002/download-inventory.json'))
    assets = {}
    for item in inventory:
        if item['repo'] == config['model']:
            path = ROOT/config['tokenizer_path']/item['file']
            if sha(path) != item['sha256'] or path.stat().st_size != item['bytes']:
                raise ValueError(f'Tokenizer/config asset drift: {item["file"]}')
            assets[item['file']] = item['sha256']
    return dict(protocol_id='SUP-QWEN-EVAL-v1', protocol_git_commit=PROTOCOL_COMMIT,
                protocol_sha256=hashes[PROTOCOL], decision_log_sha256=hashes[DECISIONS],
                frozen_files=hashes, dataset_hashes=datasets, tokenizer_hashes=assets)


def input_inventory(requests):
    result = {}
    for task in TASKS:
        rows = [r for r in requests if r['task'] == task]
        if rows:
            result[task] = dict(expected_count=len(rows),
                ordered_ids_sha256=text_sha(''.join(r['example_id']+'\n' for r in rows)),
                rendered_inventory_sha256=text_sha(''.join(f'{task}\t{r["example_id"]}\t{r["prompt_sha256"]}\t{r["prompt_token_count"]}\n' for r in rows)),
                max_prompt_tokens=max(r['prompt_token_count'] for r in rows))
    return result


def prepare_full(directory, *, tasks=TASKS, run_id=None, dataset_root=ROOT, config_path=CONFIG, mock=False, dry_run=False):
    """CPU input preflight for FULL. Only tokenizer loading; never loads weights."""
    from transformers import AutoTokenizer
    directory, dataset_root, config_path = map(lambda p: Path(p).resolve(), (directory, dataset_root, config_path))
    if mock and dry_run:
        raise ValueError('Choose mock or dry-run')
    mode = 'MOCK_TEST_ONLY' if mock else 'CPU_DRY_RUN' if dry_run else 'REAL'
    formal = (ROOT/'artifacts/pa5-supplement-qwen/baseline/full').resolve()
    if mode != 'REAL' and (directory == formal or formal in directory.parents):
        raise ValueError('Mock/dry-run cannot use the formal Full results directory')
    if set(tasks)-set(TASKS):
        raise ValueError('Unknown task selection')
    tasks = tuple(task for task in TASKS if task in tasks)
    if not tasks:
        raise ValueError('No valid tasks selected')
    config = json.loads(config_path.read_text())
    pins = full_pins(config, dataset_root)
    rows, datasets = load_tasks(dataset_root)
    if datasets != pins['dataset_hashes']:
        raise ValueError('Dataset file inventory drift')
    selected = select(rows, 'FULL', config['seed'])
    tokenizer = AutoTokenizer.from_pretrained(ROOT/config['tokenizer_path'], local_files_only=True)
    requests = []
    for task in tasks:
        for index, value in enumerate(selected[task]):
            prompt = render(task, value)
            ids = tokenizer.encode(prompt, add_special_tokens=False)
            if len(ids)+config['sampling']['max_tokens'] > config['engine']['max_model_len']:
                raise ValueError(f'Prompt too long: {task}/{value["example_id"]}')
            requests.append(dict(**value, task=task, request_index=index, formatted_prompt=prompt,
                prompt_sha256=text_sha(prompt), prompt_token_ids=ids, prompt_token_count=len(ids)))
    directory.mkdir(parents=True, exist_ok=False)
    for name in ('raw', 'attempts', 'finalized'):
        (directory/name).mkdir()
    storage.atomic_json(directory/'selected_examples.json', requests)
    sources = {str(p.relative_to(ROOT)): sha(p) for p in (Path(__file__), ROOT/'cs336_alignment/qwen_baseline_storage.py', ROOT/'cs336_alignment/qwen_baseline_audit.py')}
    manifest = dict(schema_version='2.0', experiment_id='SUP-QWEN-01', run_id=run_id or directory.name,
        experiment_type='PA5 Supplement Adapted Reproduction', stage='FULL', mode=mode,
        evaluation_protocol_id='SUP-QWEN-EVAL-v1', directly_comparable_to_official=False,
        created_at=now(), status='PREPARED', run_code_commit=None, start_time=None, end_time=None,
        lifecycle_note='Actual inference commit/start/end/counts in immutable attempts and finalized/version/manifest-final.json',
        prepare_git=git_state(), configuration=config,
        config_path=str(config_path.relative_to(ROOT)) if config_path.is_relative_to(ROOT) else str(config_path), config_sha256=sha(config_path),
        model_name=config['model'], model_revision=config['model_revision'], tokenizer_revision=config['tokenizer_revision'],
        dataset_root=str(dataset_root.relative_to(ROOT)) if dataset_root.is_relative_to(ROOT) else str(dataset_root),
        dataset_name=list(tasks), dataset_split={t: selected[t][0]['dataset_split'] for t in tasks},
        dataset_sha256=storage.digest(datasets), tasks=list(tasks), selection='all; original source order',
        scope='ALL_FOUR_TASKS' if tasks == TASKS else 'TASK_SUBSET', expected_count=len(requests), completed_count=0,
        inventory=input_inventory(requests), selected_examples_sha256=sha(directory/'selected_examples.json'),
        sources=sources, **pins, hardware_software=environment(), judge_executed=False, training_params=None,
        recovery_policy='P1A explicit resume: committed records exactly once; uncommitted inference may repeat; preserve attempt evidence')
    storage.atomic_json(directory/'manifest.json', manifest)
    storage.atomic_text(directory/'manifest.sha256', sha(directory/'manifest.json')+'\n')
    storage.atomic_json(directory/'progress.json', dict(status='PREPARED', completed_count=0, expected_count=len(requests), mode=mode))
    validate_full(directory)
    storage.atomic_json(directory/'input-check.json', dict(status='PASS', mode=mode, generation_executed=False,
        model_loaded=False, verified_count=len(requests), inventory=manifest['inventory']))
    return manifest


def raw_name(row):
    return f'{row["task"]}-{row["request_index"]:05d}.jsonl'


def validate_full(directory):
    """O(inputs + committed records) audit; called at boundaries, not every batch.

    Pending attempt evidence does not authorize retries. run_full requires the
    explicit resume flag and records the uncertainty before generating missing IDs.
    """
    directory = Path(directory)
    manifest_sha = sha(directory/'manifest.json')
    if manifest_sha != (directory/'manifest.sha256').read_text().strip():
        raise ValueError('Manifest hash changed')
    m = json.loads((directory/'manifest.json').read_text())
    config_path = ROOT/m['config_path']
    config = json.loads(config_path.read_text())
    if sha(config_path) != m['config_sha256'] or config != m['configuration']:
        raise ValueError('Configuration drift')
    if m['evaluation_protocol_id'] != 'SUP-QWEN-EVAL-v1':
        raise ValueError('Evaluation protocol drift')
    if m['model_name'] != config['model'] or m['model_revision'] != config['model_revision'] or m['tokenizer_revision'] != config['tokenizer_revision']:
        raise ValueError('Model/tokenizer revision drift')
    pins = full_pins(config, ROOT/m['dataset_root'])
    if any(m.get(key) != value for key, value in pins.items()):
        raise ValueError('Protocol/model/tokenizer/dataset/prompt drift')
    for relative, expected in m['sources'].items():
        if sha(ROOT/relative) != expected:
            raise ValueError(f'Runner source drift: {relative}')
    if sha(directory/'selected_examples.json') != m['selected_examples_sha256']:
        raise ValueError('Selected inputs changed')
    requests = json.loads((directory/'selected_examples.json').read_text())
    expected = {(r['task'], r['example_id']): r for r in requests}
    if len(expected) != len(requests) or input_inventory(requests) != m['inventory']:
        raise ValueError('Selected ID/inventory mismatch')
    if len(requests) != m['expected_count'] or any(len([r for r in requests if r['task'] == t]) != FULL_COUNTS[t] for t in m['tasks']):
        raise ValueError('Full input count mismatch')
    raw, seen = [], set()
    required = {'schema_version', 'experiment_id', 'run_id', 'stage', 'mode', 'task', 'example_id', 'dataset_split',
        'model_name', 'model_revision', 'tokenizer_revision', 'formatted_prompt', 'prompt_sha256', 'ground_truth',
        'raw_input', 'raw_response', 'finish_reason', 'stop_reason', 'prompt_token_count', 'response_token_count',
        'response_token_ids', 'generation_config', 'request_index', 'attempt_id', 'batch_id', 'batch_seconds',
        'latency_seconds', 'timing_scope', 'manifest_sha256', 'run_code_commit', 'generation_status', 'directly_comparable_to_official'}
    attempts = {p.name: json.loads((p/'start.json').read_text()) for p in sorted((directory/'attempts').iterdir()) if p.is_dir() and (p/'start.json').exists()}
    for path in sorted((directory/'raw').iterdir()):
        if path.name.startswith('.pending-'):
            continue  # uncommitted write debris retained and inventoried at explicit resume
        row = storage.read_raw(path)
        missing = required-row.keys()
        if missing:
            raise ValueError(f'{path}:1: missing schema fields: {sorted(missing)}')
        identity = (row['task'], row['example_id'])
        if identity in seen:
            raise ValueError(f'{path}:1: duplicate ID {identity}')
        seen.add(identity)
        if identity not in expected:
            raise ValueError(f'{path}:1: unexpected ID {identity}')
        inp = expected[identity]
        if path.name != raw_name(inp):
            raise ValueError(f'{path}:1: unexpected raw filename')
        for key, value in inp.items():
            if key != 'prompt_token_ids' and row.get(key) != value:
                raise ValueError(f'{path}:1: input identity mismatch: {key}')
        fixed = dict(schema_version='2.0', experiment_id=m['experiment_id'], run_id=m['run_id'], stage='FULL', mode=m['mode'],
            model_name=m['model_name'], model_revision=m['model_revision'], tokenizer_revision=m['tokenizer_revision'],
            manifest_sha256=manifest_sha, generation_config=config['sampling'], generation_status='completed',
            directly_comparable_to_official=False, latency_seconds=None, timing_scope='batch wall seconds; excludes load/write; no per-request latency')
        if any(row.get(k) != v for k, v in fixed.items()):
            raise ValueError(f'{path}:1: raw provenance/config mismatch')
        if not isinstance(row['raw_response'], str) or not isinstance(row['response_token_ids'], list):
            raise ValueError(f'{path}:1: invalid response schema')
        if type(row['response_token_count']) is not int or row['response_token_count'] != len(row['response_token_ids']) or not all(type(t) is int and t >= 0 for t in row['response_token_ids']):
            raise ValueError(f'{path}:1: invalid token count/IDs')
        if row['response_token_count'] > config['sampling']['max_tokens'] or row['finish_reason'] not in ('stop', 'length'):
            raise ValueError(f'{path}:1: unfinished/invalid generation')
        seconds = row['batch_seconds']
        if type(seconds) not in (float, int) or not math.isfinite(seconds) or seconds < 0:
            raise ValueError(f'{path}:1: invalid timing')
        attempt = attempts.get(row['attempt_id'])
        intent_path = directory/'attempts'/row['attempt_id']/f'{row["batch_id"]}.intent.json'
        if attempt is None or row['run_code_commit'] != attempt['run_code_commit'] or not intent_path.exists():
            raise ValueError(f'{path}:1: missing attempt/batch provenance')
        intent = json.loads(intent_path.read_text())
        if list(identity) not in intent['ids']:
            raise ValueError(f'{path}:1: batch identity mismatch')
        raw.append(row)
    verify_finalized(directory)
    return m, requests, raw


def verify_finalized(directory):
    """Verify published bundles and their immutable input/raw/attempt references."""
    for bundle in sorted((directory/'finalized').iterdir()):
        if not bundle.is_dir():
            raise ValueError(f'Unexpected final artifact: {bundle}')
        expected = {}
        for line in (bundle/'SHA256SUMS').read_text().splitlines():
            value, relative = line.split('  ', 1)
            if Path(relative).is_absolute() or '..' in Path(relative).parts or relative in expected:
                raise ValueError('Invalid final checksum inventory')
            expected[relative] = value
        actual = {str(p.relative_to(bundle)) for p in bundle.rglob('*') if p.is_file() and p.name != 'SHA256SUMS'}
        if set(expected) != actual or not {'manifest-final.json', 'metrics.json', 'checks/source-inventory.json', 'checks/integrity-report.json', 'checks/recomputation-report.json'} <= actual:
            raise ValueError('Incomplete final bundle')
        for relative, value in expected.items():
            if sha(bundle/relative) != value:
                raise ValueError(f'Final artifact checksum mismatch: {bundle/relative}')
        for relative, value in json.loads((bundle/'checks/source-inventory.json').read_text()).items():
            if Path(relative).is_absolute() or '..' in Path(relative).parts or sha(directory/relative) != value:
                raise ValueError(f'Final source checksum mismatch: {relative}')


def mock_generate(batch):
    """Deterministic CPU plumbing data; never a capability/safety result."""
    return [SimpleNamespace(prompt_token_ids=r['prompt_token_ids'], outputs=[SimpleNamespace(
        text='MOCK / TEST_ONLY', token_ids=[1, 2, 3], finish_reason='stop', stop_reason=None)]) for r in batch]


def verify_weights(model_path, m):
    expected = json.loads(frozen_bytes('artifacts/pa5-supplement-qwen/baseline/weight-acceptance.json'))['weights']
    weights = json.loads((model_path/'weights-manifest.json').read_text())
    if weights['model'] != m['model_name'] or weights['revision'] != m['model_revision']:
        raise ValueError('Weight identity mismatch')
    # Frozen accepted file bytes/SHA are authoritative, not an arbitrary local manifest.
    for name, item in expected['files'].items():
        if name not in weights['files'] or any(weights['files'][name].get(k) != item[k] for k in ('bytes', 'sha256')):
            raise ValueError(f'Weight manifest mismatch: {name}')
        if (model_path/name).stat().st_size != item['bytes'] or sha(model_path/name) != item['sha256']:
            raise ValueError(f'Weight integrity mismatch: {name}')
    return weights


def run_full(directory, model_path=None, *, resume=False, mock=False, approve_full=False, max_seconds=None, generator=None):
    """Persist each completion exactly once. No inference retry inside an attempt.

    Explicit resume may regenerate uncommitted requests after a failed/crashed
    attempt. Already committed raw bytes are checked and never overwritten.
    max_seconds is a total attempt-admission budget across resumes, not a promise
    to interrupt an in-flight GPU batch at an exact billing deadline.
    """
    directory = Path(directory)
    with storage.run_lock(directory):
        m, requests, previous = validate_full(directory)
        if max_seconds is not None and (not math.isfinite(max_seconds) or max_seconds <= 0):
            raise ValueError('Time budget must be finite and positive')
        if m['mode'] == 'CPU_DRY_RUN' or mock != (m['mode'] == 'MOCK_TEST_ONLY'):
            raise ValueError('Run mode mismatch; dry-run cannot generate')
        if generator is not None and not mock:
            raise ValueError('Injected generator requires MOCK_TEST_ONLY')
        if not mock and (not approve_full or model_path is None or max_seconds is None or max_seconds <= 0):
            raise ValueError('Real Full requires P1B approval, model path and positive --max-seconds')
        attempts = sorted((directory/'attempts').glob('*/start.json'))
        if (attempts or previous) and not resume:
            raise ValueError('Existing run requires explicit --resume; no automatic retry')
        if len(previous) == len(requests):
            if json.loads((directory/'progress.json').read_text())['status'] != 'RAW_COMPLETE':
                storage.atomic_json(directory/'recoveries'/f'{uuid.uuid4().hex}.json', dict(
                    action='explicit resume reconciled all committed raw; no generation', at=now(), count=len(previous),
                    evidence={str(p.relative_to(directory)): sha(p) for p in (directory/'attempts').rglob('*') if p.is_file()}))
                storage.atomic_json(directory/'progress.json', dict(status='RAW_COMPLETE', mode=m['mode'], completed_count=len(previous), expected_count=len(requests)), replace=True)
            return dict(status='RAW_COMPLETE', count=len(previous), model_loaded=False)
        state = git_state()
        if not mock and state['git_dirty']:
            raise ValueError('Real Full requires clean committed source before inference')
        consumed = 0.0
        for path in attempts:
            old = json.loads(path.read_text())
            end = path.parent/'end.json'
            # A crash has unknown active duration; conservatively charge its full reservation.
            consumed += json.loads(end.read_text())['elapsed_seconds'] if end.exists() else (old.get('reserved_seconds') or 0)
        if max_seconds is not None and consumed >= max_seconds:
            raise ValueError('Total time budget exhausted; resource/budget review required')
        attempt_id = uuid.uuid4().hex
        attempt_dir = directory/'attempts'/attempt_id
        attempt_dir.mkdir()
        tick = time.monotonic()
        done = {(r['task'], r['example_id']) for r in previous}
        start = dict(**state, attempt_id=attempt_id, start_time=now(), mode=m['mode'],
            reserved_seconds=None if max_seconds is None else max_seconds-consumed,
            hardware_software=environment(), manifest_sha256=sha(directory/'manifest.json'),
            resume=resume, persisted_before=len(previous), generation_may_repeat_uncommitted=bool(attempts),
            missing_ids=[[r['task'], r['example_id']] for r in requests if (r['task'], r['example_id']) not in done],
            incident_evidence={str(p.relative_to(directory)): sha(p) for p in directory.rglob('*') if p.is_file() and ('.pending-' in p.name or ('attempts' in p.parts and p.parent != attempt_dir))})
        storage.atomic_json(attempt_dir/'start.json', start)
        done = {(r['task'], r['example_id']) for r in previous}
        monitor = None
        try:
            if mock:
                generate = generator or mock_generate
            else:
                weights = verify_weights(Path(model_path), m)
                monitor = VramMonitor()
                monitor.start()
                from vllm import LLM, SamplingParams
                config = m['configuration']
                llm = LLM(model=str(model_path), tokenizer=str(ROOT/config['tokenizer_path']), revision=m['model_revision'], tokenizer_revision=m['tokenizer_revision'], **config['engine'])
                sampling = SamplingParams(**config['sampling'])
                storage.atomic_json(attempt_dir/'runtime.json', dict(load_seconds=time.monotonic()-tick,
                    weights_manifest=weights, sampling_effective=str(sampling), engine_effective=str(llm.llm_engine.vllm_config)))
                generate = lambda batch: llm.generate([{'prompt_token_ids': r['prompt_token_ids']} for r in batch], sampling, use_tqdm=False)
            for task in m['tasks']:
                pending = [r for r in requests if r['task'] == task and (task, r['example_id']) not in done]
                size = m['configuration']['batch_size']
                for offset in range(0, len(pending), size):
                    if max_seconds is not None and consumed+time.monotonic()-tick >= max_seconds:
                        raise TimeoutError('Budget reached at batch boundary; remaining IDs retained')
                    batch = pending[offset:offset+size]
                    batch_id = f'{task}-{batch[0]["request_index"]:05d}'
                    storage.atomic_json(attempt_dir/f'{batch_id}.intent.json', dict(ids=[[r['task'], r['example_id']] for r in batch], started_at=now()))
                    started = time.perf_counter()
                    outputs = generate(batch)
                    elapsed = time.perf_counter()-started
                    if len(outputs) != len(batch):
                        raise ValueError('Generation returned count mismatch')
                    # Validate the whole response envelope before saving any row of this batch.
                    for inp, out in zip(batch, outputs, strict=True):
                        if list(out.prompt_token_ids) != inp['prompt_token_ids'] or len(out.outputs) != 1:
                            raise ValueError('Returned prompt identity/count mismatch')
                        v = out.outputs[0]
                        if not isinstance(v.text, str) or v.finish_reason not in ('stop', 'length') or len(v.token_ids) > m['configuration']['sampling']['max_tokens'] or not all(type(t) is int and t >= 0 for t in v.token_ids):
                            raise ValueError('Invalid generator envelope')
                    for inp, out in zip(batch, outputs, strict=True):
                        v = out.outputs[0]
                        row = {k: v for k, v in inp.items() if k != 'prompt_token_ids'}
                        row.update(schema_version='2.0', experiment_id=m['experiment_id'], run_id=m['run_id'], stage='FULL', mode=m['mode'],
                            model_name=m['model_name'], model_revision=m['model_revision'], tokenizer_revision=m['tokenizer_revision'],
                            manifest_sha256=start['manifest_sha256'], run_code_commit=state['run_code_commit'],
                            raw_response=v.text, response_token_ids=list(v.token_ids), response_token_count=len(v.token_ids),
                            finish_reason=v.finish_reason, stop_reason=v.stop_reason, generation_config=m['configuration']['sampling'],
                            attempt_id=attempt_id, batch_id=batch_id, batch_seconds=elapsed, latency_seconds=None,
                            timing_scope='batch wall seconds; excludes load/write; no per-request latency',
                            generation_status='completed', directly_comparable_to_official=False)
                        storage.commit_raw(directory/'raw'/raw_name(inp), row)
                        done.add((inp['task'], inp['example_id']))
                    storage.atomic_json(attempt_dir/f'{batch_id}.saved.json', dict(ids=[[r['task'], r['example_id']] for r in batch], batch_seconds=elapsed))
                    storage.atomic_json(directory/'progress.json', dict(status='PARTIAL', mode=m['mode'], completed_count=len(done), expected_count=len(requests), attempt_id=attempt_id), replace=True)
            if monitor:
                storage.atomic_json(attempt_dir/'vram.json', monitor.finish())
                monitor = None
            _, _, raw = validate_full(directory)
            if len(raw) != len(requests):
                raise ValueError('Final generation set mismatch')
            storage.atomic_json(attempt_dir/'end.json', dict(status='RAW_COMPLETE', end_time=now(), elapsed_seconds=time.monotonic()-tick, completed_count=len(raw)))
            storage.atomic_json(directory/'progress.json', dict(status='RAW_COMPLETE', mode=m['mode'], completed_count=len(raw), expected_count=len(requests)), replace=True)
            return dict(status='RAW_COMPLETE', count=len(raw))
        except BaseException as exc:
            try:
                if not (attempt_dir/'end.json').exists():
                    storage.atomic_json(attempt_dir/'end.json', dict(status='FAILED', end_time=now(), elapsed_seconds=time.monotonic()-tick, error_type=type(exc).__name__, error=str(exc)))
                storage.atomic_json(directory/'progress.json', dict(status='FAILED', mode=m['mode'], completed_count=len(done), expected_count=len(requests), error=str(exc)), replace=True)
            except OSError:
                pass  # Original error wins; absent terminal record remains an incomplete attempt.
            raise
        finally:
            if monitor:
                monitor.finish()


def full_metrics(examples):
    """Primary aggregation from persisted raw. Denominator includes valid bad answers."""
    scored = [dict(**row, **score(row)) for row in examples]
    n = len(scored)
    lengths = sorted(r['response_token_count'] for r in examples)
    batches = {}
    for row in examples:
        key = (row['run_id'], row['attempt_id'], row['task'], row['batch_id'])
        if key in batches and batches[key] != row['batch_seconds']:
            raise ValueError('Conflicting batch timing')
        batches[key] = row['batch_seconds']
    seconds = math.fsum(batches.values())
    empty = sum(r['raw_response'] == '' for r in examples)
    whitespace = sum(bool(r['raw_response']) and not r['raw_response'].strip() for r in examples)
    result = dict(n=n, expected_count=n, completed_count=n, empty_count=empty, whitespace_only_count=whitespace,
        blank_rate=(empty+whitespace)/n, length_termination_count=sum(r['finish_reason'] == 'length' for r in examples),
        average_response_tokens=statistics.mean(lengths), median_response_tokens=statistics.median(lengths),
        p95_response_tokens=lengths[math.ceil(.95*n)-1], finish_reasons=dict(Counter(r['finish_reason'] for r in examples)),
        generation_seconds=seconds, examples_per_second=n/seconds if seconds else None,
        output_tokens_per_second=sum(lengths)/seconds if seconds else None,
        timing_scope='sum unique recorded batch wall times; excludes load/write and lost unpersisted batches; not per-request latency',
        metric_status='MOCK_TEST_ONLY' if examples[0]['mode'] == 'MOCK_TEST_ONLY' else 'FULL',
        judge_execution_status='NOT_RUN', lc_validation_status='NOT_VALIDATED', confidence_interval=None)
    if examples[0]['task'] in ('mmlu', 'gsm8k'):
        correct = sum(r['correct'] for r in scored)
        failures = sum(r['parse_failure'] for r in scored)
        result.update(correct_count=correct, incorrect_count=n-correct, accuracy=correct/n,
            accuracy_numerator=correct, accuracy_denominator=n, accuracy_unit='fraction',
            parse_failure_count=failures, parse_failure_rate=failures/n)
    else:
        result['evaluation_status'] = 'pending_judge'
    return result, scored


def finalize_full(directory, version):
    """Publish one complete, verified derived bundle by directory rename.

    The presence of a verified finalized/<version>/manifest-final.json is the
    completion marker. progress.json describes raw capture only. A failure before
    promotion leaves .finalizing-* evidence, never a completed run.
    """
    from cs336_alignment.qwen_baseline_audit import recompute
    if not version or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_' for c in version):
        raise ValueError('Invalid score version')
    directory = Path(directory)
    with storage.run_lock(directory):
        m, requests, raw = validate_full(directory)
        expected = {(r['task'], r['example_id']) for r in requests}
        completed = {(r['task'], r['example_id']) for r in raw}
        if expected != completed:
            raise ValueError(f'PARTIAL: missing={len(expected-completed)}, unexpected={len(completed-expected)}')
        if json.loads((directory/'progress.json').read_text())['status'] != 'RAW_COMPLETE':
            raise ValueError('Unresolved capture failure: explicit --resume required before finalization')
        target = directory/'finalized'/version
        if target.exists():
            raise FileExistsError('Use a new score version; derived artifacts are immutable')
        staging = directory/f'.finalizing-{version}-{uuid.uuid4().hex}'
        staging.mkdir()
        metrics = dict(stage='FULL', run_id=m['run_id'], mode=m['mode'], scope=m['scope'],
            directly_comparable_to_official=False, judge_executed=False, results={})
        for task in m['tasks']:
            examples = sorted([r for r in raw if r['task'] == task], key=lambda r: r['request_index'])
            result, scored = full_metrics(examples)
            for r in scored:
                r.update(raw_reference=f'raw/{raw_name(r)}', raw_sha256=sha(directory/'raw'/raw_name(r)),
                    parser_sha256=m['frozen_files']['cs336_alignment/supplement_metrics.py'])
            storage.atomic_text(staging/'scored'/f'{task}.scored.jsonl', ''.join(json.dumps(r, ensure_ascii=False)+'\n' for r in scored))
            metrics['results'][task] = result
            if task == 'alpaca_eval':
                candidates = [dict(instruction=r['raw_input']['instruction'], output=r['raw_response'], generator='qwen2.5-7b-base-pa5-supplement', dataset=r['dataset']) for r in examples]
                storage.atomic_json(staging/'exports'/'alpaca_eval.json', candidates)
            elif task == 'simple_safety_tests':
                candidates = [dict(prompts_final=r['raw_input']['prompts_final'], output=r['raw_response'], example_id=r['example_id'], run_id=r['run_id'], model=r['model_name'], model_revision=r['model_revision']) for r in examples]
                storage.atomic_text(staging/'exports'/'simple_safety_tests.jsonl', ''.join(json.dumps(r, ensure_ascii=False)+'\n' for r in candidates))
        independent = recompute(directory)
        if independent != metrics['results']:
            raise ValueError('Independent disk metric recomputation mismatch')
        storage.atomic_json(staging/'metrics.json', metrics)
        storage.atomic_json(staging/'checks'/'recomputation-report.json', dict(status='PASS', mode=m['mode'], method='separate disk reader + frozen parsers + independent aggregation', results=independent))
        storage.atomic_json(staging/'checks'/'integrity-report.json', dict(status='PASS', expected_count=len(expected), completed_count=len(completed), missing_ids=0, unexpected_ids=0, duplicate_ids=0, inventory=m['inventory']))
        # Recheck raw and configuration after writing derived data; no mutable memory counter is authoritative.
        validate_full(directory)
        evidence = {str(p.relative_to(directory)): sha(p) for p in directory.rglob('*') if p.is_file() and
                    p != directory/'.runner.lock' and 'finalized' not in p.relative_to(directory).parts and
                    staging not in p.parents}
        storage.atomic_json(staging/'checks'/'source-inventory.json', evidence)
        starts = [json.loads(p.read_text()) for p in (directory/'attempts').glob('*/start.json')]
        commits = sorted({r['run_code_commit'] for r in raw})
        final = dict(**m)
        final.update(status='COMPLETED', completed_count=len(raw), start_time=min(s['start_time'] for s in starts), end_time=now(),
            run_code_commit=commits[0] if len(commits) == 1 else None, run_code_commits=commits,
            archive_commit=None, archive_commit_note='Locate archive commit through Git history; never substitute for execution commit',
            version=version, sources_inventory_sha256=sha(staging/'checks'/'source-inventory.json'),
            generation_executed=m['mode'] == 'REAL', mock_generation_executed=m['mode'] == 'MOCK_TEST_ONLY')
        storage.atomic_json(staging/'manifest-final.json', final)
        hashes = {str(p.relative_to(staging)): sha(p) for p in staging.rglob('*') if p.is_file()}
        storage.atomic_text(staging/'SHA256SUMS', ''.join(f'{value}  {path}\n' for path, value in sorted(hashes.items())))
        for path, value in hashes.items():
            if sha(staging/path) != value:
                raise ValueError(f'Final bundle checksum mismatch: {path}')
        for path in sorted((p for p in staging.rglob('*') if p.is_dir()), reverse=True):
            storage.fsync_dir(path)
        storage.fsync_dir(staging)
        os.rename(staging, target)
        try:
            storage.fsync_dir(target.parent)
        except OSError:
            os.rename(target, staging)
            raise
        return metrics


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('action',choices=['prepare','validate','run','score'])
    location = p.add_mutually_exclusive_group(required=True)
    location.add_argument('--run-dir',type=Path)
    location.add_argument('--output-dir',type=Path,help='Parent directory; requires --run-id')
    p.add_argument('--run-id')
    p.add_argument('--stage',type=str.upper,choices=['CPU_DRY_RUN','SMOKE','PILOT','FULL'])
    p.add_argument('--task',nargs='+',choices=TASKS)
    p.add_argument('--dataset-root',type=Path,help='Root containing data/mmlu, data/gsm8k, etc.')
    p.add_argument('--config',type=Path,help='Pinned model + generation JSON; tokenizer path may relocate')
    p.add_argument('--resume',action='store_true')
    p.add_argument('--mock',action='store_true')
    p.add_argument('--dry-run',action='store_true',help='Full prepare only; permanently input-only run')
    p.add_argument('--approve-full',action='store_true',help='Use only AFTER explicit P1B execution approval')
    p.add_argument('--max-seconds',type=float,help='Cumulative attempt-admission budget; see P1B runbook')
    p.add_argument('--model-path',type=Path)
    p.add_argument('--score-version',default='v1')
    args=p.parse_args()
    if args.run_id and (args.run_id in ('.','..') or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_' for c in args.run_id)):
        p.error('--run-id must be a simple identifier')
    if args.output_dir:
        if not args.run_id:p.error('--output-dir requires --run-id')
        args.run_dir=args.output_dir/args.run_id
    if args.action != 'prepare' and any((args.task, args.dataset_root, args.config, args.dry_run)):
        p.error('Input/config flags are prepare-only; resume always validates saved configuration')
    if args.action=='prepare':
        if args.stage is None:p.error('--stage required')
        options = {}
        if args.stage=='FULL':
            options=dict(tasks=args.task or TASKS, run_id=args.run_id, dataset_root=args.dataset_root or ROOT,
                config_path=args.config or CONFIG, mock=args.mock, dry_run=args.dry_run)
        elif any((args.task,args.run_id,args.config,args.dataset_root,args.mock,args.dry_run)):
            p.error('These options require --stage full')
        m=prepare(args.run_dir,args.stage,**options)
        print(json.dumps(dict(run_id=m['run_id'],stage=m['stage'],status='PREPARED',expected=m.get('expected_count'))))
    elif args.action=='validate':
        m,req,raw=validate(args.run_dir);print(json.dumps(dict(run_id=m['run_id'],expected=len(req),saved=len(raw))))
    elif args.action=='run':
        m=json.loads((args.run_dir/'manifest.json').read_text())
        if m['schema_version']=='2.0':
            print(json.dumps(run(args.run_dir,args.model_path,resume=args.resume,mock=args.mock,approve_full=args.approve_full,max_seconds=args.max_seconds)))
        else:
            if args.model_path is None:p.error('--model-path required')
            run(args.run_dir,args.model_path)
    else:
        print(json.dumps(summarize(args.run_dir,args.score_version),indent=2))


if __name__=='__main__':
    main()
