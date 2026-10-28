"""Independent disk verifier for P2-A.2; imports no derivation/classifier code.

Reads Raw, Derived, complete mappings, exclusions and manifest. Byte comparison
checks all retained fields, order and multiplicity, not just prompt/response.
Exact overlap uses unnormalized strings; sample/train containment is expected.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys
from datetime import datetime, timezone


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        while block := f.read(1024 * 1024):
            h.update(block)
    return h.hexdigest()


def verify_bundle(folder, raw_dir, a1_path):
    """Check each disk record independently; return measured overlap and counts."""
    m = json.loads((folder / 'manifest.json').read_text())
    a1 = json.loads(a1_path.read_text())
    require(sha(a1_path) == m['a1_sha256'], 'A.1 SHA mismatch')
    require(a1['status'] == 'PASS' and m['rule_sha256'] == a1['policy_sha256'], 'Policy/A.1 status')
    require(m['status'] == 'GENERATED_PENDING_INDEPENDENT_VERIFICATION', 'Manifest status')
    require(len(m['files']) == len(a1['files']), 'Split count')
    exclusions = [json.loads(x) for x in (folder / 'excluded_rows.jsonl').read_text().splitlines()]
    expected = [x for f in a1['files'] for x in f['anomalies']]
    require(exclusions == expected, 'Exclusions vs A.1 mismatch')
    summaries, prompts, pairs = {}, {}, {}
    for f, prior in zip(m['files'], a1['files']):
        split = f['split']; fingerprint = f['source_sha256']
        require(split == prior['split'] and fingerprint == prior['sha256'], 'Source identity')
        raw = raw_dir / f['source_file']
        require(raw.name == Path(prior['source_path']).name, 'Source filename')
        require(sha(raw) == fingerprint and raw.stat().st_size == prior['bytes'] == f['source_bytes'], 'Raw SHA/bytes')
        relevant = {x['line_number']: x for x in exclusions if x['split'] == split}
        require(len(relevant) == f['excluded_rows'], 'Exclusion count')
        prompts[split], pairs[split] = set(), set()
        retained = total = removed = 0
        with raw.open('rb') as source, (folder / f['derived']['file']).open('rb') as derived, (folder / f['mapping']['file']).open() as mapping:
            require(next(mapping) == 'source_line\tderived_line\n', 'Mapping header')
            for total, data in enumerate(source, 1):
                value = json.loads(data.decode('utf-8'))
                require(isinstance(value, dict) and all(isinstance(value.get(k), str) for k in ('prompt', 'response')), 'Schema')
                reasons = []
                for key in ('prompt', 'response'):
                    s = value[key]
                    if len(s) == 0:
                        reasons.append('empty_' + key)
                    elif s.isspace():
                        reasons.append('whitespace_only_' + key)
                row = mapping.readline().rstrip('\n').split('\t')
                if reasons:
                    removed += 1
                    expected_row = {'source_row_id': f'{fingerprint}:{split}:{total}', 'source_file_sha256': fingerprint,
                                    'source_file': raw.name, 'split': split, 'line_number': total, 'reasons': reasons}
                    require(relevant.get(total) == expected_row, 'Excluded reason/identity')
                    require(row == [str(total), '0'], 'Excluded mapping')
                else:
                    retained += 1
                    require(total not in relevant, 'Unexpected exclusion')
                    require(row == [str(total), str(retained)], 'Retained mapping')
                    require(derived.readline() == data, 'Derived content/order/missing record')
                    prompts[split].add(value['prompt'])
                    pairs[split].add((value['prompt'], value['response']))
            require(not derived.read(1) and not mapping.read(1), 'Extra derived/mapping rows')
        require(total == prior['physical_lines'] == f['source_rows'] == retained + removed, 'Row conservation')
        require(retained == f['derived']['rows'] and total == f['mapping']['rows'] and removed == f['excluded_rows'], 'Manifest row counts')
        require(sha(raw) == fingerprint, 'Raw changed during verification')
        summaries[split] = {'raw_rows': total, 'derived_rows': retained, 'excluded_rows': removed, 'byte_identity': 'PASS'}
    for info in [m['exclusions']] + [f[k] for f in m['files'] for k in ('derived', 'mapping')]:
        p = folder / info['file']
        require(p.stat().st_size == info['bytes'] and sha(p) == info['sha256'], 'Manifest output bytes/SHA')
    require(len(exclusions) == m['exclusions']['rows'], 'Manifest exclusions rows')
    for name, expected_files in [('DATA_SHA256SUMS', [f['derived']['file'] for f in m['files']]),
                                 ('METADATA_SHA256SUMS', [f['mapping']['file'] for f in m['files']] + ['excluded_rows.jsonl', 'manifest.json'])]:
        actual_files = []
        for line in (folder / name).read_text().splitlines():
            h, file = line.split('  ', 1); actual_files.append(file)
            require(sha(folder / file) == h, 'Checksum mismatch')
        require(actual_files == expected_files, 'Checksum coverage')
    overlaps = {}
    for left, right in [('train', 'validation'), ('sample_train', 'train'), ('sample_train', 'validation')]:
        overlaps[left + '__' + right] = {'exact_prompt': len(prompts[left] & prompts[right]), 'exact_pair': len(pairs[left] & pairs[right])}
    require(overlaps['train__validation'] == {'exact_prompt': 0, 'exact_pair': 0}, 'Train/validation leakage')
    require(pairs['sample_train'] <= pairs['train'], 'Sample containment')
    return {'status': 'PASS', 'manifest_sha256': sha(folder / 'manifest.json'), 'files': summaries,
            'overlaps': overlaps, 'sample_pair_subset_of_train': True,
            'limits': 'Exact equality only; near-duplicate/semantic benchmark contamination and human admission PENDING.'}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--dataset', type=Path, required=True)
    p.add_argument('--raw-dir', type=Path, required=True)
    p.add_argument('--a1', type=Path, required=True)
    p.add_argument('--report', type=Path, required=True)
    a = p.parse_args()
    # Exclusive create before verification; refusal cannot overwrite any evidence.
    with a.report.open('x') as stream:
        try:
            result = verify_bundle(a.dataset, a.raw_dir, a.a1)
        except Exception as exc:
            result = {'status': 'FAIL', 'error': f'{type(exc).__name__}: {exc}'}
        result.update(finished_at=datetime.now(timezone.utc).isoformat(), command=[sys.executable, *sys.argv], verifier_sha256=sha(Path(__file__)))
        json.dump(result, stream, indent=2); stream.write('\n')
    print(json.dumps(result, indent=2))
    return 0 if result['status'] == 'PASS' else 1


if __name__ == '__main__':
    sys.exit(main())
