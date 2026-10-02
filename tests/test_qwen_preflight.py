"""Offline CPU integration checks; assets explicitly downloaded by preflight."""
from pathlib import Path
import importlib.util
import json
import pytest
from transformers import AutoTokenizer

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('qwen_preflight',ROOT/'scripts/qwen_preflight.py')
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)

@pytest.mark.parametrize('value,errors',[
    ({'prompt':'hello','response':'world'},[]),
    ({'prompt':'  ','response':'x'},['empty_prompt']),
    ({'prompt':'x','response':None},['non_string_response']),
    ({'response':'x'},['missing_prompt']),
    ([],['not_object']),
])
def test_sft_schema(value,errors):
    assert audit.schema_errors(value)==errors

def test_jsonl_audit_keeps_malformed_and_duplicates(tmp_path):
    path=tmp_path/'test.jsonl'
    path.write_text('{"prompt":"a","response":"b"}\n{"response":"b","prompt":"a"}\n{bad}\n{"prompt":" ","response":""}\n')
    result,_,_=audit.audit_jsonl(path)
    assert result['line_count']==4
    assert result['counts']['malformed_json']==1
    assert result['counts']['exact_duplicate_prompt_response_count']==1
    assert result['counts']['duplicate_record_count']==1
    assert result['counts']['empty_response']==1

@pytest.fixture(scope='module')
def policy():
    path=ROOT/'models/qwen-preflight/Qwen2.5-7B'
    if not path.exists():
        pytest.skip('Restore pinned tokenizer assets before offline integration tests')
    return AutoTokenizer.from_pretrained(path,local_files_only=True)

def test_native_qwen_eos_and_no_invented_bos(policy):
    assert policy.eos_token=='<|endoftext|>'
    assert policy.eos_token_id==151643
    assert policy.encode(policy.eos_token,add_special_tokens=False)==[151643]
    assert policy.bos_token is None
    assert policy.pad_token_id==151643

def test_document_roundtrip_and_explicit_eos(policy):
    template=(ROOT/'cs336_alignment/prompts_safety/alpaca_sft.prompt').read_text()
    example={'prompt':'Compute 1 + 1.','response':'2'}
    ids=audit.encode_document(policy,template,example)
    assert ids[-1]==policy.eos_token_id
    assert policy.decode(ids[:-1])==template.format(instruction=example['prompt'],response=example['response'])
    assert '<|im_start|>' not in policy.decode(ids)

def test_judge_native_chat_preserves_semantics():
    path=ROOT/'models/qwen-preflight/Qwen2.5-72B-Instruct'
    if not path.exists():
        pytest.skip('Restore pinned judge tokenizer assets')
    tokenizer=AutoTokenizer.from_pretrained(path,local_files_only=True)
    for messages in audit.judge_messages(ROOT).values():
        rendered=tokenizer.apply_chat_template(messages,tokenize=False,add_generation_prompt=True)
        assert all(message['content'] in rendered for message in messages)
        assert rendered.startswith('<|im_start|>system\n')
        assert rendered.endswith('<|im_start|>assistant\n')
        assert '<|start_header_id|>' not in rendered
    assert tokenizer.eos_token_id==151645

def test_persisted_judge_prompt_and_pinned_configuration():
    import yaml
    path=ROOT/'models/qwen-preflight/Qwen2.5-72B-Instruct'
    if not path.exists():
        pytest.skip('Restore pinned judge tokenizer assets')
    tokenizer=AutoTokenizer.from_pretrained(path,local_files_only=True)
    folder=ROOT/'scripts/alpaca_eval_vllm_qwen2_5_72b_fn'
    expected=tokenizer.apply_chat_template(audit.judge_messages(ROOT)['alpaca_eval'],tokenize=False,add_generation_prompt=True)
    assert (folder/'alpaca_eval_fn.txt').read_text()==expected
    config=json.loads((ROOT/'configs/pa5_supplement_qwen.json').read_text())
    annotator=yaml.safe_load((folder/'configs.yaml').read_text())['alpaca_eval_vllm_qwen2_5_72b_fn']
    kwargs=annotator['completions_kwargs']
    assert kwargs['model_kwargs']['revision']==config['judge_revision']
    assert kwargs['model_kwargs']['tokenizer_revision']==config['judge_tokenizer_revision']
    assert kwargs['model_kwargs']['generation_config']=='vllm'
    assert kwargs['stop_token_ids']==config['judge']['stop_token_ids']
    assert kwargs['is_chatml_prompt'] is False
    assert kwargs['temperature']==0 and kwargs['top_p']==1
