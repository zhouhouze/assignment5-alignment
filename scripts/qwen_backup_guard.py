"""Run one explicitly supplied command; stop only its process group on stale backup.

No experiment is selected automatically. A local-verified backup acknowledgment
must identify this run's manifest. SIGTERM/SIGKILL may leave a partial runner
attempt: retain raw and use the runner's explicit recovery after inspection.
"""
import argparse
from datetime import datetime
import hashlib
import json
import math
import os
from pathlib import Path
import signal
import subprocess
import time


def healthy(ack_path, run_dir, max_age):
    ack = json.loads(Path(ack_path).read_text())
    age = time.time()-datetime.fromisoformat(ack['verified_at']).timestamp()
    expected = hashlib.sha256((Path(run_dir)/'manifest.json').read_bytes()).hexdigest()
    if ack['source'] != str(Path(run_dir).resolve()) or ack['source_manifest_sha256'] != expected or age > max_age or age < -30:
        raise ValueError(f'Backup acknowledgment invalid/stale: age={age:.1f}s')


def guard(ack, run_dir, command, max_age=180, poll=5, grace=30):
    healthy(ack, run_dir, max_age)
    child = subprocess.Popen(command, start_new_session=True)
    try:
        while child.poll() is None:
            healthy(ack, run_dir, max_age)
            time.sleep(poll)
        return child.returncode
    except BaseException:
        if child.poll() is None:
            os.killpg(child.pid, signal.SIGTERM)
            try:
                child.wait(timeout=grace)
            except subprocess.TimeoutExpired:
                os.killpg(child.pid, signal.SIGKILL)
                child.wait()
        raise


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--ack-file', required=True); p.add_argument('--run-dir', required=True)
    p.add_argument('--max-age', type=float, default=180); p.add_argument('--poll', type=float, default=5)
    p.add_argument('command', nargs=argparse.REMAINDER)
    args = p.parse_args()
    command = args.command[1:] if args.command[:1] == ['--'] else args.command
    if not command or any(not math.isfinite(x) or x <= 0 for x in (args.max_age, args.poll)):
        p.error('Command and positive finite time limits required')
    def interrupted(signum, frame):
        raise KeyboardInterrupt(f'Guard interrupted by signal {signum}')
    signal.signal(signal.SIGTERM, interrupted)
    signal.signal(signal.SIGHUP, interrupted)
    raise SystemExit(guard(args.ack_file, args.run_dir, command, args.max_age, args.poll))


if __name__ == '__main__':
    main()
