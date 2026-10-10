"""Reproduce P1A CPU coverage and MOCK_TEST_ONLY IO acceptance, never GPU inference.

Usage: python scripts/verify_qwen_full_cpu.py --report /tmp/p1a-report.json
Temporary raw remains outside the repository for inspection, not formal results.
Only the compact report is intended for Git archival; it contains no mock scores.
"""
import argparse
import json
from pathlib import Path
import sys
import tempfile
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from cs336_alignment import qwen_baseline as b
from cs336_alignment import qwen_baseline_storage as s

P0_IDS = dict(zip(b.TASKS, [
    '80a50c01f339362887feb3c853f6f7558e187bf1ae6b75005a918ac39ec0926e',
    '57695ad86447a1794056b2e3e90739995477110e7c648781821347f712ad990e',
    'cbd581cdd91f69501a8b04a2d2286217da7f6d97ebfbdf4d01dcecb762368f06',
    '5664de77bf3e075247ef46ae191c6a53d95e8df882659c747744b5662880fe49']))
P0_RENDER = dict(zip(b.TASKS, [
    '983d4e908fc07803a332f42cee9ed22be2517840268b3dfc1324985fda3503ac',
    'df4dd6af87967bd1a3918efd3ac5b9c275e701b7d82d8b94214d03399e13cca1',
    'f7c1364dfffc4fe32b3ab59b5ec5eb329a66f080653722f896cda4ac9c9d435d',
    '20c6f6c77a7a2265c9c079ff3c0d477b1eadfa0baa791819bbaa40ad8b93e60b']))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    work = Path(tempfile.mkdtemp(prefix='pa5-P1A-MOCK_TEST_ONLY-'))
    timings = {}
    for mode in ('dry', 'mock'):
        tick = time.monotonic()
        m = b.prepare(work/mode, 'full', dry_run=mode == 'dry', mock=mode == 'mock')
        for task, inventory in m['inventory'].items():
            assert inventory['expected_count'] == b.FULL_COUNTS[task]
            assert inventory['ordered_ids_sha256'] == P0_IDS[task]
            assert inventory['rendered_inventory_sha256'] == P0_RENDER[task]
        assert m['expected_count'] == 16266
        timings[f'{mode}_prepare_seconds'] = time.monotonic()-tick
        print(f'{mode}: CPU input coverage 16266/16266; P0 IDs/render hashes MATCH', flush=True)
    tick = time.monotonic()
    b.run(work/'mock', mock=True)
    timings['mock_capture_seconds'] = time.monotonic()-tick
    print('MOCK_TEST_ONLY: saved 16266/16266', flush=True)
    tick = time.monotonic()
    metrics = b.summarize(work/'mock', 'v1')
    b.validate(work/'mock')
    timings['score_audit_finalize_seconds'] = time.monotonic()-tick
    assert 'vllm' not in sys.modules
    final = work/'mock'/'finalized/v1'
    alpaca = json.loads((final/'exports/alpaca_eval.json').read_text())
    safety = [json.loads(line) for line in (final/'exports/simple_safety_tests.jsonl').read_text().splitlines()]
    assert len(alpaca) == 805 and all(set(r) == {'instruction','output','generator','dataset'} for r in alpaca)
    assert len(safety) == 100 and all(isinstance(r['output'], str) and r['example_id'] for r in safety)
    sizes = {name: sum(p.stat().st_size for p in (work/'mock'/name).rglob('*') if p.is_file()) for name in ('raw','attempts','finalized')}
    files = [p for p in (work/'mock').rglob('*') if p.is_file()]
    report = dict(status='PASS', mode='MOCK_TEST_ONLY', created_at=b.now(), source=b.git_state(),
        code_sources_sha256=m['sources'], test_driver_sha256=b.sha(Path(__file__)),
        protocol_id=m['evaluation_protocol_id'], protocol_sha256=m['protocol_sha256'],
        generation_executed=False, gpu_model_loaded=False, vllm_imported=False, mock_generation_executed=True,
        full_real_generation_status='NOT_RUN', input_inventory=m['inventory'], dataset_sha256=m['dataset_sha256'],
        dataset_file_count=len(m['dataset_hashes']), coverage={task: dict(expected=b.FULL_COUNTS[task], verified=result['n']) for task,result in metrics['results'].items()},
        total_verified=sum(result['n'] for result in metrics['results'].values()),
        independent_recomputation='PASS', candidate_schemas='PASS', timings=timings,
        sizes_bytes=sizes, total_bytes=sum(p.stat().st_size for p in files), file_count=len(files),
        temporary_artifacts=str(work), temporary_artifacts_durability='NON_DURABLE; reproducible CPU MOCK; not experimental raw',
        final_bundle_checksums_sha256=b.sha(final/'SHA256SUMS'),
        note='No capability/safety scores archived from mocks. Re-run this driver to recreate plumbing evidence.')
    s.atomic_json(args.report, report)
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
