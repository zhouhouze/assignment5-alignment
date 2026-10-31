"""Independent on-disk P2-C verifier; no generator imports."""

import argparse
import hashlib
import json
from pathlib import Path


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(8 * 1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def check_sums(directory, name):
    with (directory / name).open() as f:
        for line in f:
            expected, file = line.strip().split('  ')
            if sha(directory / file) != expected:
                raise ValueError(f'Checksum mismatch: {file}')


def verify(v1, v2):
    original = json.loads((v1 / 'manifest.json').read_text())
    produced = json.loads((v2 / 'manifest.json').read_text())
    if sha(v1 / 'manifest.json') != produced['source_manifest_sha256']:
        raise ValueError('Source manifest changed')
    if produced['source_files'] != original['files']:
        raise ValueError('Source file ledger changed')
    for entry in original['files']:
        for key in ('derived', 'mapping'):
            item = entry[key]
            if sha(v1 / item['file']) != item['sha256']:
                raise ValueError('Source data/mapping changed')
    if sha(v1 / 'excluded_rows.jsonl') != produced['source_exclusions_sha256']:
        raise ValueError('Source exclusions changed')
    check_sums(v2, 'DATA_SHA256SUMS')
    check_sums(v2, 'METADATA_SHA256SUMS')
    for name, item in produced['files'].items():
        p = v2 / name
        if p.stat().st_size != item['bytes'] or sha(p) != item['sha256']:
            raise ValueError(f'Manifest output mismatch: {name}')
    delta = json.loads((v2 / 'delta-exclusion.json').read_text())
    train_source = original['files'][0]['source_sha256']
    if delta['source_row_id'] != f'{train_source}:train:181453' or delta['v1_line'] != 181433:
        raise ValueError('Wrong exclusion identity')
    rows = {}
    pair = (b'What is the capital of Australia?', b'The capital of Australia is Canberra.')
    with (v1 / 'train.jsonl').open('rb') as old, (v2 / 'train.jsonl').open('rb') as new:
        removed = 0
        retained = 0
        for old_number, original_line in enumerate(old, 1):
            if old_number == 181433:
                removed += 1
                if hashlib.sha256(original_line).hexdigest() != delta['v1_line_sha256']:
                    raise ValueError('Removed line mismatch')
            else:
                if new.readline() != original_line:
                    raise ValueError(f'Byte mutation or row displacement: {old_number}')
                retained += 1
                obj = json.loads(original_line)
                if (obj['prompt'].encode(), obj['response'].encode()) == pair:
                    raise ValueError('AlpacaEval 370 pair remains in Train')
        if new.readline() or removed != 1 or retained != 210325:
            raise ValueError('Train row count or trailing data mismatch')
        rows['train'] = retained
    for name, expected in [('validation', 23108), ('sample_train', 1000)]:
        if sha(v1 / f'{name}.jsonl') != sha(v2 / f'{name}.jsonl'):
            raise ValueError(f'{name} changed')
        with (v2 / f'{name}.jsonl').open('rb') as f:
            rows[name] = sum(1 for _ in f)
        if rows[name] != expected:
            raise ValueError(f'{name} row count mismatch')
        if sha(v1 / f'{name}.mapping.tsv') != sha(v2 / f'{name}.mapping.tsv'):
            raise ValueError(f'{name} mapping changed')
    if sha(v1 / 'excluded_rows.jsonl') != sha(v2 / 'excluded_rows.jsonl'):
        raise ValueError('Historical exclusions changed')
    with (v1 / 'train.mapping.tsv').open() as old, (v2 / 'train.mapping.tsv').open() as new:
        if old.readline() != new.readline():
            raise ValueError('Mapping header mismatch')
        mapped = 0
        excluded = 0
        for oldrow in old:
            newrow = new.readline()
            src, position = map(int, oldrow.rstrip('\n').split('\t'))
            new_src, new_position = map(int, newrow.rstrip('\n').split('\t'))
            expected_position = 0 if position == 181433 else position - (position > 181433)
            if src != new_src or new_position != expected_position or (src == 181453) != (position == 181433):
                raise ValueError(f'Mapping disagreement at Raw {src}')
            mapped += new_position != 0
            excluded += new_position == 0
        if new.readline() or mapped != 210325 or excluded != 23:
            raise ValueError('Mapping count mismatch')
    train_pairs = set()
    with (v2 / 'train.jsonl').open() as f:
        for line in f:
            obj = json.loads(line)
            train_pairs.add((obj['prompt'], obj['response']))
    with (v2 / 'sample_train.jsonl').open() as f:
        if not all((obj['prompt'], obj['response']) in train_pairs for obj in map(json.loads, f)):
            raise ValueError('Sample Train no longer subset of Train')
    if rows != produced['output_rows']:
        raise ValueError('Manifest row count mismatch')
    return dict(status='PASS', rows=rows, removed_raw_line=181453, removed_v1_line=181433,
                train_mapping_excluded=excluded, sample_pair_subset_of_train=True,
                alpaca_eval_370_exact_pair_remaining=0, manifest_sha256=sha(v2 / 'manifest.json'))


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--v1', type=Path, required=True)
    p.add_argument('--v2', type=Path, required=True)
    p.add_argument('--report', type=Path, required=True)
    a = p.parse_args()
    result = verify(a.v1, a.v2)
    with a.report.open('x') as f:
        json.dump(result, f, indent=2)
        f.write('\n')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
