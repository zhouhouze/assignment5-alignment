"""Download only the approved 7B Base revision after CPU gate passes."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import time
import argparse
import subprocess
from huggingface_hub import HfApi, hf_hub_download

ROOT=Path(__file__).resolve().parents[1]
MODEL='Qwen/Qwen2.5-7B'
REVISION='d149729398750b98c0af14eb82c78cfe92750796'
TARGET=ROOT/'models/qwen-baseline-7b'/REVISION
ALLOWED={'config.json','generation_config.json','model.safetensors.index.json'} | {f'model-{i:05d}-of-00004.safetensors' for i in range(1,5)}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--transport',choices=['hf','aria2'],default='hf')
    args=parser.parse_args()
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
    if args.transport=='aria2':
        # All URLs and integrity checks are pinned to primary HF metadata.
        lines=[]
        for name,item in sorted(files.items()):
            if not item.lfs and (TARGET/name).exists():
                continue
            lines.extend([f'https://huggingface.co/{MODEL}/resolve/{REVISION}/{name}',f'  out={name}'])
            if item.lfs:
                lines.append(f'  checksum=sha-256={item.lfs.sha256}')
        inputs=TARGET/'aria2-inputs.txt'
        inputs.write_text('\n'.join(lines)+'\n')
        subprocess.run(['aria2c','--input-file='+str(inputs),'--dir='+str(TARGET),
                        '--max-concurrent-downloads=4','--max-connection-per-server=16',
                        '--split=16','--min-split-size=16M','--file-allocation=none',
                        '--continue=true','--auto-file-renaming=false','--check-integrity=true',
                        '--max-tries=1','--connect-timeout=30','--timeout=120',
                        '--summary-interval=30','--console-log-level=warn'],check=True)
    def download(name):
        item=files[name]
        path=TARGET/name if args.transport=='aria2' else Path(hf_hub_download(MODEL,name,revision=REVISION,local_dir=TARGET))
        with path.open('rb') as f:digest=hashlib.file_digest(f,'sha256').hexdigest()
        expected=item.lfs.sha256 if item.lfs else None
        if not item.lfs:
            content=path.read_bytes()
            if hashlib.sha1(b'blob '+str(len(content)).encode()+b'\0'+content).hexdigest()!=item.blob_id:
                raise ValueError('Upstream git blob mismatch: '+name)
        if path.stat().st_size!=item.size or (expected and digest!=expected):
            raise ValueError('Weight size/SHA mismatch: '+name)
        result=dict(bytes=path.stat().st_size,sha256=digest,upstream_lfs_sha256=expected,url=f'https://huggingface.co/{MODEL}/resolve/{REVISION}/{name}')
        print('VERIFIED '+name+' '+str(result['bytes'])+' '+digest,flush=True)
        return name,result
    with ThreadPoolExecutor(max_workers=4) as pool:
        results=dict(pool.map(download,sorted(files)))
    manifest=dict(model=MODEL,revision=REVISION,created_at=datetime.now(timezone.utc).isoformat(),cache_path=str(TARGET),transport=args.transport,files=results,total_bytes=sum(x['bytes'] for x in results.values()),download_and_hash_seconds=time.perf_counter()-start)
    with (TARGET/'weights-manifest.json').open('x') as f:json.dump(manifest,f,indent=2)
    print('WEIGHTS_READY '+json.dumps(manifest),flush=True)

if __name__=='__main__':main()
