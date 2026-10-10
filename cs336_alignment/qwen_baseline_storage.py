"""Local POSIX durability helpers for the baseline runner (no model imports).

Committed JSONL is one sealed record per file. Temporary files are evidence,
never completed records. A local flock excludes concurrent writers; the target
filesystem must support fsync, hard links and atomic rename (not object storage).
"""
from contextlib import contextmanager
import fcntl
import hashlib
import json
import os
from pathlib import Path
import tempfile


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode()).hexdigest()


def fsync_dir(path):
    fd = os.open(path, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def atomic_text(path, text, *, replace=False):
    """fsync before publishing; exclusive link prevents overwriting immutable data.

On failure retain the .pending-* file for incident inspection. A failure after
link can leave a valid committed file as well; resume validates its content.
"""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix='.pending-', dir=path.parent)
    temporary = Path(temporary)
    with os.fdopen(fd, 'w', encoding='utf-8') as f:
        f.write(text)
        f.flush()
        os.fsync(f.fileno())
    if replace:
        os.replace(temporary, path)
    else:
        os.link(temporary, path)
        temporary.unlink()
    fsync_dir(path.parent)


def atomic_json(path, value, *, replace=False):
    atomic_text(path, json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n', replace=replace)


def commit_raw(path, row):
    value = {**row, 'record_sha256': digest(row)}
    atomic_text(path, json.dumps(value, ensure_ascii=False, allow_nan=False)+'\n')


def read_raw(path):
    """Verify exact single-line framing and canonical payload checksum."""
    data = path.read_bytes()
    try:
        if not data.endswith(b'\n') or len(data.splitlines()) != 1:
            raise ValueError('half-line/multiple lines')
        row = json.loads(data)
        if not isinstance(row, dict):
            raise ValueError('record is not an object')
        stored = row.pop('record_sha256', None)
        if stored != digest(row):
            raise ValueError('record checksum mismatch')
        return row
    except (ValueError, UnicodeError, TypeError) as exc:
        raise ValueError(f'{path}:1: corrupt JSONL: {exc}') from exc


@contextmanager
def run_lock(directory):
    with (directory/'.runner.lock').open('a') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise RuntimeError('Another writer holds the run lock') from exc
        try:
            yield
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)
