"""CPU-only acceptance audit. Never loads model weights or initializes CUDA.

Inputs: pinned local config/tokenizer assets and immutable prompt/response JSONL.
Outputs: schema/length/duplicate evidence, sampled original text, tokenization
statistics, and judge prompt/config preparation (not model responses).
"""
import argparse
import ast
from collections import Counter
import hashlib
import json
from pathlib import Path
import random


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def schema_errors(value):
    if not isinstance(value, dict):
        return ['not_object']
    errors = []
    for key in ('prompt', 'response'):
        if key not in value:
            errors.append('missing_' + key)
        elif not isinstance(value[key], str):
            errors.append('non_string_' + key)
        elif not value[key].strip():
            errors.append('empty_' + key)
    return errors


def distribution(values):
    values = sorted(values)
    if not values:
        return None
    return dict(min=values[0], p50=values[int((len(values)-1)*.5)],
                p90=values[int((len(values)-1)*.9)], p99=values[int((len(values)-1)*.99)],
                max=values[-1], mean=sum(values)/len(values))


def audit_jsonl(path):
    counts = Counter()
    objects, pairs, prompts = set(), set(), set()
    lengths = {'prompt': [], 'response': []}
    line_count = 0
    invalid_rows = []
    with Path(path).open() as stream:
        for line_count, line in enumerate(stream, 1):
            try:
                value = json.loads(line)
            except json.JSONDecodeError:
                counts['malformed_json'] += 1
                invalid_rows.append({'line_number':line_count,'errors':['malformed_json']})
                continue
            errors = schema_errors(value)
            counts.update(errors)
            canonical = json.dumps(value, sort_keys=True, ensure_ascii=False)
            obj = hashlib.sha256(canonical.encode()).hexdigest()
            counts['duplicate_record_count'] += obj in objects
            objects.add(obj)
            if errors:
                invalid_rows.append({'line_number':line_count,'errors':errors})
            else:
                counts['valid_examples'] += 1
            if not isinstance(value,dict) or not all(isinstance(value.get(k),str) for k in lengths):
                continue
            pair = hashlib.sha256(json.dumps([value['prompt'], value['response']], ensure_ascii=False).encode()).hexdigest()
            prompt = hashlib.sha256(value['prompt'].encode()).hexdigest()
            counts['exact_duplicate_prompt_response_count'] += pair in pairs
            counts['duplicate_prompt_count'] += prompt in prompts
            pairs.add(pair)
            prompts.add(prompt)
            for key in lengths:
                lengths[key].append(len(value[key]))
    for key in ('malformed_json','not_object','missing_prompt','missing_response','non_string_prompt','non_string_response','empty_prompt','empty_response'):
        counts.setdefault(key, 0)
    return dict(bytes=Path(path).stat().st_size, sha256=digest(path), line_count=line_count,
                counts=dict(counts), invalid_rows=invalid_rows, length_unit='Unicode characters; all string-typed rows including empties',
                lengths={k: distribution(v) for k,v in lengths.items()}), pairs, prompts


def encode_document(tokenizer, template, example):
    """One document, no implicit BOS/chat wrapper, followed by native EOS ID."""
    errors = schema_errors(example)
    if errors:
        raise ValueError(errors)
    if tokenizer.eos_token_id is None:
        raise ValueError('Tokenizer must define an EOS delimiter')
    text = template.format(instruction=example['prompt'], response=example['response'])
    return tokenizer.encode(text, add_special_tokens=False) + [tokenizer.eos_token_id]


def judge_messages(root):
    # Extract semantic content while discarding only the official Llama wrappers.
    text = (root/'scripts/alpaca_eval_vllm_llama3_3_70b_fn/alpaca_eval_fn.txt').read_text()
    system, user = text.split('<|start_header_id|>system<|end_header_id|>\n\n',1)[1].split('<|eot_id|><|start_header_id|>user<|end_header_id|>\n\n',1)
    user = user.split('<|eot_id|><|start_header_id|>assistant<|end_header_id|>',1)[0]
    tree = ast.parse((root/'scripts/evaluate_safety.py').read_text())
    safety = next(ast.literal_eval(n.value) for n in ast.walk(tree)
                  if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='system_message' for t in n.targets))
    return {'alpaca_eval':[{'role':'system','content':system},{'role':'user','content':user}],
            'safety':[{'role':'system','content':safety},{'role':'user','content':'User Message: {request}\nAssistant Response: {response}'}]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    out = args.output
    out.mkdir(parents=True, exist_ok=False)
    def save(name, value):
        (out/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
    config = json.loads((root/'configs/pa5_supplement_qwen.json').read_text())
    results, pair_sets, prompt_sets = {}, {}, {}
    for filename in config['dataset_files']:
        key = Path(filename).stem
        path = root/'data/qwen-sft-mirror'/filename
        results[key], pair_sets[key], prompt_sets[key] = audit_jsonl(path)
    results['overlap'] = {f'{a}__{b}':{'unique_exact_pairs':len(pair_sets[a]&pair_sets[b]),'unique_prompts':len(prompt_sets[a]&prompt_sets[b])}
                          for a,b in [('train','test'),('sample_train','train'),('sample_train','test')]}
    results['directly_comparable_to_official'] = False
    save('dataset-acceptance.json', results)
    selected = set(random.Random(config['seed']).sample(range(results['train']['line_count']),20))
    with (out/'review-packet.jsonl').open('x') as target, (root/'data/qwen-sft-mirror/sft-instruct/train.jsonl').open() as source:
        for index,line in enumerate(source):
            if index in selected:
                value = json.loads(line)
                target.write(json.dumps(dict(example_id=index,line_number=index+1,selection_seed=config['seed'],selection='uniform sample without replacement from all train lines',**value,human_label=None,human_notes=None,human_review_status='pending'),ensure_ascii=False)+'\n')
    from transformers import AutoConfig, AutoTokenizer
    tokenizers = {}
    for role, name in [('policy','Qwen2.5-7B'),('judge','Qwen2.5-72B-Instruct')]:
        path = root/'models/qwen-preflight'/name
        tokenizer = AutoTokenizer.from_pretrained(path, local_files_only=True, trust_remote_code=False)
        model_config = AutoConfig.from_pretrained(path, local_files_only=True, trust_remote_code=False)
        tokenizers[role] = tokenizer
        save(role+'-tokenizer.json',dict(model=name,model_type=model_config.model_type,architectures=model_config.architectures,
             **{key:getattr(tokenizer,key) for key in ['eos_token','eos_token_id','bos_token','bos_token_id','pad_token','pad_token_id','special_tokens_map','chat_template']},
             config_bos_token_id=model_config.bos_token_id,config_eos_token_id=model_config.eos_token_id,
             pad_override=None,weights_loaded=False,gpu_used=False))
    tokenizer = tokenizers['policy']
    template = (root/config['sft']['template']).read_text()
    lengths = []
    for line in (root/'data/qwen-sft-mirror/sft-instruct/sample_train.jsonl').open():
        lengths.append(len(encode_document(tokenizer,template,json.loads(line))))
    total = sum(lengths); size = config['sft']['context_length']; sequences=(total-1)//size
    save('sample-tokenization.json',dict(scope='sample_train only; arithmetic next-token packing audit, not implemented Dataset',
         num_documents=len(lengths),total_tokens=total,tokens_per_document=distribution(lengths),seq_length=size,
         packed_sequences=sequences,input_target_pairs=sequences*size,unconsumed_suffix_tokens=total-(sequences*size+1),
         drop_remainder_tokens=(total-1)%size,packing_utilization=sequences*size/(total-1),
         delimiter=tokenizer.eos_token,delimiter_id=tokenizer.eos_token_id,add_special_tokens=False,
         formula='N=floor((T-1)/512); inputs S[i:i+512], labels S[i+1:i+513]. One lookahead token; no tensors/training.',
         full_train_token_statistics=None,directly_comparable_to_official=False))
    messages = judge_messages(root)
    save('judge-semantic-messages.json',messages)
    for task,msg in messages.items():
        rendered=tokenizers['judge'].apply_chat_template(msg,tokenize=False,add_generation_prompt=True)
        (out/(task+'-qwen-chat-template.txt')).write_text(rendered)
    print(json.dumps({'dataset':results,'output':str(out)},ensure_ascii=False,indent=2))


if __name__ == '__main__':
    main()
