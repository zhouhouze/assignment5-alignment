import importlib.util
from pathlib import Path

import pytest


SPEC = importlib.util.spec_from_file_location('v2', Path(__file__).resolve().parents[1] / 'scripts/derive_qwen_sft_v2.py')
v2 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(v2)


def test_exact_one_byte_preservation_and_boundary(tmp_path):
    src = tmp_path / 'source'
    src.write_bytes(b'{"a": 1}\n{"a":2}  \n{"a":3}\n')
    dest = tmp_path / 'dest'
    assert v2.copy_excluding(src, dest, 2) == 2
    assert dest.read_bytes() == b'{"a": 1}\n{"a":3}\n'
    assert src.read_bytes() == b'{"a": 1}\n{"a":2}  \n{"a":3}\n'
    with pytest.raises(FileExistsError):
        v2.copy_excluding(src, dest, 2)
    with pytest.raises(ValueError):
        v2.copy_excluding(src, tmp_path / 'outside', 4)


def test_mapping_source_one_based_and_prior_exclusion(tmp_path, monkeypatch):
    monkeypatch.setattr(v2, 'TARGET_RAW', 4)
    src = tmp_path / 'old.tsv'
    src.write_text('source_line\tderived_line\n1\t1\n2\t0\n3\t2\n4\t3\n5\t4\n')
    dest = tmp_path / 'new.tsv'
    assert v2.remap(src, dest, 3) == 5
    assert dest.read_text() == 'source_line\tderived_line\n1\t1\n2\t0\n3\t2\n4\t0\n5\t3\n'
    with pytest.raises(FileExistsError):
        v2.remap(src, dest, 3)


def test_wrong_target_mapping_stops(tmp_path, monkeypatch):
    monkeypatch.setattr(v2, 'TARGET_RAW', 2)
    src = tmp_path / 'old.tsv'
    src.write_text('source_line\tderived_line\n1\t1\n2\t3\n')
    with pytest.raises(ValueError, match='Target mapping moved'):
        v2.remap(src, tmp_path / 'new.tsv', 2)


def test_existing_output_directory_stops_before_identity_check(tmp_path, monkeypatch):
    import sys
    monkeypatch.setattr(sys, 'argv', ['derive_qwen_sft_v2.py', '--output', str(tmp_path)])
    with pytest.raises(ValueError, match='Output exists'):
        v2.main()
