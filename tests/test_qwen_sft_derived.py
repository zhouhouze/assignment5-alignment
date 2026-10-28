"""Synthetic derivation and independent verification, no model imports."""
import importlib.util
import json
from pathlib import Path
import sys
import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts'
sys.path.insert(0, str(SCRIPTS))
import derive_qwen_sft as d
import verify_qwen_sft_derived as v


def make_bundle(tmp_path):
    raw = tmp_path / 'raw'; raw.mkdir()
    out = d.create_output(tmp_path / 'derived-v1', raw)
    # Keep duplicate prompts, extra fields and original whitespace; final line has no LF.
    examples = {
        'train': [{'prompt': ' p ', 'response': '\tr ', 'extra': [1, 2]}, {'prompt': '', 'response': '\u2003'}, {'prompt': ' p ', 'response': 'different'}, {'prompt': '\t', 'response': ''}],
        'validation': [{'prompt': 'validation', 'response': ' v '}],
        'sample_train': [{'prompt': ' p ', 'response': '\tr ', 'extra': [1, 2]}],
    }
    previous, files, exclusions = [], [], []
    for split, rows in examples.items():
        path = raw / (split + '.jsonl')
        path.write_bytes('\n'.join(json.dumps(x, ensure_ascii=False) for x in rows).encode())
        prior = d.validate_file(path, split, d.digest(path), path.stat().st_size, len(rows))
        previous.append(prior)
        result, removed = d.derive_split(path, out, prior)
        files.append(result); exclusions.extend(removed)
    a1 = tmp_path / 'a1.json'
    d.write_json(a1, {'status': 'PASS', 'policy_sha256': 'fixture-policy', 'files': previous})
    with (out / 'excluded_rows.jsonl').open('x') as f:
        for row in exclusions:f.write(json.dumps(row) + '\n')
    m = {'status': 'GENERATED_PENDING_INDEPENDENT_VERIFICATION', 'a1_sha256': d.digest(a1), 'rule_sha256': 'fixture-policy', 'files': files, 'exclusions': d.inventory(out / 'excluded_rows.jsonl', len(exclusions))}
    d.write_json(out / 'manifest.json', m)
    d.checksums(out, 'DATA_SHA256SUMS', [out / x['derived']['file'] for x in files])
    d.checksums(out, 'METADATA_SHA256SUMS', [out / x['mapping']['file'] for x in files] + [out / 'excluded_rows.jsonl', out / 'manifest.json'])
    return out, raw, a1


def test_roundtrip_counts_all_fields_and_containment(tmp_path):
    out, raw, a1 = make_bundle(tmp_path)
    before = {p.name: p.read_bytes() for p in raw.iterdir()}
    result = v.verify_bundle(out, raw, a1)
    assert result['status'] == 'PASS'
    assert result['files']['train'] == dict(raw_rows=4, derived_rows=2, excluded_rows=2, byte_identity='PASS')
    assert result['overlaps']['sample_train__train'] == dict(exact_prompt=1, exact_pair=1)
    assert result['overlaps']['train__validation'] == dict(exact_prompt=0, exact_pair=0)
    assert (out / 'train.mapping.tsv').read_text() == 'source_line\tderived_line\n1\t1\n2\t0\n3\t2\n4\t0\n'
    assert [json.loads(x)['reasons'] for x in (out / 'excluded_rows.jsonl').read_text().splitlines()] == [['empty_prompt', 'whitespace_only_response'], ['whitespace_only_prompt', 'empty_response']]
    assert {p.name:p.read_bytes() for p in raw.iterdir()} == before


@pytest.mark.parametrize('damage', ['content', 'missing', 'duplicate', 'order', 'mapping', 'exclusion', 'manifest', 'checksum', 'raw', 'a1'])
def test_independent_verifier_detects_damage(tmp_path, damage):
    out, raw, a1 = make_bundle(tmp_path)
    path = out / 'train.jsonl'; data = path.read_bytes()
    if damage == 'content':path.write_bytes(data.replace(b' p ', b'p'))
    if damage == 'missing':path.write_bytes(b'')
    if damage == 'duplicate':path.write_bytes(data + b'\n' + data)
    if damage == 'order':path.write_bytes(b'\n'.join(reversed(data.splitlines())))
    if damage == 'mapping':(out / 'train.mapping.tsv').write_text('source_line\tderived_line\n1\t2\n')
    if damage == 'exclusion':(out / 'excluded_rows.jsonl').write_text('')
    if damage == 'manifest':
        m=json.loads((out/'manifest.json').read_text());m['files'][0]['derived']['rows']=999
        (out/'manifest.json').write_text(json.dumps(m))
    if damage == 'checksum':(out/'DATA_SHA256SUMS').write_text('0'*64+'  train.jsonl\n')
    if damage == 'raw':(raw/'train.jsonl').write_bytes(data)
    if damage == 'a1':a1.write_text('{}')
    with pytest.raises((ValueError, KeyError)):
        v.verify_bundle(out, raw, a1)


def test_no_overwrite_and_no_raw_destination(tmp_path):
    out, raw, a1 = make_bundle(tmp_path)
    before=(out/'train.jsonl').read_bytes()
    prior=json.loads(a1.read_text())['files'][0]
    with pytest.raises(FileExistsError):d.derive_split(raw/'train.jsonl',out,prior)
    with pytest.raises(FileExistsError):d.create_output(out,raw)
    with pytest.raises(d.HardStop):d.create_output(raw/'derived',raw)
    assert (out/'train.jsonl').read_bytes()==before


def test_a1_disagreement_before_writing(tmp_path):
    out, raw, a1=make_bundle(tmp_path)
    prior=json.loads(a1.read_text())['files'][0]
    prior['anomalies'][0]['reasons']=['empty_response']
    fresh=d.create_output(tmp_path/'new',raw)
    with pytest.raises(d.HardStop,match='A.1 disagreement'):
        d.derive_split(raw/'train.jsonl',fresh,prior)
    assert list(fresh.iterdir())==[]


@pytest.mark.parametrize('broken', ['sha', 'schema'])
def test_raw_hard_stop_before_output(tmp_path,broken):
    out,raw,a1=make_bundle(tmp_path); prior=json.loads(a1.read_text())['files'][0]
    path=raw/'train.jsonl';path.write_bytes(b'{}\n')
    if broken=='schema':prior.update(sha256=d.digest(path),bytes=3,physical_lines=1)
    fresh=d.create_output(tmp_path/'new',raw)
    with pytest.raises(d.HardStop):d.derive_split(path,fresh,prior)
    assert list(fresh.iterdir())==[]
