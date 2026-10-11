"""CPU-only, file-level incremental backup over an already authenticated SSH link.

Committed raw must use the runner's sealed one-record JSONL. During generation,
capture raw before attempt metadata, and defer changing mutable logs/progress.
Only --quiescent takes the runner lock and includes finalized bundles. A live
snapshot is a recoverable prefix, not a transactionally consistent final run.
No model imports, credentials, deletion, or in-place rewriting of backup objects.
"""
import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import gzip
import hashlib
import io
import json
import math
import os
from pathlib import Path, PurePosixPath
import shlex
import stat
import subprocess
import sys
import tarfile
import tempfile
import time
import uuid


def now():
    return datetime.now(timezone.utc).isoformat()


def sha(data):
    return hashlib.sha256(data).hexdigest()


def digest_file(path):
    with Path(path).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def sync_dir(path):
    fd = os.open(path, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def mkdir_durable(path):
    """Persist new directory entries before publishing files below them."""
    path = Path(path)
    if not path.exists():
        mkdir_durable(path.parent)
        try:
            path.mkdir()
        except FileExistsError:
            pass
    # Also covers a directory left by an earlier interrupted mkdir/fsync.
    sync_dir(path.parent)


def atomic(path, data, replace=False):
    path = Path(path)
    mkdir_durable(path.parent)
    fd, temp = tempfile.mkstemp(prefix='.pending-', dir=path.parent)
    with os.fdopen(fd, 'wb') as f:
        f.write(data)
        f.flush()
        os.fsync(f.fileno())
    if replace:
        os.replace(temp, path)
    else:
        os.link(temp, path)
        os.unlink(temp)
    sync_dir(path.parent)


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False)+'\n').encode()


@contextmanager
def lock(path):
    path = Path(path)
    mkdir_durable(path.parent)
    with path.open('a') as f:
        fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield


def allowed(name, quiescent):
    p = PurePosixPath(name)
    if p.is_absolute() or '..' in p.parts or not p.parts:
        return False
    if any(x.startswith('.') and not (quiescent and x.startswith(('.pending-', '.finalizing-'))) for x in p.parts):
        return False
    return name in ('manifest.json', 'manifest.sha256', 'selected_examples.json', 'input-check.json', 'progress.json') or p.parts[0] in (
        ('raw', 'attempts', 'recoveries', 'logs', 'finalized') if quiescent else ('raw', 'attempts', 'recoveries', 'logs')) or (
        quiescent and p.parts[0].startswith(('.pending-', '.finalizing-')))


def committed_raw(name):
    return name.startswith('raw/') and not any(x.startswith('.') for x in PurePosixPath(name).parts)


def immutable(name):
    return name != 'progress.json' and not name.startswith('logs/') and not any(
        x.startswith(('.pending-', '.finalizing-')) for x in PurePosixPath(name).parts)


def sealed(data):
    if not data.endswith(b'\n') or len(data.splitlines()) != 1:
        raise ValueError('Raw framing is corrupt')
    value = json.loads(data)
    stored = value.pop('record_sha256', None)
    canonical = json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode()
    if sha(canonical) != stored:
        raise ValueError('Raw payload seal is corrupt')


def stable_read(path):
    """Detect replace/append/truncate during capture; never follow a symlink."""
    before = path.lstat()
    if not stat.S_ISREG(before.st_mode):
        raise ValueError(f'Not a regular file: {path}')
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(fd, 'rb') as f:
        data = f.read()
        after_fd = os.fstat(f.fileno())
    after = path.lstat()
    signature = lambda s: (s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns)
    if signature(before) != signature(after_fd) or signature(before) != signature(after):
        return None
    return data


def export_run(root, known, stream, quiescent=False):
    """Export a manifest plus only new content; read-only except runner lock."""
    root = Path(root).resolve()
    if not (root/'manifest.json').is_file():
        raise ValueError('Missing source manifest')
    if quiescent:
        with lock(root/'.runner.lock'):
            return _export(root, known, stream, quiescent)
    return _export(root, known, stream, quiescent)


def _export(root, known, stream, quiescent):
    files, deferred, skipped = {}, [], []
    with tempfile.TemporaryDirectory(prefix='pa5-backup-export-') as scratch:
        scratch = Path(scratch)
        # Raw-first order ensures its already-published intent is scanned later.
        paths = sorted((root/'raw').glob('*'))
        paths += [p for p in sorted(root.rglob('*')) if 'raw' != p.relative_to(root).parts[0]]
        for p in paths:
            name = p.relative_to(root).as_posix()
            if p.is_symlink():
                raise ValueError(f'Symlink rejected: {name}')
            if not p.is_file():
                continue
            if not allowed(name, quiescent):
                skipped.append(name)
                continue
            try:
                data = stable_read(p)
            except FileNotFoundError:
                data = None
            if data is None:
                if immutable(name) or quiescent:
                    raise ValueError(f'Immutable/quiescent source changed: {name}')
                deferred.append(name)
                continue
            if committed_raw(name):
                sealed(data)
            checksum = sha(data)
            if immutable(name) and name in known and known[name]['sha256'] != checksum:
                raise ValueError(f'Immutable source changed: {name}')
            files[name] = dict(sha256=checksum, bytes=len(data))
            if name not in known or known[name] != files[name]:
                obj = scratch/checksum
                if not obj.exists():
                    obj.write_bytes(data)
        for name, value in known.items():
            if allowed(name, quiescent) and immutable(name) and name not in files:
                raise ValueError(f'Previously committed source missing: {name}')
        for required in ('manifest.json', 'manifest.sha256', 'selected_examples.json'):
            if required not in files:
                raise ValueError(f'Missing required source: {required}')
        # Recheck the immutable experiment identity even on the initial cycle.
        if (root/'manifest.sha256').read_text().strip() != files['manifest.json']['sha256']:
            raise ValueError('Source manifest checksum mismatch')
        manifest = dict(schema=1, snapshot_id=uuid.uuid4().hex, captured_at=now(), source=str(root),
            quiescent=quiescent, files=files, deferred=deferred, skipped=skipped,
            raw_count=sum(committed_raw(n) for n in files), mode='BACKUP_ONLY_NO_GENERATION')
        with tarfile.open(fileobj=stream, mode='w|gz') as tar:
            data = json_bytes(manifest)
            info = tarfile.TarInfo('snapshot.json'); info.size = len(data)
            tar.addfile(info, io.BytesIO(data))
            for obj in sorted(scratch.iterdir()):
                tar.add(obj, arcname='objects/'+obj.name, recursive=False)
        return manifest


def object_path(store, checksum):
    if len(checksum) != 64 or any(c not in '0123456789abcdef' for c in checksum):
        raise ValueError('Invalid object checksum')
    return Path(store)/'objects'/checksum[:2]/checksum[2:]


def latest(store, max_age=None):
    store = Path(store)
    pointer = json.loads((store/'LATEST.json').read_text())
    path = store/'snapshots'/(pointer['snapshot_id']+'.json')
    if digest_file(path) != pointer['sha256']:
        raise ValueError('Snapshot manifest checksum mismatch')
    value = json.loads(path.read_text())
    for name, item in value['files'].items():
        if not allowed(name, value['quiescent']):
            raise ValueError('Unsafe snapshot path')
        p = object_path(store, item['sha256'])
        if p.stat().st_size != item['bytes'] or digest_file(p) != item['sha256']:
            raise ValueError(f'Backup object corrupt: {name}')
    age = time.time()-datetime.fromisoformat(pointer['verified_at']).timestamp()
    if max_age is not None and (age > max_age or age < -30):
        raise ValueError(f'Backup stale: age {age:.1f}s')
    return value, pointer


def import_archive(store, archive):
    store = Path(store)
    # Consume gzip to its end so truncated streams / CRC errors cannot publish.
    with gzip.open(archive, 'rb') as f:
        while f.read(1024*1024):
            pass
    previous = latest(store)[0] if (store/'LATEST.json').exists() else None
    copied = 0
    with tarfile.open(archive, 'r:gz') as tar:
        members = tar.getmembers()
        if not members or members[0].name != 'snapshot.json' or not all(m.isfile() for m in members):
            raise ValueError('Invalid archive members')
        if len({m.name for m in members}) != len(members):
            raise ValueError('Duplicate archive member')
        value = json.load(tar.extractfile(members[0]))
        if value['schema'] != 1 or not value['files'] or len(value['snapshot_id']) != 32 or not value['snapshot_id'].isalnum():
            raise ValueError('Invalid snapshot identity')
        if previous and value['source'] != previous['source']:
            raise ValueError('Backup source identity changed')
        for name, item in value['files'].items():
            if not allowed(name, value['quiescent']):
                raise ValueError('Unsafe snapshot path')
            if previous and immutable(name) and name in previous['files'] and previous['files'][name] != item:
                raise ValueError('Immutable backup drift')
        if previous:
            for name in previous['files']:
                if allowed(name, value['quiescent']) and immutable(name) and name not in value['files']:
                    raise ValueError('Immutable backup deletion')
        expected = {i['sha256']: i['bytes'] for i in value['files'].values()}
        for member in members[1:]:
            checksum = member.name.removeprefix('objects/')
            if member.name != 'objects/'+checksum or checksum not in expected or member.size != expected[checksum]:
                raise ValueError('Unexpected archive object')
            data = tar.extractfile(member).read()
            if sha(data) != checksum:
                raise ValueError('Transfer checksum mismatch')
            p = object_path(store, checksum)
            if p.exists():
                if digest_file(p) != checksum:
                    raise ValueError('Existing backup object corrupt')
            else:
                atomic(p, data)
                copied += 1
        for item in value['files'].values():
            p = object_path(store, item['sha256'])
            if not p.is_file() or p.stat().st_size != item['bytes'] or digest_file(p) != item['sha256']:
                raise ValueError('Missing/corrupt referenced object')
    data = json_bytes(value)
    atomic(store/'snapshots'/(value['snapshot_id']+'.json'), data)
    pointer = dict(snapshot_id=value['snapshot_id'], sha256=sha(data), verified_at=now(),
        source=value['source'], source_manifest_sha256=value['files']['manifest.json']['sha256'], raw_count=value['raw_count'])
    atomic(store/'LATEST.json', json_bytes(pointer), replace=True)
    return dict(**pointer, copied_objects=copied, files=len(value['files']), deferred=value['deferred'],
        quiescent=value['quiescent'], transfer_bytes=Path(archive).stat().st_size)


def restore(store, destination):
    value, _ = latest(store)
    destination = Path(destination)
    mkdir_durable(destination.parent)
    destination.mkdir(exist_ok=False)
    sync_dir(destination.parent)
    # Failure retains a partial destination; never use it as a validated run.
    for name, item in value['files'].items():
        atomic(destination/name, object_path(store, item['sha256']).read_bytes())
    for name in ('raw', 'attempts', 'recoveries', 'finalized', 'logs'):
        mkdir_durable(destination/name)
    for name, item in value['files'].items():
        if digest_file(destination/name) != item['sha256']:
            raise ValueError('Restore verification failed')
    return dict(status='RESTORED_SHA256_VERIFIED', files=len(value['files']), raw_count=value['raw_count'],
        snapshot_id=value['snapshot_id'], destination=str(destination), runner_validation='REQUIRED_SEPARATELY')


def event(store, status, **fields):
    data = json_bytes(dict(at=now(), status=status, **fields))
    with (Path(store)/'backup-events.jsonl').open('ab') as f:
        f.write(data); f.flush(); os.fsync(f.fileno())
    sync_dir(store)
    print(data.decode().strip(), flush=True)


def ssh_command(args, action):
    parts = [args.remote_python, args.remote_script, action, '--run-dir', args.run_dir]
    if action == 'export' and args.quiescent:
        parts.append('--quiescent')
    if action == 'ack':
        parts += ['--ack-path', args.ack_path]
    return ['ssh', '-F', '/dev/null', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=10',
        '-o', 'ServerAliveInterval=15', '-o', 'ServerAliveCountMax=2', '-S', args.control_path,
        '-p', str(args.port), args.host, shlex.join(parts)]


def pull(args):
    store = Path(args.store); mkdir_durable(store)
    with lock(store/'.backup.lock'):
        count = 0
        while args.cycles == 0 or count < args.cycles:
            incoming = store/('incoming-'+uuid.uuid4().hex+'.tar.gz')
            error_path = store/(incoming.stem+'.stderr.txt')
            try:
                event(store, 'START', cycle=count+1)
                known = latest(store)[0]['files'] if (store/'LATEST.json').exists() else {}
                tick = time.monotonic()
                with incoming.open('xb') as out, error_path.open('xb') as err:
                    subprocess.run(ssh_command(args, 'export'), input=json_bytes(known), stdout=out, stderr=err,
                        timeout=args.timeout, check=True)
                    out.flush(); os.fsync(out.fileno())
                result = import_archive(store, incoming)
                if args.ack_path:
                    subprocess.run(ssh_command(args, 'ack'), input=json_bytes(result), capture_output=True,
                        timeout=30, check=True)
                event(store, 'SUCCESS', elapsed_seconds=time.monotonic()-tick, **result)
                incoming.unlink()  # verified transport envelope only; objects/snapshots are retained
                count += 1
            except BaseException as exc:
                for path in (incoming, error_path):
                    if path.is_file():
                        with path.open('rb') as f:
                            os.fsync(f.fileno())
                event(store, 'FAILED', error_type=type(exc).__name__, error=str(exc),
                    retained_incoming=str(incoming), stderr_path=str(error_path))
                raise
            if args.cycles == 0 or count < args.cycles:
                time.sleep(args.interval)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='action', required=True)
    export = sub.add_parser('export'); export.add_argument('--run-dir', required=True); export.add_argument('--quiescent', action='store_true')
    ack = sub.add_parser('ack'); ack.add_argument('--run-dir', required=True); ack.add_argument('--ack-path', required=True)
    for action in ('status', 'restore'):
        parser = sub.add_parser(action); parser.add_argument('--store', required=True)
        if action == 'status': parser.add_argument('--max-age', type=float)
        else: parser.add_argument('--destination', required=True)
    parser = sub.add_parser('pull')
    for flag in ('host', 'control-path', 'remote-python', 'remote-script', 'run-dir', 'store'):
        parser.add_argument('--'+flag, required=True)
    parser.add_argument('--port', type=int, required=True)
    parser.add_argument('--interval', type=float, default=60)
    parser.add_argument('--cycles', type=int, default=1)
    parser.add_argument('--timeout', type=float, default=180)
    parser.add_argument('--quiescent', action='store_true')
    parser.add_argument('--ack-path')
    args = p.parse_args()
    if args.action == 'export': export_run(args.run_dir, json.load(sys.stdin), sys.stdout.buffer, args.quiescent)
    elif args.action == 'pull':
        if args.cycles < 0 or not math.isfinite(args.interval) or args.interval <= 0 or not math.isfinite(args.timeout) or args.timeout <= 0:
            p.error('Positive finite interval/timeout and nonnegative cycles required')
        pull(args)
    elif args.action == 'restore': print(json.dumps(restore(args.store, args.destination)))
    elif args.action == 'status': print(json.dumps(latest(args.store, args.max_age)[1]))
    elif args.action == 'ack':
        root, target = Path(args.run_dir).resolve(), Path(args.ack_path).resolve()
        if target.is_relative_to(root): raise ValueError('Acknowledgment must be outside run directory')
        value = json.load(sys.stdin)
        if value['source'] != str(root) or value['source_manifest_sha256'] != digest_file(root/'manifest.json'):
            raise ValueError('Acknowledgment source mismatch')
        atomic(target, json_bytes(value), replace=True)


if __name__ == '__main__':
    main()
