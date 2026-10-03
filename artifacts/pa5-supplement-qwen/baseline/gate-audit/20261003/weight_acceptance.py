from pathlib import Path
from datetime import datetime, timezone
import hashlib,json,subprocess,shutil,fcntl,os
from huggingface_hub import HfApi
from transformers import AutoConfig, AutoTokenizer
R=Path('/root/cs336/pa5-supplement'); B=Path('/root/pa5-supplement-setup/20261003-gpu-gate')
M='Qwen/Qwen2.5-7B'; V='d149729398750b98c0af14eb82c78cfe92750796'; P=R/'models/qwen-baseline-7b'/V
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip()=='f5f4050de424a2b371da83e792fa5a4a81279084'
assert not subprocess.check_output(['git','status','--porcelain'],cwd=R).strip()
assert not any('aria2c' in line or 'download_qwen_baseline_weights' in line for line in subprocess.check_output(['ps','-eo','comm'],text=True).splitlines())
def sha(p):
 with p.open('rb') as f: return hashlib.file_digest(f,'sha256').hexdigest()
def save(p,obj):
 with p.open('x') as f: json.dump(obj,f,indent=2); f.write('\n'); f.flush(); os.fsync(f.fileno())
info=HfApi().model_info(M,revision=V,files_metadata=True)
assert info.sha==V
names={'config.json','generation_config.json','model.safetensors.index.json'}|{f'model-{i:05d}-of-00004.safetensors' for i in range(1,5)}
metadata={x.rfilename:x for x in info.siblings if x.rfilename in names}; assert set(metadata)==names
files={}
for name,item in sorted(metadata.items()):
 p=P/name; digest=sha(p)
 assert p.stat().st_size==item.size,name
 if item.lfs: assert digest==item.lfs.sha256,name
 else:
  data=p.read_bytes(); assert hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()==item.blob_id,name
 files[name]={'bytes':p.stat().st_size,'sha256':digest,'upstream_lfs_sha256':item.lfs.sha256 if item.lfs else None,'upstream_git_blob_id':item.blob_id,'url':f'https://huggingface.co/{M}/resolve/{V}/{name}'}
 print('WEIGHT_VERIFIED',name,flush=True)
inv=json.loads((R/'artifacts/pa5-supplement-qwen/preflight/20261002/download-inventory.json').read_text())
tokens=[]
for x in inv:
 if x['repo']==M:
  p=R/x['local_path']; assert x['revision']==V and p.stat().st_size==x['bytes'] and sha(p)==x['sha256']
  tokens.append(x)
assert len(tokens)>=6
for name in ['config.json','generation_config.json']:
 assert sha(P/name)==sha(R/'models/qwen-preflight/Qwen2.5-7B'/name)
cfg=AutoConfig.from_pretrained(P,local_files_only=True)
tok=AutoTokenizer.from_pretrained(R/'models/qwen-preflight/Qwen2.5-7B',local_files_only=True)
assert cfg.model_type=='qwen2' and tok.eos_token_id==151643
index=json.loads((P/'model.safetensors.index.json').read_text()); assert set(index['weight_map'].values())=={f'model-{i:05d}-of-00004.safetensors' for i in range(1,5)}
# Preserve unused transport remnants; acquire lock before treating it as stale.
residuals=[]
for p in sorted(P.rglob('*')):
 if p.is_file() and p.suffix in {'.lock','.incomplete','.partial','.aria2'}:
  if p.suffix=='.lock':
   with p.open('rb') as f: fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
  q=B/'download-residuals'/p.relative_to(P); q.parent.mkdir(parents=True,exist_ok=True)
  assert not q.exists()
  residuals.append({'original':str(p),'preserved_as':str(q),'bytes':p.stat().st_size,'sha256':sha(p)})
  shutil.move(str(p),str(q))
assert not [p for p in P.rglob('*') if p.is_file() and p.suffix in {'.lock','.incomplete','.partial','.aria2'}]
now=datetime.now(timezone.utc).isoformat()
weights={'model':M,'revision':V,'created_at':now,'cache_path':str(P),'transport':'prior pinned HF aria2 downloads; acceptance reused files without download','files':files,'total_bytes':sum(x['bytes'] for x in files.values())}
save(P/'weights-manifest.json',weights)
accept={'schema_version':'1.0','experiment_id':'SUP-QWEN-01','directly_comparable_to_official':False,'status':'PASS','created_at':now,'git_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip(),'model':M,'model_revision':V,'tokenizer_revision':V,'weights':weights,'tokenizer_inventory_verified':tokens,'tokenizer_config_load':'PASS','model_type':cfg.model_type,'eos_token_id':tok.eos_token_id,'shard_count':4,'active_downloads':0,'download_remnants_in_model_directory':0,'preserved_stale_transport_files':residuals,'disk_free_bytes':shutil.disk_usage(P).free,'gpu_before_load':subprocess.check_output(['nvidia-smi','--query-gpu=name,memory.total,memory.used,utilization.gpu,driver_version','--format=csv,noheader'],text=True).strip(),'weights_redownloaded':False}
save(B/'weight-acceptance.json',accept)
print('ACCEPTANCE_PASS',weights['total_bytes'],'disk_free',accept['disk_free_bytes'],flush=True)
