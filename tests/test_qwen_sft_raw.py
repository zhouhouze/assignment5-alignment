"""Synthetic Raw verification contracts, independent of model/tokenizer assets."""
import hashlib
import importlib.util
import json
from pathlib import Path
import pytest

spec = importlib.util.spec_from_file_location('raw_validator', Path(__file__).resolve().parents[1] / 'scripts/validate_qwen_sft_raw.py')
v = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v)


@pytest.mark.parametrize('text,kind', [('', 'empty'), (' ', 'whitespace_only'), ('\t\r\n', 'whitespace_only'), ('\u00a0\u2003\u3000', 'whitespace_only')])
@pytest.mark.parametrize('field', ['prompt', 'response'])
def test_classification(text, kind, field):
    value = {'prompt': 'p', 'response': 'r'}
    value[field] = text
    assert v.classify(value) == [kind + '_' + field]


def fixture_file(tmp_path, data):
    path = tmp_path / 'raw.jsonl'
    path.write_bytes(data)
    return path, hashlib.sha256(data).hexdigest(), len(data)


def test_counts_identity_and_preservation(tmp_path):
    records = [{'prompt': '', 'response': '\t'}, {'prompt': '  p\n', 'response': '\tr  '}, {'prompt': '\u200b', 'response': 'x'}]
    data = '\n'.join(json.dumps(x) for x in records).encode()  # no final newline
    path, sha, size = fixture_file(tmp_path, data)
    result = v.validate_file(path, 'train', sha, size, 3, 1)
    assert result['reason_counts'] == dict(empty_prompt=1, whitespace_only_prompt=0, empty_response=0, whitespace_only_response=1)
    assert result['unique_anomaly_rows'] == 1
    assert result['nonempty_rows'] + result['unique_anomaly_rows'] == result['physical_lines'] == 3
    assert result['anomalies'][0]['source_row_id'] == sha + ':train:1'
    assert result['anomalies'][0]['line_number'] == 1
    assert path.read_bytes() == data
    assert v.classify(records[1]) == []
    assert records[1] == {'prompt': '  p\n', 'response': '\tr  '}


@pytest.mark.parametrize('data', [b'{bad}\n', b'[]\n', b'{}\n', b'{"prompt":"x"}\n', b'{"prompt":null,"response":"r"}\n', b'{"prompt":"p","response":5}\n', b'\n', b'\xff\n', b'{"prompt":"p","response":"r","x":NaN}\n'])
def test_schema_hard_stop(tmp_path, data):
    path, sha, size = fixture_file(tmp_path, data)
    with pytest.raises(v.HardStop, match='physical line 1'):
        v.validate_file(path, 'train', sha, size, 1)


def test_sha_checked_before_parsing(tmp_path):
    path, _, size = fixture_file(tmp_path, b'bad JSON')
    with pytest.raises(v.HardStop, match='SHA mismatch'):
        v.validate_file(path, 'train', '0' * 64, size, 1)


@pytest.mark.parametrize('size_delta,line_delta,anomalies', [(1, 0, 0), (0, 1, 0), (0, 0, 1)])
def test_reference_disagreement(tmp_path, size_delta, line_delta, anomalies):
    path, sha, size = fixture_file(tmp_path, b'{"prompt":"p","response":"r"}\n')
    with pytest.raises(v.HardStop, match='mismatch'):
        v.validate_file(path, 'train', sha, size + size_delta, 1 + line_delta, anomalies)


def test_no_output_overwrite_or_raw_destination(tmp_path):
    raw = tmp_path / 'raw'
    raw.mkdir()
    out = v.create_output(tmp_path / 'out', raw)
    marker = out / 'evidence'
    marker.write_text('keep')
    with pytest.raises(FileExistsError):
        v.create_output(out, raw)
    with pytest.raises(v.HardStop):
        v.create_output(raw / 'nested', raw)
    link = tmp_path / 'alias'
    link.symlink_to(raw, target_is_directory=True)
    with pytest.raises(v.HardStop):
        v.create_output(link / 'nested', raw)
    assert marker.read_text() == 'keep'
    assert list(raw.iterdir()) == []
