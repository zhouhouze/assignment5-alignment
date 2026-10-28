"""P2-A.2: derive immutable v1 files by excluding only Policy v1 empty fields.

Inputs: pinned A.1 evidence, Raw files and frozen policy. Outputs in a NEW
external directory: byte-preserved JSONL, complete TSV mappings, exclusions,
manifest and separate data/metadata checksums. Partial failures are retained.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys
from datetime import datetime, timezone
from validate_qwen_sft_raw import (ROOT, POLICY, REFERENCES, HardStop, digest,
                                  classify, reject_constant, validate_file,
                                  create_output, write_json, git)

A1 = 'artifacts/pa5-supplement-qwen/sft/20261028-p2a1-raw/raw-verification.json'
A1_SHA = 'c81445523482acc5f1894c1ceab394850b8836720c98fd1b972a3653c9f559fc'


def inventory(path, rows):
    return {'file': path.name, 'sha256': digest(path), 'bytes': path.stat().st_size, 'rows': rows}


def derive_split(raw, out, previous):
    """Revalidate A.1 evidence, then preserve retained physical lines verbatim.

    Mapping TSV has one row per source line: source_line, derived_line (0 if
    excluded). Source SHA and split in the manifest identify every mapping row.
    """
    split = previous['split']
    fresh = validate_file(raw, split, previous['sha256'], previous['bytes'],
                          previous['physical_lines'], previous['unique_anomaly_rows'])
    for key in ('anomalies', 'reason_counts', 'nonempty_rows'):
        if fresh[key] != previous[key]:
            raise HardStop(f'{split}: A.1 disagreement: {key}')
    derived = out / (split + '.jsonl')
    mapping = out / (split + '.mapping.tsv')
    excluded = []
    n = 0
    source_hash = hashlib.sha256()
    with raw.open('rb') as source, derived.open('xb') as dest, mapping.open('x') as maps:
        maps.write('source_line\tderived_line\n')
        for line, data in enumerate(source, 1):
            source_hash.update(data)
            reasons = classify(json.loads(data.decode('utf-8'), parse_constant=reject_constant))
            if reasons:
                excluded.append({'source_row_id': f'{fresh["sha256"]}:{split}:{line}',
                                 'source_file_sha256': fresh['sha256'], 'source_file': raw.name,
                                 'split': split, 'line_number': line, 'reasons': reasons})
                maps.write(f'{line}\t0\n')
            else:
                n += 1
                dest.write(data)
                maps.write(f'{line}\t{n}\n')
    if source_hash.hexdigest() != fresh['sha256'] or digest(raw) != fresh['sha256']:
        raise HardStop(f'{split}: Raw changed')
    if excluded != fresh['anomalies'] or n + len(excluded) != fresh['physical_lines']:
        raise HardStop(f'{split}: derivation accounting mismatch')
    return {'split': split, 'source_file': raw.name, 'source_sha256': fresh['sha256'],
            'source_rows': fresh['physical_lines'], 'source_bytes': fresh['bytes'],
            'excluded_rows': len(excluded), 'derived': inventory(derived, n),
            'mapping': inventory(mapping, fresh['physical_lines'])}, excluded


def checksums(out, name, files):
    with (out / name).open('x') as stream:
        for path in files:
            stream.write(digest(path) + '  ' + path.name + '\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    raw_dir = ROOT / 'data/qwen-sft-mirror/sft-instruct'
    # Full datasets belong outside the Git worktree, including resolved aliases.
    if args.output.resolve().is_relative_to(ROOT.resolve()):
        parser.error('Output must be outside the repository')
    try:
        out = create_output(args.output, raw_dir)
    except (OSError, HardStop) as exc:
        print('HARD STOP:', exc, file=sys.stderr)
        return 1
    state = {'gate': 'P2-A.2', 'status': 'PENDING', 'run_id': out.name,
             'started_at': datetime.now(timezone.utc).isoformat(), 'files': [],
             'rule_version': 'SFT Data Acceptance Policy v1', 'derived_version': 'derived-v1',
             'data_admission': 'PENDING', 'directly_comparable_to_official': False,
             'authorization': 'User authorized P2-A.2 CPU derivation, testing, verification and archival in this conversation; no P2-B/P3/training/GPU.',
             'command': [sys.executable, *sys.argv], 'python': sys.version, 'gpu_used': False}
    with (out / 'execution.txt').open('x') as log:
        def record(s):
            print(s, flush=True); log.write(s + '\n'); log.flush()
        try:
            state.update(execution_commit=git('rev-parse', 'HEAD'), git_branch=git('branch', '--show-current'),
                         git_status=git('status', '--porcelain'), rule_sha256=digest(ROOT / POLICY),
                         a1_sha256=digest(ROOT / A1), source_sha256=digest(__file__))
            if state['git_branch'] != 'learning/pa5-supplement' or state['a1_sha256'] != A1_SHA:
                raise HardStop('Branch/A.1 identity mismatch')
            previous = json.loads((ROOT / A1).read_text())
            if previous['status'] != 'PASS' or previous['policy_sha256'] != state['rule_sha256']:
                raise HardStop('Policy or A.1 status mismatch')
            excluded = []
            for f in previous['files']:
                filename, sha, size, lines, anomalies = REFERENCES[f['split']]
                if (f['sha256'], f['bytes'], f['physical_lines'], f['unique_anomaly_rows']) != (sha, size, lines, anomalies):
                    raise HardStop('A.1 reference mismatch')
                record('START ' + f['split'])
                result, rows = derive_split(raw_dir / filename, out, f)
                state['files'].append(result); excluded.extend(rows)
                record(f'DERIVED {f["split"]}: {result["derived"]}')
            with (out / 'excluded_rows.jsonl').open('x') as stream:
                for row in excluded:
                    stream.write(json.dumps(row, sort_keys=True) + '\n')
            state['exclusions'] = inventory(out / 'excluded_rows.jsonl', len(excluded))
            state['status'] = 'GENERATED_PENDING_INDEPENDENT_VERIFICATION'
            state['finished_at'] = datetime.now(timezone.utc).isoformat()
            write_json(out / 'manifest.json', state)
            checksums(out, 'DATA_SHA256SUMS', [out / f['derived']['file'] for f in state['files']])
            checksums(out, 'METADATA_SHA256SUMS', [out / f['mapping']['file'] for f in state['files']] + [out / 'excluded_rows.jsonl', out / 'manifest.json'])
            record(state['status'])
            return 0
        except Exception as exc:
            state.update(status='FAIL', error=f'{type(exc).__name__}: {exc}', finished_at=datetime.now(timezone.utc).isoformat())
            write_json(out / 'failure.json', state)
            record('HARD STOP ' + state['error'])
            return 1


if __name__ == '__main__':
    sys.exit(main())
