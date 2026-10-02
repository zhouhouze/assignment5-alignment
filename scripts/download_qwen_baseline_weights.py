"""Download only the approved 7B Base revision after CPU gate passes."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import time
from huggingface_hub import HfApi, hf_hub_download

ROOT=Path(__file__).resolve().parents[1]
MODEL='Qwen/Qwen2.5-7B'
REVISION='d149729398750b98c0af14eb82c78cfe92750796'
TARGET=ROOT/'models/qwen-baseline-7b'/REVISION
ALLOWED={'config.json','generation_config.json','model.safetensors.index.json'} | {f'model-{i:05d}-of-00004.safetensors' for i in range(1,5)}

def main():
    # The local and cloud dry-run reports are evidence; do not run before that Gate.
    dry=ROOT/'artifacts/pa5-supplement-qwen/baseline/cpu-dry-run/20261002-01/dry-run.json'
    if json.loads(dry.read_text())['status']!='PASS':
        raise RuntimeError('CPU dry-run not passed')
    if (TARGET/'weights-manifest.json').exists():
        raise FileExistsError('Weights manifest exists; verify and reuse, do not overwrite')
    start=time.perf_counter()
    info=HfApi().model_info(MODEL,revision=REVISION,files_metadata=True)
    if info.sha!=REVISION:raise ValueError('Model revision mismatch')
    files={x.rfilename:x for x in info.siblings if x.rfilename in ALLOWED}
    if set(files)!=ALLOWED:raise ValueError('Weight file inventory mismatch')
    TARGET.mkdir(parents=True,exist_ok=True)
    def download(name):
        item=files[name]
        path=Path(hf_hub_download(MODEL,name,revision=REVISION,local_dir=TARGET))
        with path.open('rb') as f:digest=hashlib.file_digest(f,'sha256').hexdigest()
        expected=item.lfs.sha256 if item.lfs else None
        if path.stat().st_size!=item.size or (expected and digest!=expected):
            raise ValueError('Weight size/SHA mismatch: '+name)
        result=dict(bytes=path.stat().st_size,sha256=digest,upstream_lfs_sha256=expected,url=f'https://huggingface.co/{MODEL}/resolve/{REVISION}/{name}')
        print('VERIFIED '+name+' '+str(result['bytes'])+' '+digest,flush=True)
        return name,result
    with ThreadPoolExecutor(max_workers=4) as pool:
        results=dict(pool.map(download,sorted(files)))
    manifest=dict(model=MODEL,revision=REVISION,created_at=datetime.now(timezone.utc).isoformat(),cache_path=str(TARGET),files=results,total_bytes=sum(x['bytes'] for x in results.values()),download_and_hash_seconds=time.perf_counter()-start)
    with (TARGET/'weights-manifest.json').open('x') as f:json.dump(manifest,f,indent=2)
    print('WEIGHTS_READY '+json.dumps(manifest),flush=True)

if __name__=='__main__':main()
