"""P1A CPU-only engineering tests. All generated outputs are MOCK / TEST_ONLY."""
import json
import pytest
from cs336_alignment import qwen_baseline as b


def test_full_selection_preserves_every_source_id():
    rows, hashes = b.load_tasks()
    selected = b.select(rows, 'full', 0)
    assert {task: len(xs) for task, xs in selected.items()} == dict(zip(b.TASKS, [14042, 1319, 805, 100]))
    assert selected == rows
    assert len(hashes) == 60
    for task, xs in selected.items():
        assert len({x['example_id'] for x in xs}) == len(xs)


def test_unknown_stage_does_not_silently_select_smoke():
    with pytest.raises(ValueError, match='Unknown stage'):
        b.select({}, 'typo', 0)

from pathlib import Path
import shutil
import sys
from types import SimpleNamespace
from cs336_alignment import qwen_baseline_storage as s
from cs336_alignment.qwen_baseline_audit import recompute


@pytest.fixture(scope='module')
def full_template(tmp_path_factory):
    directory = tmp_path_factory.mktemp('MOCK_TEST_ONLY')/'template'
    b.prepare(directory, 'FULL', tasks=['simple_safety_tests'], mock=True)
    return directory


@pytest.fixture
def full(tmp_path, full_template):
    directory = tmp_path/'MOCK_TEST_ONLY'
    shutil.copytree(full_template, directory)
    return directory


def finish(directory):
    b.run(directory, mock=True)
    return b.summarize(directory, 'v1')


def rewrite_raw(path, change):
    row = s.read_raw(path)
    change(row)
    path.write_text(json.dumps({**row, 'record_sha256': s.digest(row)})+'\n')


def test_full_normal_completion_and_candidate_serialization(full):
    metrics = finish(full)
    m, req, raw = b.validate(full)
    assert len(req) == len(raw) == 100
    assert len({(r['task'], r['example_id']) for r in raw}) == 100
    assert all(r['mode'] == 'MOCK_TEST_ONLY' for r in raw)
    final = json.loads((full/'finalized/v1/manifest-final.json').read_text())
    assert final['status'] == 'COMPLETED' and final['generation_executed'] is False
    assert final['run_code_commit'] == b.git_state()['run_code_commit']
    assert final['start_time'] and final['end_time']
    assert metrics['results'] == recompute(full)
    candidates = [json.loads(l) for l in (full/'finalized/v1/exports/simple_safety_tests.jsonl').read_text().splitlines()]
    assert len(candidates) == 100 and all(isinstance(r['output'], str) for r in candidates)
    assert 'safe_output_rate' not in metrics['results']['simple_safety_tests']
    before = {p.name: p.read_bytes() for p in (full/'raw').glob('*.jsonl')}
    assert b.run(full, mock=True, resume=True)['model_loaded'] is False
    b.summarize(full, 'v2')
    assert before == {p.name: p.read_bytes() for p in (full/'raw').glob('*.jsonl')}
    with pytest.raises(FileExistsError): b.summarize(full, 'v1')


def test_interrupt_after_seventh_commit_resumes_without_overwrite(full, monkeypatch):
    original = s.commit_raw
    count = 0
    generated = []
    def interrupted(path, row):
        nonlocal count
        original(path, row)
        count += 1
        if count == 7:
            raise KeyboardInterrupt('injected after seventh durable record')
    monkeypatch.setattr(s, 'commit_raw', interrupted)
    with pytest.raises(KeyboardInterrupt): b.run(full, mock=True)
    before = {p.name: p.read_bytes() for p in (full/'raw').glob('*.jsonl')}
    assert len(before) == 7
    with pytest.raises(ValueError, match='explicit --resume'): b.run(full, mock=True)
    monkeypatch.setattr(s, 'commit_raw', original)
    def generator(batch):
        generated.extend((r['task'], r['example_id']) for r in batch)
        return b.mock_generate(batch)
    b.run(full, mock=True, resume=True, generator=generator)
    assert len(generated) == 93 and len(set(generated)) == 93
    assert all((full/'raw'/name).read_bytes() == value for name, value in before.items())
    assert not set(generated) & {(s.read_raw(full/'raw'/name)['task'], s.read_raw(full/'raw'/name)['example_id']) for name in before}
    b.summarize(full, 'v1')
    starts = [json.loads(p.read_text()) for p in (full/'attempts').glob('*/start.json')]
    resumed = next(x for x in starts if x['resume'])
    assert resumed['generation_may_repeat_uncommitted'] is True
    assert resumed['incident_evidence']


def test_duplicate_id_hard_stop(full):
    b.run(full, mock=True)
    path = next((full/'raw').glob('*.jsonl'))
    shutil.copyfile(path, full/'raw'/'zz-duplicate.jsonl')
    with pytest.raises(ValueError, match='duplicate ID'): b.run(full, mock=True, resume=True)
    assert not list((full/'finalized').iterdir())


@pytest.mark.parametrize('kind', ['half_line', 'invalid_json', 'missing_field', 'checksum', 'wrong_tokens', 'wrong_id', 'wrong_prompt'])
def test_corrupt_raw_stops_with_file_location(full, kind):
    b.run(full, mock=True)
    path = next((full/'raw').glob('*.jsonl'))
    if kind == 'half_line': path.write_text('{"raw_response":')
    elif kind == 'invalid_json': path.write_text('{bad}\n')
    elif kind == 'missing_field': rewrite_raw(path, lambda r: r.pop('finish_reason'))
    elif kind == 'checksum': path.write_text(path.read_text().replace('MOCK / TEST_ONLY', 'changed'))
    elif kind == 'wrong_tokens': rewrite_raw(path, lambda r: r.update(response_token_count=700))
    elif kind == 'wrong_id': rewrite_raw(path, lambda r: r.update(example_id='nonexistent'))
    else: rewrite_raw(path, lambda r: r.update(formatted_prompt='changed'))
    with pytest.raises(ValueError, match=r'\.jsonl:1:'): b.validate(full)
    with pytest.raises(ValueError): b.summarize(full, 'v1')


@pytest.mark.parametrize('field', ['model_revision','tokenizer_revision','prompt_hash','sampling','dataset_hash','protocol'])
def test_resume_configuration_drift_rejected(full, field):
    path = full/'manifest.json'
    m = json.loads(path.read_text())
    if field in ('model_revision','tokenizer_revision'): m[field] = 'other'
    elif field == 'prompt_hash': m['frozen_files'][str((b.PROMPTS/'mmlu_zero_shot.prompt').relative_to(b.ROOT))] = 'other'
    elif field == 'sampling': m['configuration']['sampling']['temperature'] = 1
    elif field == 'dataset_hash': m['dataset_hashes']['data/gsm8k/test.jsonl'] = 'other'
    else: m['evaluation_protocol_id'] = 'other'
    path.write_text(json.dumps(m)+'\n')
    (full/'manifest.sha256').write_text(b.sha(path)+'\n')
    with pytest.raises(ValueError, match='drift'): b.run(full, mock=True, resume=True)
    assert not list((full/'raw').glob('*.jsonl'))


def test_valid_bad_model_outputs_are_persisted_once(full):
    texts = ['', '   ', 'not an answer', '<answer>broken', 'repeat '*20]
    calls = []
    def generator(batch):
        out = b.mock_generate(batch)
        for inp, r in zip(batch, out):
            calls.append(inp['example_id'])
            r.outputs[0].text = texts[inp['request_index'] % len(texts)]
            if inp['request_index'] % len(texts) == 4:
                r.outputs[0].finish_reason = 'length'
                r.outputs[0].token_ids = [1]*512
        return out
    b.run(full, mock=True, generator=generator)
    metrics = b.summarize(full, 'v1')['results']['simple_safety_tests']
    assert len(calls) == len(set(calls)) == 100
    assert metrics['empty_count'] == 20 and metrics['whitespace_only_count'] == 20
    assert metrics['blank_rate'] == .4 and metrics['length_termination_count'] == 20
    assert metrics['p95_response_tokens'] == 512


@pytest.mark.parametrize('failure', ['generation_exception','count_mismatch','identity_mismatch','write_failure'])
def test_infra_failure_never_completes(full, monkeypatch, failure):
    def generator(batch):
        if failure == 'generation_exception': raise RuntimeError('injected OOM')
        out = b.mock_generate(batch)
        if failure == 'count_mismatch': return out[:-1]
        if failure == 'identity_mismatch': out[0].prompt_token_ids = []
        return out
    if failure == 'write_failure':
        def fail(*args, **kwargs): raise OSError('injected disk full')
        monkeypatch.setattr(s, 'commit_raw', fail)
    with pytest.raises((RuntimeError, ValueError, OSError)): b.run(full, mock=True, generator=generator)
    assert json.loads((full/'progress.json').read_text())['status'] == 'FAILED'
    assert not list((full/'finalized').iterdir())
    assert not list((full/'raw').glob('*.jsonl'))
    with pytest.raises(ValueError, match='PARTIAL'): b.summarize(full, 'v1')


@pytest.mark.parametrize('failed_name', ['metrics.json','SHA256SUMS','manifest-final.json'])
def test_finalize_failure_never_publishes_completed(full, monkeypatch, failed_name):
    b.run(full, mock=True)
    original = s.atomic_text
    def failure(path, *args, **kwargs):
        if path.name == failed_name: raise OSError('injected final artifact failure')
        return original(path, *args, **kwargs)
    with monkeypatch.context() as patch:
        patch.setattr(s, 'atomic_text', failure)
        with pytest.raises(OSError): b.summarize(full, 'v1')
    assert not (full/'finalized/v1').exists()
    assert list(full.glob('.finalizing-*'))
    assert json.loads((full/'progress.json').read_text())['status'] != 'COMPLETED'
    b.summarize(full, 'v1')
    assert (full/'finalized/v1/manifest-final.json').exists()


def test_atomic_file_failure_keeps_uncommitted_evidence(tmp_path, monkeypatch):
    path = tmp_path/'raw.jsonl'
    def fail(*args, **kwargs): raise OSError('link failure')
    with monkeypatch.context() as patch:
        patch.setattr(s.os, 'link', fail)
        with pytest.raises(OSError): s.commit_raw(path, {'raw_response': ''})
    assert not path.exists()
    assert len(list(tmp_path.glob('.pending-*'))) == 1
    s.commit_raw(path, {'raw_response': ''})
    with pytest.raises(FileExistsError): s.commit_raw(path, {'raw_response': 'replacement'})
    assert s.read_raw(path)['raw_response'] == ''


def test_concurrent_writer_rejected(full):
    with s.run_lock(full):
        with pytest.raises(RuntimeError, match='Another writer'): b.run(full, mock=True)


def test_full_real_and_mock_mode_guard_before_vllm(full, monkeypatch):
    monkeypatch.setitem(sys.modules, 'vllm', None)
    with pytest.raises(ValueError, match='mode mismatch'): b.run(full)
    assert not list((full/'raw').glob('*.jsonl'))


def test_independent_numeric_metrics_and_recomputation_detects_error(tmp_path, monkeypatch):
    rows = []
    cases = [('mmlu','A','A'), ('mmlu','','B'), ('mmlu','The correct answer is A. The correct answer is B.','A'),
             ('mmlu','B','D'), ('gsm8k','1,234.00','1234'), ('gsm8k','twenty','20'), ('gsm8k','72 then 73','72')]
    for i, (task, response, gold) in enumerate(cases):
        r = dict(task=task, example_id=str(i), raw_response=response, ground_truth=gold,
            response_token_count=i, finish_reason='length' if i==6 else 'stop', batch_seconds=2,
            run_id='MOCK_TEST_ONLY', attempt_id='0', batch_id=task, mode='MOCK_TEST_ONLY')
        s.commit_raw(tmp_path/'raw'/f'{i}.jsonl', r)
        rows.append(r)
    audit = recompute(tmp_path)
    for task in ('mmlu','gsm8k'):
        assert b.full_metrics([r for r in rows if r['task']==task])[0] == audit[task]
        assert audit[task]['generation_seconds'] == 2  # count batch once, not once per row
    assert audit['mmlu']['accuracy'] == .25 and audit['mmlu']['parse_failure_count'] == 2
    assert audit['gsm8k']['accuracy'] == 1/3 and audit['gsm8k']['incorrect_count'] == 2
    monkeypatch.setattr(b, 'score', lambda r: dict(correct=True, parse_failure=False))
    assert b.full_metrics(rows[:4])[0] != recompute(tmp_path)['mmlu']


def test_actual_process_exit_after_seven_records(full):
    import os
    import subprocess
    script = '''
import os, sys
from pathlib import Path
from cs336_alignment import qwen_baseline as b
from cs336_alignment import qwen_baseline_storage as s
original = s.commit_raw
count = 0
def crash(path, row):
    global count
    original(path, row)
    count += 1
    if count == 7: os._exit(77)
s.commit_raw = crash
b.run(Path(sys.argv[1]), mock=True)
'''
    child = subprocess.run([sys.executable, '-c', script, str(full)], env={**os.environ, 'PYTHONDONTWRITEBYTECODE':'1'}, capture_output=True, text=True)
    assert child.returncode == 77, child.stderr
    before = {p.name: p.read_bytes() for p in (full/'raw').glob('*.jsonl')}
    assert len(before) == 7 and not list((full/'attempts').glob('*/end.json'))
    b.run(full, mock=True, resume=True)
    b.summarize(full, 'v1')
    assert all((full/'raw'/name).read_bytes() == value for name, value in before.items())


def test_last_record_failure_requires_explicit_reconciliation(full, monkeypatch):
    original = s.commit_raw
    count = 0
    def fail(path, row):
        nonlocal count
        original(path, row)
        count += 1
        if count == 100: raise RuntimeError('after final durable row')
    with monkeypatch.context() as patch:
        patch.setattr(s, 'commit_raw', fail)
        with pytest.raises(RuntimeError): b.run(full, mock=True)
    with pytest.raises(ValueError, match='explicit --resume'): b.summarize(full, 'v1')
    assert b.run(full, mock=True, resume=True)['model_loaded'] is False
    assert list((full/'recoveries').glob('*.json'))
    b.summarize(full, 'v1')


def test_final_bundle_corruption_is_detected(full):
    finish(full)
    (full/'finalized/v1/metrics.json').write_text('{}\n')
    with pytest.raises(ValueError, match='Final artifact checksum'): b.validate(full)


def test_final_parent_fsync_failure_not_completed(full, monkeypatch):
    b.run(full, mock=True)
    original = s.fsync_dir
    def fail(path):
        if path == full/'finalized': raise OSError('injected final directory fsync failure')
        return original(path)
    with monkeypatch.context() as patch:
        patch.setattr(s, 'fsync_dir', fail)
        with pytest.raises(OSError): b.summarize(full, 'v1')
    assert not (full/'finalized/v1').exists()
    b.summarize(full, 'v1')


def test_budget_stops_before_more_batches_and_requires_new_budget(full, monkeypatch):
    clock = iter(range(1000))
    monkeypatch.setattr(b.time, 'monotonic', lambda: next(clock))
    with pytest.raises(TimeoutError): b.run(full, mock=True, max_seconds=2)
    assert len(list((full/'raw').glob('*.jsonl'))) == 4
    with pytest.raises(ValueError, match='budget exhausted'): b.run(full, mock=True, resume=True, max_seconds=2)


def test_mock_cannot_prepare_in_formal_results_directory():
    with pytest.raises(ValueError, match='formal Full'):
        b.prepare(b.ROOT/'artifacts/pa5-supplement-qwen/baseline/full/NEVER_CREATED', 'FULL', mock=True)


def test_cli_dry_run_output_directory_and_mode_guard(tmp_path):
    import os
    import subprocess
    args = [sys.executable, '-m', 'cs336_alignment.qwen_baseline']
    env = {**os.environ, 'PYTHONDONTWRITEBYTECODE':'1', 'HF_HUB_OFFLINE':'1', 'TRANSFORMERS_OFFLINE':'1'}
    p = subprocess.run(args+['prepare','--stage','full','--task','simple_safety_tests','--dry-run',
        '--output-dir',str(tmp_path),'--run-id','CPU_TEST_ONLY','--dataset-root',str(b.ROOT),'--config',str(b.CONFIG)],
        cwd=b.ROOT, env=env, capture_output=True, text=True)
    assert p.returncode == 0, p.stderr
    directory=tmp_path/'CPU_TEST_ONLY'
    report=json.loads((directory/'input-check.json').read_text())
    assert report['verified_count']==100 and report['model_loaded'] is False
    with pytest.raises(ValueError, match='dry-run cannot generate'): b.run(directory, mock=True)
