"""P1B-0.5 backup failure tests; stdlib only, no inference or model imports."""
from datetime import datetime, timezone, timedelta
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts import qwen_artifact_backup as b
from scripts import qwen_backup_guard as g


class BackupTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)/'MOCK_TEST_ONLY'
        self.root.mkdir(); (self.root/'raw').mkdir()
        (self.root/'manifest.json').write_text('{"mode":"MOCK_TEST_ONLY"}\n')
        (self.root/'manifest.sha256').write_text(b.digest_file(self.root/'manifest.json')+'\n')
        (self.root/'selected_examples.json').write_text('[]\n')
        self.store = Path(self.temp.name)/'backup'
        self.row(1)

    def row(self, n):
        row = dict(example_id=str(n), raw_response='MOCK / TEST_ONLY', mode='MOCK_TEST_ONLY')
        canonical = json.dumps(row, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()
        b.atomic(self.root/'raw'/f'{n}.jsonl', b.json_bytes(dict(**row, record_sha256=b.sha(canonical))))

    def archive(self, known=None, quiescent=False):
        f = io.BytesIO()
        b.export_run(self.root, known or {}, f, quiescent)
        p = Path(self.temp.name)/('transport-'+str(time.time_ns())+'.gz')
        p.write_bytes(f.getvalue()); return p

    def test_roundtrip_and_incremental_no_duplicate_payload(self):
        first = b.import_archive(self.store, self.archive())
        known = b.latest(self.store)[0]['files']
        second = b.import_archive(self.store, self.archive(known))
        self.assertEqual(second['copied_objects'], 0)
        self.row(2)
        third = b.import_archive(self.store, self.archive(known))
        self.assertEqual(third['copied_objects'], 1)
        self.assertEqual(third['raw_count'], 2)
        dest = Path(self.temp.name)/'restore'
        self.assertEqual(b.restore(self.store, dest)['raw_count'], 2)
        self.assertEqual((dest/'raw/1.jsonl').read_bytes(), (self.root/'raw/1.jsonl').read_bytes())
        self.assertEqual(len(list((self.store/'snapshots').glob('*.json'))), 3)

    def test_pending_partial_write_is_not_committed(self):
        (self.root/'raw/.pending-incomplete').write_text('{"raw_response":')
        r = b.import_archive(self.store, self.archive())
        self.assertEqual(r['raw_count'], 1)
        self.assertIn('raw/.pending-incomplete', b.latest(self.store)[0]['skipped'])

    def test_quiescent_retains_pending_and_failed_finalization_as_evidence(self):
        (self.root/'raw/.pending-incomplete').write_text('{half-written')
        (self.root/'.finalizing-v1-failed').mkdir()
        (self.root/'.finalizing-v1-failed/metrics.json').write_text('{unfinished')
        result = b.import_archive(self.store, self.archive(quiescent=True))
        self.assertEqual(result['raw_count'], 1)
        dest = Path(self.temp.name)/'restore'
        b.restore(self.store, dest)
        self.assertEqual((dest/'raw/.pending-incomplete').read_text(), '{half-written')
        self.assertTrue((dest/'.finalizing-v1-failed/metrics.json').exists())

    def test_published_half_line_hard_stop(self):
        (self.root/'raw/1.jsonl').write_text('{broken')
        with self.assertRaisesRegex(ValueError, 'framing'): self.archive()

    def test_published_seal_corruption_hard_stop(self):
        p = self.root/'raw/1.jsonl'; p.write_text(p.read_text().replace('TEST_ONLY', 'CORRUPTED'))
        with self.assertRaisesRegex(ValueError, 'seal'): self.archive()

    def test_immutable_source_rewrite_detected(self):
        b.import_archive(self.store, self.archive())
        known = b.latest(self.store)[0]['files']
        p = self.root/'selected_examples.json'; p.write_text('[1]\n')
        with self.assertRaisesRegex(ValueError, 'Immutable source changed'): self.archive(known)

    def test_source_deletion_does_not_delete_backup(self):
        b.import_archive(self.store, self.archive())
        known = b.latest(self.store)[0]['files']; (self.root/'raw/1.jsonl').unlink()
        with self.assertRaisesRegex(ValueError, 'source missing'): self.archive(known)
        self.assertEqual(b.latest(self.store)[0]['raw_count'], 1)

    def test_mid_read_append_detected_by_stat(self):
        p = self.root/'progress.json'; p.write_text('{}')
        original = os.fdopen
        def changed(fd, *args, **kwargs):
            f = original(fd, *args, **kwargs)
            with p.open('a') as out: out.write(' ')
            return f
        with patch.object(b.os, 'fdopen', side_effect=changed):
            self.assertIsNone(b.stable_read(p))

    def test_changing_log_deferred_until_later_cycle(self):
        (self.root/'logs').mkdir(); (self.root/'logs/generation.log').write_text('first\n')
        original = b.stable_read
        with patch.object(b, 'stable_read', side_effect=lambda p: None if p.name.endswith('.log') else original(p)):
            result = b.import_archive(self.store, self.archive())
        self.assertEqual(result['deferred'], ['logs/generation.log'])
        b.import_archive(self.store, self.archive(b.latest(self.store)[0]['files']))
        self.assertIn('logs/generation.log', b.latest(self.store)[0]['files'])

    def test_changing_raw_hard_stop(self):
        original = b.stable_read
        with patch.object(b, 'stable_read', side_effect=lambda p: None if p.suffix=='.jsonl' else original(p)):
            with self.assertRaisesRegex(ValueError, 'source changed'): self.archive()

    def test_truncated_transfer_preserves_latest_then_resume(self):
        b.import_archive(self.store, self.archive())
        before = (self.store/'LATEST.json').read_bytes()
        known = b.latest(self.store)[0]['files']; self.row(2)
        transport = self.archive(known); data = transport.read_bytes()
        transport.write_bytes(data[:len(data)//2])
        with self.assertRaises((EOFError, OSError)): b.import_archive(self.store, transport)
        self.assertEqual(before, (self.store/'LATEST.json').read_bytes())
        result = b.import_archive(self.store, self.archive(known))
        self.assertEqual(result['copied_objects'], 1)

    def test_object_write_failure_preserves_last_snapshot(self):
        b.import_archive(self.store, self.archive()); self.row(2)
        before = (self.store/'LATEST.json').read_bytes()
        archive = self.archive(b.latest(self.store)[0]['files'])
        original = b.atomic
        def failure(path, data, **kwargs):
            if 'objects' in Path(path).parts: raise OSError('Injected disk full')
            return original(path, data, **kwargs)
        with patch.object(b, 'atomic', side_effect=failure):
            with self.assertRaisesRegex(OSError, 'disk full'): b.import_archive(self.store, archive)
        self.assertEqual(before, (self.store/'LATEST.json').read_bytes())
        self.assertEqual(b.import_archive(self.store, archive)['raw_count'], 2)

    def test_new_directory_entries_synced_before_file_publication(self):
        target = self.store/'objects/ab/example'
        synced = []
        original_sync, original_link = b.sync_dir, os.link
        def sync(path):
            synced.append(Path(path)); original_sync(path)
        def publish(source, dest):
            for path in (self.store.parent, self.store, self.store/'objects'):
                self.assertIn(path, synced)
            return original_link(source, dest)
        with patch.object(b, 'sync_dir', side_effect=sync), patch.object(b.os, 'link', side_effect=publish):
            b.atomic(target, b'CPU_TEST_ONLY')
        self.assertEqual(target.read_bytes(), b'CPU_TEST_ONLY')

    def test_failure_event_directory_is_synced(self):
        b.mkdir_durable(self.store)
        with patch.object(b, 'sync_dir', wraps=b.sync_dir) as sync, patch('builtins.print'):
            b.event(self.store, 'FAILED', error='CPU_TEST_ONLY')
        sync.assert_called_with(self.store)
        self.assertEqual(json.loads((self.store/'backup-events.jsonl').read_text())['status'], 'FAILED')

    def test_local_corruption_is_not_silently_repaired(self):
        b.import_archive(self.store, self.archive())
        value, _ = b.latest(self.store)
        p = b.object_path(self.store, value['files']['raw/1.jsonl']['sha256']); p.write_text('corrupt')
        with self.assertRaisesRegex(ValueError, 'object corrupt'): b.latest(self.store)

    def test_quiescent_lock_conflict(self):
        with b.lock(self.root/'.runner.lock'):
            with self.assertRaises(BlockingIOError): self.archive(quiescent=True)

    def test_finalize_only_in_quiescent_snapshot(self):
        (self.root/'finalized/v1').mkdir(parents=True)
        (self.root/'finalized/v1/metrics.json').write_text('{}')
        live = b.import_archive(self.store, self.archive())
        self.assertNotIn('finalized/v1/metrics.json', b.latest(self.store)[0]['files'])
        b.import_archive(self.store, self.archive(b.latest(self.store)[0]['files'], True))
        self.assertIn('finalized/v1/metrics.json', b.latest(self.store)[0]['files'])

    def test_symlink_rejected(self):
        (self.root/'raw/link.jsonl').symlink_to(self.root/'raw/1.jsonl')
        with self.assertRaisesRegex(ValueError, 'Symlink'): self.archive()

    def test_restore_never_overwrites_existing_destination(self):
        b.import_archive(self.store, self.archive())
        with self.assertRaises(FileExistsError): b.restore(self.store, self.root)

    def test_stale_and_corrupt_latest_detected(self):
        b.import_archive(self.store, self.archive())
        pointer = json.loads((self.store/'LATEST.json').read_text())
        pointer['verified_at'] = (datetime.now(timezone.utc)-timedelta(hours=1)).isoformat()
        (self.store/'LATEST.json').write_bytes(b.json_bytes(pointer))
        with self.assertRaisesRegex(ValueError, 'stale'): b.latest(self.store, 180)
        p = self.store/'snapshots'/(pointer['snapshot_id']+'.json'); p.write_text('{}')
        with self.assertRaisesRegex(ValueError, 'manifest checksum'): b.latest(self.store)

    def test_excludes_credentials_and_unsafe_paths(self):
        (self.root/'.env').write_text('TEST_ONLY_NOT_A_SECRET')
        b.import_archive(self.store, self.archive())
        self.assertNotIn('.env', b.latest(self.store)[0]['files'])
        self.assertFalse(b.allowed('../escape', True))
        self.assertFalse(b.allowed('/tmp/escape', True))

    def ack(self):
        p = Path(self.temp.name)/'ack.json'
        p.write_bytes(b.json_bytes(dict(source=str(self.root.resolve()),
            source_manifest_sha256=b.digest_file(self.root/'manifest.json'), verified_at=b.now())))
        return p

    def test_guard_rejects_missing_ack_before_spawn(self):
        with patch.object(g.subprocess, 'Popen') as spawn:
            with self.assertRaises(FileNotFoundError): g.guard('/missing-test-only', self.root, ['unused'])
            spawn.assert_not_called()

    def test_guard_normal_cpu_child(self):
        self.assertEqual(g.guard(self.ack(), self.root, [sys.executable, '-c', 'pass'], poll=.01), 0)

    def test_guard_stale_ack_stops_only_owned_cpu_process_group(self):
        ack = self.ack(); pidfile = Path(self.temp.name)/'child.pid'
        command = [sys.executable, '-c', f'import os,time; from pathlib import Path; Path({str(pidfile)!r}).write_text(str(os.getpid())); time.sleep(10)']
        with self.assertRaisesRegex(ValueError, 'stale'):
            g.guard(ack, self.root, command, max_age=.3, poll=.02, grace=.2)
        with self.assertRaises(ProcessLookupError): os.kill(int(pidfile.read_text()), 0)


if __name__ == '__main__':
    unittest.main()
