"""Restore only pinned configuration/tokenizers and the three authorized SFT files.

No weights, no eval data, no dataset loader, no model load. Verify SHA256 before
promoting a download; existing mismatched files cause a hard stop.
"""
import argparse
import hashlib
import json
from pathlib import Path
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INVENTORY = ROOT/'artifacts/pa5-supplement-qwen/preflight/20261002/download-inventory.json'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inventory',type=Path,default=DEFAULT_INVENTORY)
    args = parser.parse_args()
    inventory = json.loads(args.inventory.read_text())
    allowed_models = {'Qwen/Qwen2.5-7B','Qwen/Qwen2.5-72B-Instruct'}
    allowed_model_files = {'config.json','generation_config.json','tokenizer.json','tokenizer_config.json','vocab.json','merges.txt','README.md','LICENSE'}
    allowed_dataset_files = {'sft-instruct/train.jsonl','sft-instruct/test.jsonl','sft-instruct/sample_train.jsonl','README.md','sft-instruct/README.md'}
    for item in inventory:
        if len(item['revision'])!=40 or any(c not in '0123456789abcdef' for c in item['revision']):
            raise ValueError('Expected immutable commit')
        if item['repo'] in allowed_models and item['file'] in allowed_model_files:
            prefix='https://huggingface.co/'
            expected_path=Path('models/qwen-preflight')/item['repo'].split('/')[-1]/item['file']
        elif item['repo']=='garg-aayush/sft-cs336-assign5-datasets' and item['file'] in allowed_dataset_files:
            prefix='https://huggingface.co/datasets/'
            expected_path=Path('data/qwen-sft-mirror')/item['file']
        else:
            raise ValueError('File outside preflight allowlist')
        expected_url=prefix+item['repo']+'/resolve/'+item['revision']+'/'+item['file']
        if item['url']!=expected_url or Path(item['local_path'])!=expected_path:
            raise ValueError('Unexpected URL or destination')
        target=ROOT/expected_path
        target.parent.mkdir(parents=True,exist_ok=True)
        downloaded=not target.exists()
        source=target.with_suffix(target.suffix+'.partial') if downloaded else target
        if downloaded:
            with urllib.request.urlopen(expected_url,timeout=120) as response,source.open('xb') as output:
                while block:=response.read(1024*1024):
                    output.write(block)
        with source.open('rb') as stream:
            sha=hashlib.file_digest(stream,'sha256').hexdigest()
        if source.stat().st_size!=item['bytes'] or sha!=item['sha256']:
            raise ValueError(f'Integrity mismatch: {expected_path}')
        if downloaded:
            source.rename(target)
        print(f'VERIFIED {expected_path} {sha}',flush=True)


if __name__=='__main__':
    main()
