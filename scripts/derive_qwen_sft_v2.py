"""P2-C only: exclude one approved source row from accepted Derived-v1."""

import argparse
import gzip
import hashlib
import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
V1 = Path('/Users/hr/Documents/Lesson/pa5-experiment-backups/sft/20261028-p2a2-derived-v1')
TARGET_RAW = 181453
TARGET_V1 = 181433
PAIR = ('What is the capital of Australia?', 'The capital of Australia is Canberra.')


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(8 * 1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def identity():
    manifest = V1 / 'manifest.json'
    if sha(manifest) != 'c9eaf0e154f073500c237d6242a3d4188cdaf15e715a183e23d164813d3c352f':
        raise ValueError('v1 manifest SHA mismatch')
    m = json.loads(manifest.read_text())
    for entry in m['files']:
        for field in ('derived', 'mapping'):
            item = entry[field]
            p = V1 / item['file']
            if sha(p) != item['sha256'] or p.stat().st_size != item['bytes']:
                raise ValueError(f'v1 {field} identity mismatch: {p}')
    for name, expected in [('excluded_rows.jsonl', m['exclusions']['sha256']),
                           ('DATA_SHA256SUMS', '25767eca9417ef936f265bd8be9af38c59e70f1c4a441eccdd900c7c24be3c18'),
                           ('METADATA_SHA256SUMS', '7c6819f7ee4020b1c1f4bf5e427a312cc548c63678fce75ef279239e9d849dc5')]:
        if sha(V1 / name) != expected:
            raise ValueError(f'v1 metadata mismatch: {name}')
    train = m['files'][0]
    raw = ROOT / 'data/qwen-sft-mirror/sft-instruct/train.jsonl'
    if sha(raw) != train['source_sha256']:
        raise ValueError('Raw train SHA mismatch')
    with raw.open('rb') as f:
        raw_line = next(line for i, line in enumerate(f, 1) if i == TARGET_RAW)
    with (V1 / 'train.jsonl').open('rb') as f:
        derived_line = next(line for i, line in enumerate(f, 1) if i == TARGET_V1)
    if raw_line != derived_line or tuple(json.loads(raw_line)[k] for k in ('prompt', 'response')) != PAIR:
        raise ValueError('Target source/content mismatch')
    with (V1 / 'train.mapping.tsv').open() as f:
        next(f)
        mapping = next((int(b) for a, b in (line.rstrip('\n').split('\t') for line in f)
                        if int(a) == TARGET_RAW), None)
    if mapping != TARGET_V1:
        raise ValueError('Target mapping mismatch')
    benchmark = ROOT / 'data/alpaca_eval/alpaca_eval_gpt4_turbo.json'
    if sha(benchmark) != '83db546b872ddebee8965fd05fa48461ee3c32bc695c62fb57f2d214ff741ec4':
        raise ValueError('Benchmark SHA mismatch')
    ref = json.loads(benchmark.read_text())[370]
    if (ref['instruction'], ref['output']) != PAIR:
        raise ValueError('Benchmark record mismatch')
    candidate_file = ROOT / 'artifacts/pa5-supplement-qwen/sft/20261028-p2b1/candidates.jsonl.gz'
    if sha(candidate_file) != '256563a0f534ee87d3529769445fdae2ac80ef8569e74f62572aeb8a70892569':
        raise ValueError('Archived candidate ledger SHA mismatch')
    found = {}
    with gzip.open(candidate_file, 'rt') as f:
        for line in f:
            c = json.loads(line)
            if c['candidate_id'] in (3273, 3274):
                found[c['candidate_id']] = c
    if set(found) != {3273, 3274}:
        raise ValueError('Candidate IDs missing')
    for number, key, refkey in [(3273, 'prompt', 'instruction'), (3274, 'response', 'output')]:
        c = found[number]
        value = json.loads(raw_line)[key]
        if (c['method'] != 'exact' or c['train']['source_row_id'] != f"{train['source_sha256']}:train:{TARGET_RAW}"
            or c['train']['derived_line'] != TARGET_V1 or c['train']['field'] != key
            or c['train']['text_sha256'] != hashlib.sha256(value.encode()).hexdigest()
            or c['target']['example_id'] != '370' or c['target']['field'] != ('gpt4_reference_output' if refkey == 'output' else refkey)
            or c['target']['text_sha256'] != hashlib.sha256(ref[refkey].encode()).hexdigest()):
            raise ValueError(f'Candidate fingerprint mismatch: {number}')
    if any(tuple(json.loads(line)[k] for k in ('prompt', 'response')) == PAIR
           for line in (V1 / 'sample_train.jsonl').open('rb')):
        raise ValueError('Target exists in Sample Train; stop')
    return m, hashlib.sha256(raw_line).hexdigest()


def copy_excluding(source, dest, target):
    count = 0
    with source.open('rb') as inp, dest.open('xb') as out:
        for count, line in enumerate(inp, 1):
            if count != target:
                out.write(line)
    if count < target:
        raise ValueError('Target line outside input')
    return count - 1


def remap(source, dest, target):
    rows = 0
    with source.open() as inp, dest.open('x') as out:
        out.write(next(inp))
        for line in inp:
            src, old = map(int, line.rstrip('\n').split('\t'))
            new = 0 if old == target else old - (old > target)
            out.write(f'{src}\t{new}\n')
            rows += 1
            if src == TARGET_RAW and old != target:
                raise ValueError('Target mapping moved')
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    out = args.output.resolve()
    data = (ROOT / 'data').resolve()
    if out.exists() or out == V1 or V1 in out.parents or out in V1.parents or out == data or data in out.parents:
        raise ValueError('Output exists or may cover source')
    m, line_sha = identity()
    out.mkdir(parents=False, exist_ok=False)
    try:
        rows = copy_excluding(V1 / 'train.jsonl', out / 'train.jsonl', TARGET_V1)
        if rows != 210325:
            raise ValueError('Unexpected train row count')
        for name in ('validation.jsonl', 'sample_train.jsonl'):
            with (V1 / name).open('rb') as inp, (out / name).open('xb') as dest:
                shutil.copyfileobj(inp, dest)
        remap(V1 / 'train.mapping.tsv', out / 'train.mapping.tsv', TARGET_V1)
        for name in ('validation.mapping.tsv', 'sample_train.mapping.tsv', 'excluded_rows.jsonl'):
            with (V1 / name).open('rb') as inp, (out / name).open('xb') as dest:
                shutil.copyfileobj(inp, dest)
        delta = dict(source_row_id=f"{m['files'][0]['source_sha256']}:train:{TARGET_RAW}",
                     raw_line=TARGET_RAW, v1_line=TARGET_V1, v1_line_sha256=line_sha,
                     reason='exact_alpaca_eval_370_instruction_and_reference_output',
                     candidate_ids=[3273, 3274], benchmark_record_index_0based=370)
        (out / 'delta-exclusion.json').write_text(json.dumps(delta, indent=2) + '\n')
        files = {p.name: dict(bytes=p.stat().st_size, sha256=sha(p)) for p in sorted(out.iterdir()) if p.is_file()}
        result = dict(gate='P2-C', status='GENERATED_PENDING_INDEPENDENT_VERIFICATION',
                      created_at=datetime.now(timezone.utc).isoformat(), source_version='derived-v1',
                      source_manifest_sha256=sha(V1 / 'manifest.json'), source_files=m['files'],
                      source_exclusions_sha256=m['exclusions']['sha256'], derived_version='derived-v2',
                      rule='Remove only train raw line 181453 / v1 line 181433 per user P2-C authorization',
                      authorization='User authorized P2-C CPU derivation and archival in this conversation',
                      execution_commit=subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
                      output_rows={'train': rows, 'validation': 23108, 'sample_train': 1000},
                      data_admission='PENDING', directly_comparable_to_official=False, files=files)
        (out / 'manifest.json').write_text(json.dumps(result, indent=2) + '\n')
        for group, names in [('DATA', ('train.jsonl', 'validation.jsonl', 'sample_train.jsonl')),
                             ('METADATA', ('train.mapping.tsv', 'validation.mapping.tsv', 'sample_train.mapping.tsv', 'excluded_rows.jsonl', 'delta-exclusion.json', 'manifest.json'))]:
            with (out / f'{group}_SHA256SUMS').open('x') as f:
                for name in names:
                    f.write(f'{sha(out / name)}  {name}\n')
        print(json.dumps(dict(status='GENERATED', rows=result['output_rows'], manifest_sha256=sha(out / 'manifest.json'))))
    except Exception:
        (out / 'failure.txt').write_text('P2-C generation stopped; inspect source and partial files.\n')
        raise


if __name__ == '__main__':
    main()
