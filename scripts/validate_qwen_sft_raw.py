"""P2-A.1 CPU Raw verification only; never writes training data.

Input: immutable JSONL and pinned SHA/bytes/physical-row expectations.
Output: measured counts and source-fingerprinted anomaly rows. Schema or
identity disagreement stops the run; existing output directories are refused.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
POLICY = 'notes/experiments/SUP-QWEN-data-flywheel/sft-data-quality-plan.md'
# SHA: frozen Policy v1; bytes/rows/anomalies: archived acceptance-v2.
REFERENCES = {
    'train': ('train.jsonl', '3b72228a7976079a5c5a30249fd3289179ad01006cbb67d15c7c366d4fd25913', 532421064, 210348, 22),
    'validation': ('test.jsonl', 'ce84dd834a7bbfc622cb3b50dc6c233e7dd91e002fd84f7cf86f70762a2c9ed9', 58872258, 23110, 2),
    'sample_train': ('sample_train.jsonl', 'b26bbe382793889ccb397e7c8afdf64ad3e52f0109d191e66c424587fba596df', 2492043, 1000, 0),
}
REASONS = ('empty_prompt', 'whitespace_only_prompt', 'empty_response', 'whitespace_only_response')


class HardStop(ValueError):
    pass


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def classify(value):
    """Validate required string fields; return reasons without mutating value."""
    if not isinstance(value, dict):
        raise HardStop('schema: not_object')
    reasons = []
    for field in ('prompt', 'response'):
        if field not in value:
            raise HardStop('schema: missing_' + field)
        if not isinstance(value[field], str):
            raise HardStop('schema: non_string_' + field)
        if value[field] == '':
            reasons.append('empty_' + field)
        elif value[field].strip() == '':
            reasons.append('whitespace_only_' + field)
    return reasons


def reject_constant(value):
    raise ValueError('non-JSON constant: ' + value)


def validate_file(path, split, expected_sha, expected_bytes, expected_lines,
                  expected_anomalies=None):
    """Read only; verify SHA before parsing and scanned bytes against that SHA.

    Counts are measured, then compared to references. A final hash also checks
    the path after scanning. No filtered records or normalized text are saved.
    """
    path = Path(path)
    initial_sha = digest(path)
    if initial_sha != expected_sha:
        raise HardStop(f'{split}: SHA mismatch expected={expected_sha} actual={initial_sha}')
    counts = Counter({reason: 0 for reason in REASONS})
    anomalies = []
    scanned_hash = hashlib.sha256()
    size = lines = 0
    with path.open('rb') as stream:
        for lines, raw in enumerate(stream, 1):
            scanned_hash.update(raw)
            size += len(raw)
            try:
                value = json.loads(raw.decode('utf-8'), parse_constant=reject_constant)
                reasons = classify(value)
            except (ValueError, UnicodeError) as exc:
                raise HardStop(f'{split}: physical line {lines}: {exc}') from exc
            counts.update(reasons)
            if reasons:
                anomalies.append({
                    'source_row_id': f'{initial_sha}:{split}:{lines}',
                    'source_file_sha256': initial_sha, 'source_file': path.name,
                    'split': split, 'line_number': lines, 'reasons': reasons,
                })
    if scanned_hash.hexdigest() != initial_sha or digest(path) != initial_sha:
        raise HardStop(f'{split}: Raw changed during verification')
    if size != expected_bytes or lines != expected_lines:
        raise HardStop(f'{split}: bytes/lines mismatch actual={size}/{lines} expected={expected_bytes}/{expected_lines}')
    if expected_anomalies is not None and len(anomalies) != expected_anomalies:
        raise HardStop(f'{split}: anomaly count mismatch actual={len(anomalies)} expected={expected_anomalies}')
    return {
        'split': split, 'source_path': str(path.resolve()), 'sha256': initial_sha,
        'bytes': size, 'physical_lines': lines, 'schema_status': 'PASS',
        'reason_counts': dict(counts), 'unique_anomaly_rows': len(anomalies),
        'nonempty_rows': lines - len(anomalies), 'raw_unchanged': True,
        'anomalies': anomalies,
    }


def create_output(path, raw_dir):
    path, raw_dir = Path(path).absolute(), Path(raw_dir).resolve()
    resolved = path.resolve()
    if resolved == raw_dir or resolved.is_relative_to(raw_dir):
        raise HardStop('Output must be outside Raw directory')
    path.mkdir(parents=True, exist_ok=False)
    return path


def write_json(path, value):
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT, text=True).strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    raw_dir = ROOT / 'data/qwen-sft-mirror/sft-instruct'
    try:
        out = create_output(args.output, raw_dir)
    except (OSError, HardStop) as exc:
        print(f'HARD STOP: {exc}', file=sys.stderr)
        return 1
    report = {
        'gate': 'P2-A.1', 'status': 'PENDING', 'run_id': out.name,
        'started_at': datetime.now(timezone.utc).isoformat(),
        'command': [sys.executable, *sys.argv], 'python': sys.version,
        'platform': platform.platform(), 'gpu_used': False,
        'directly_comparable_to_official': False,
        'dataset_repo': 'garg-aayush/sft-cs336-assign5-datasets',
        'dataset_revision': 'ac710ef808346bf458d7b093bfe4586cb15699d9',
        'derived_created': False, 'data_admission': 'PENDING', 'files': [],
    }
    with (out / 'execution.log').open('x', encoding='utf-8') as log:
        def record(message):
            log.write(message + '\n')
            log.flush()
            print(message, flush=True)
        try:
            report.update(git_branch=git('branch', '--show-current'),
                          execution_commit=git('rev-parse', 'HEAD'),
                          git_status=git('status', '--porcelain', '--untracked-files=normal'),
                          source_sha256=digest(__file__), policy_sha256=digest(ROOT / POLICY))
            report['references'] = REFERENCES
            if report['git_branch'] != 'learning/pa5-supplement':
                raise HardStop('Wrong execution branch')
            policy = (ROOT / POLICY).read_text()
            for split, (filename, sha, size, rows, anomalies) in REFERENCES.items():
                if sha not in policy:
                    raise HardStop(f'{split}: reference SHA missing from frozen policy')
                record(f'START {split}')
                result = validate_file(raw_dir / filename, split, sha, size, rows, anomalies)
                report['files'].append(result)
                record(f'PASS {split}: bytes={result["bytes"]} rows={result["physical_lines"]} reasons={result["reason_counts"]} unique={result["unique_anomaly_rows"]}')
            report['status'] = 'PASS'
        except Exception as exc:
            report['status'] = 'FAIL'
            report['error'] = f'{type(exc).__name__}: {exc}'
            record('HARD STOP ' + report['error'])
        report['finished_at'] = datetime.now(timezone.utc).isoformat()
        write_json(out / 'raw-verification.json', report)
        record('P2-A.1=' + report['status'])
    return 0 if report['status'] == 'PASS' else 1


if __name__ == '__main__':
    sys.exit(main())
