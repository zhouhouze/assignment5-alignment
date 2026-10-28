"""P2-B.1 read-only CPU lexical contamination candidate audit.

Frozen data -> independent normalized index -> machine candidates; no edits,
filtering, semantic-model inference, human adjudication or admission approval.
"""
import argparse
from collections import Counter, defaultdict
import csv
from datetime import datetime, timezone
import gzip
import hashlib
import heapq
import json
from pathlib import Path
import re
import resource
import subprocess
import sys
import time
import unicodedata

ROOT = Path(__file__).resolve().parents[1]
A2 = 'artifacts/pa5-supplement-qwen/sft/20261028-p2a2'
PILOT = 'artifacts/pa5-supplement-qwen/baseline/pilot/20261003-pilot-03/manifest.json'
PROTOCOL = 'notes/experiments/SUP-QWEN-evaluation/evaluation-protocol-v1.md'
POLICY = 'notes/experiments/SUP-QWEN-data-flywheel/sft-data-quality-plan.md'
PINS = {PROTOCOL: '879764bf6f0286439cdf9527a7c9bdda93d064d4a157676851d79cf69145bcd3',
        POLICY: 'd841242f8f770c6b6e87988107885cf7402531cce193efe7f2d3295e8aed3389',
        A2+'/manifest.json': 'c9eaf0e154f073500c237d6242a3d4188cdaf15e715a183e23d164813d3c352f',
        A2+'/acceptance.json': '701782a1949e58c21e1d332c700eae3a7332ac3b2bbd06e9e7566c6a69103f72'}
PARAMS = dict(normalization='NFKC + casefold + Unicode word regex [^\\W_]+; no source mutation',
              ngram=5, anchors=8, minimum_anchor_hits=2, minimum_tokens=12,
              jaccard_threshold=.8, containment_threshold=.9, minimum_shared_grams=8,
              wall_seconds_limit=900, peak_rss_bytes_limit=4*1024**3,
              output_bytes_limit=2_000_000_000, comparisons_limit=10_000_000,
              candidates_limit=1_000_000, hash='BLAKE2b-64, deterministic bottom-8 anchors')


def require(ok, message):
    if not ok: raise ValueError(message)


def sha(path):
    with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def text_hash(text):return hashlib.sha256(text.encode()).hexdigest()


def words(text):return re.findall(r'[^\W_]+',unicodedata.normalize('NFKC',text).casefold())


def grams(tokens):
    return {int.from_bytes(hashlib.blake2b(' '.join(tokens[i:i+5]).encode(),digest_size=8).digest(),'big') for i in range(len(tokens)-4)}


def rss():
    x=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return x if sys.platform=='darwin' else x*1024


def new_output(path, protected):
    path=Path(path).resolve()
    require(not any(path==p.resolve() or path.is_relative_to(p.resolve()) for p in protected),'Unsafe output location')
    path.mkdir(parents=True,exist_ok=False)
    return path


def check_identity(root,derived):
    fingerprints={}
    for name,h in PINS.items():
        require(sha(root/name)==h,'Frozen identity mismatch: '+name);fingerprints[str(root/name)]=h
    m=json.loads((root/A2/'manifest.json').read_text())
    a=json.loads((root/A2/'acceptance.json').read_text())
    verify=root/A2/'independent-verification.json'
    require(sha(verify)==a['independent_verification_sha256'],'A.2 verifier identity')
    require(json.loads(verify.read_text())['status']=='PASS' and a['status']=='PASS','A.2 acceptance')
    fingerprints[str(verify)]=sha(verify)
    require(sha(derived/'manifest.json')==PINS[A2+'/manifest.json'],'External manifest')
    for checksum in ['DATA_SHA256SUMS','METADATA_SHA256SUMS']:
        require((derived/checksum).read_bytes()==(root/A2/checksum).read_bytes(),'Checksum inventory disagreement')
        fingerprints[str(derived/checksum)]=sha(derived/checksum)
        for line in (derived/checksum).read_text().splitlines():
            h,name=line.split('  ',1);p=derived/name
            require(sha(p)==h,'Derived identity mismatch: '+name);fingerprints[str(p)]=h
    for f in m['files']:
        for kind in ['derived','mapping']:
            require((derived/f[kind]['file']).stat().st_size==f[kind]['bytes'],'Derived size mismatch')
    inventory=json.loads((root/PILOT).read_text())['dataset_hashes']
    inv_hash=hashlib.sha256(json.dumps(inventory,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    require(inv_hash=='8ae5c03b4f261bd7c10dd31056efde8c87b34cf580ee90f4c6aaf856ab684e55','Benchmark inventory')
    require(len(inventory)==60,'Benchmark file count')
    for name,h in inventory.items():
        require(sha(root/name)==h,'Benchmark SHA mismatch: '+name);fingerprints[str(root/name)]=h
    return m,inventory,fingerprints


def sft_rows(folder, info):
    """Join immutable Derived lines to complete source mappings, checking counts."""
    with (folder/info['mapping']['file']).open() as maps, (folder/info['derived']['file']).open() as data:
        require(next(maps)=='source_line\tderived_line\n','Mapping header')
        current=0;source_count=0
        for source_count,line in enumerate(maps,1):
            source,dest=map(int,line.split())
            require(source==source_count,'Source mapping offset')
            if not dest:continue
            current+=1;require(dest==current,'Derived mapping offset')
            row=json.loads(next(data))
            require(isinstance(row,dict) and all(isinstance(row.get(k),str) and row[k].strip() for k in ('prompt','response')),'Derived schema')
            ref={'dataset':info['split'],'example_id':str(current),'derived_line':current,
                 'source_row_id':f'{info["source_sha256"]}:{info["split"]}:{source}',
                 'file':info['derived']['file'],'file_sha256':info['derived']['sha256']}
            yield ref,row
        require(current==info['derived']['rows'] and source_count==info['source_rows'] and not data.read(1),'Mapping/data coverage')


def benchmark_fields(task, value):
    """Each benchmark has a distinct schema. Nonlinguistic scoring metadata excluded."""
    if task=='mmlu':
        require(isinstance(value,list) and len(value)==6 and value[5] in ['A','B','C','D'],'MMLU schema')
        return {'question':value[0], 'question_with_options':'\n'.join(value[:5]), 'correct_option_text':value[1+'ABCD'.index(value[5])]}
    if task=='gsm8k':
        require(isinstance(value,dict) and all(isinstance(value.get(k),str) for k in ['question','answer']) and '####' in value['answer'],'GSM schema')
        return {'question':value['question'],'answer_rationale_and_gold':value['answer']}
    if task=='alpaca_eval':
        require(isinstance(value,dict) and all(isinstance(value.get(k),str) for k in ['instruction','output','dataset','generator']),'Alpaca schema')
        return {'instruction':value['instruction'],'gpt4_reference_output':value['output']}
    require(task=='simple_safety_tests' and all(isinstance(value.get(k),str) for k in ['id','prompts_final','harm_area','category']),'SST schema')
    return {'prompts_final':value['prompts_final']}


def benchmarks(root,inventory):
    for name,h in sorted(inventory.items()):
        p=root/name
        if '/mmlu/' in name:
            task='mmlu'
            with p.open() as f:rows=list(csv.reader(f))
            ids=[p.stem.removesuffix('_test')+':'+str(i) for i in range(len(rows))]
        elif '/gsm8k/' in name:
            task='gsm8k';rows=[json.loads(x) for x in p.read_text().splitlines()];ids=list(map(str,range(len(rows))))
        elif '/alpaca_eval/' in name:
            task='alpaca_eval';rows=json.loads(p.read_text());ids=list(map(str,range(len(rows))))
        else:
            task='simple_safety_tests'
            with p.open() as f:rows=list(csv.DictReader(f))
            ids=[r['id'] for r in rows]
        for i,(id,row) in enumerate(zip(ids,rows)):
            yield {'dataset':task,'example_id':id,'file':name,'file_sha256':h,
                   'record_index_0based':i},benchmark_fields(task,row)


class Index:
    def __init__(self):
        self.targets=[];self.exact=defaultdict(list);self.normal=defaultdict(list);self.anchors=defaultdict(list)
        self.coverage=Counter();self.comparisons=0

    def add(self,ref,field,text,near=True):
        token=words(text);norm=' '.join(token);g=grams(token) if near and len(token)>=12 else set()
        idx=len(self.targets)
        self.targets.append((ref,field,text,norm,g))
        self.exact[text_hash(text)].append(idx)
        if norm and near:self.normal[text_hash(norm)].append(idx)
        for anchor in heapq.nsmallest(8,g):self.anchors[anchor].append(idx)
        self.coverage[(ref['dataset'],field,'all')]+=1
        self.coverage[(ref['dataset'],field,'near_eligible' if g else 'near_not_assessed')]+=1

    def query(self,text,pair_only=False):
        token=words(text);norm=' '.join(token);g=grams(token) if len(token)>=12 and not pair_only else set()
        exact=set(self.exact.get(text_hash(text),[]))
        normalized=set(self.normal.get(text_hash(norm),[])) if norm and not pair_only else set()
        retrieval=Counter()
        for gram in g:retrieval.update(self.anchors.get(gram,()))
        ids=exact|normalized|{idx for idx,n in retrieval.items() if n>=2}
        for idx in sorted(ids):
            ref,field,target,tnorm,tg=self.targets[idx]
            if pair_only != (field=='pair'):continue
            self.comparisons+=1
            require(self.comparisons<=PARAMS['comparisons_limit'],'Comparison budget exceeded')
            shared=len(g&tg) if tg and g else 0
            j=shared/len(g|tg) if shared else 0.;c=shared/min(len(g),len(tg)) if shared else 0.
            if text==target:method='exact'
            elif norm and norm==tnorm and not pair_only:method='normalized_equal'
            elif shared>=8 and (j>=.8 or c>=.9):method='ngram_candidate'
            else:continue
            yield idx,{'method':method,'category':'Exact Match' if method=='exact' else 'Near Duplicate Candidate',
                       'jaccard':j,'containment':c,'shared_5grams':shared,'short_text':min(len(token),len(words(target)))<12}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--derived',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    out=new_output(a.output,[a.derived,ROOT/'data'])
    start=time.monotonic();cpu_start=time.process_time()
    state={'gate':'P2-B.1','status':'PENDING','directly_comparable_to_official':False,'parameters':PARAMS,
           'command':[sys.executable,*sys.argv],'started_at':datetime.now(timezone.utc).isoformat(),'python':sys.version,
           'potential_semantic_contamination':'NOT ASSESSED: no semantic model/human review', 'data_admission':'PENDING',
           'gpu_used':False,'human_review_status':'pending'}
    with (out/'execution.txt').open('x') as log:
        def emit(message):print(message,flush=True);log.write(message+'\n');log.flush()
        def guard():
            require(time.monotonic()-start<900,'Wall time budget exceeded')
            require(rss()<4*1024**3,'RSS budget exceeded')
            require(sum(x.stat().st_size for x in out.iterdir() if x.is_file())<2_000_000_000,'Output disk budget exceeded')
        try:
            state.update(execution_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
                         git_status=subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True),source_sha256=sha(Path(__file__)))
            require(subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip()=='learning/pa5-supplement','Branch')
            manifest,inventory,fingerprints=check_identity(ROOT,a.derived);state['input_fingerprints']=fingerprints;state['benchmark_files']=inventory
            emit('PASS identities: Derived + mapping + manifest + 60 benchmark files')
            index=Index();dataset_counts=Counter();target_ids=defaultdict(list)
            for ref,row in sft_rows(a.derived,manifest['files'][1]):
                dataset_counts['validation']+=1
                for field in ['prompt','response']:index.add(ref,field,row[field])
                index.add(ref,'pair',json.dumps([row['prompt'],row['response']],ensure_ascii=False),near=False)
                if dataset_counts['validation']%2000==0:guard()
            for ref,fields in benchmarks(ROOT,inventory):
                dataset_counts[ref['dataset']]+=1;target_ids[ref['dataset']].append(ref['example_id'])
                for field,text in fields.items():index.add(ref,field,text)
                if sum(dataset_counts.values())%2000==0:guard()
            require({k:dataset_counts[k] for k in ['mmlu','gsm8k','alpaca_eval','simple_safety_tests']}==dict(mmlu=14042,gsm8k=1319,alpaca_eval=805,simple_safety_tests=100),'Benchmark counts')
            state['target_field_coverage']=[dict(dataset=k[0],field=k[1],scope=k[2],count=n) for k,n in sorted(index.coverage.items())]
            state['benchmark_ordered_id_sha256']={k:text_hash('\n'.join(ids)+'\n') for k,ids in target_ids.items()}
            emit(f'INDEX ready: {len(index.targets)} fields; peak_RSS={rss()}')
            stats=Counter();matched_train=defaultdict(set);matched_target=defaultdict(set);record_pairs=defaultdict(set);n=0;short_train=Counter()
            with gzip.open(out/'candidates.jsonl.gz','xt',encoding='utf-8') as candidates:
                for ref,row in sft_rows(a.derived,manifest['files'][0]):
                    dataset_counts['train']+=1
                    queries={'prompt':row['prompt'],'response':row['response'],'pair':json.dumps([row['prompt'],row['response']],ensure_ascii=False)}
                    for field,text in queries.items():
                        if field!='pair' and len(words(text))<12:short_train[field]+=1
                        for idx,score in index.query(text,pair_only=field=='pair'):
                            target,tfield,ttext,_,_=index.targets[idx]
                            key=(target['dataset'],score['method']);stats[(target['dataset'],field,tfield,score['method'])]+=1
                            matched_train[key].add(ref['example_id']);matched_target[key].add(target['example_id']);record_pairs[key].add((ref['example_id'],target['example_id']))
                            n+=1;require(n<=PARAMS['candidates_limit'],'Candidate output cap exceeded')
                            candidate={'candidate_id':n,'train':dict(ref,field=field,text_sha256=text_hash(text)),
                                       'target':dict(target,field=tfield,text_sha256=text_hash(ttext)),**score,
                                       'evidence':{'train_excerpt':text[:200],'target_excerpt':ttext[:200]},
                                       'human_review_status':'pending','confirmed_contamination':None}
                            candidates.write(json.dumps(candidate,ensure_ascii=False)+'\n')
                    if dataset_counts['train']%5000==0:
                        guard();emit(f'SCAN {dataset_counts["train"]}/210326 candidates={n} comparisons={index.comparisons} elapsed={time.monotonic()-start:.1f}s RSS={rss()}')
            guard()
            state.update(dataset_counts=dict(dataset_counts),candidate_field_pairs=n,scored_comparisons=index.comparisons,
                         short_train_fields=dict(short_train),field_counts=[dict(dataset=k[0],train_field=k[1],target_field=k[2],method=k[3],count=n) for k,n in sorted(stats.items())],
                         summary=[dict(dataset=k[0],method=k[1],field_pairs=sum(n for sk,n in stats.items() if (sk[0],sk[3])==k),unique_record_pairs=len(record_pairs[k]),matched_train_rows=len(matched_train[k]),matched_target_rows=len(matched_target[k]),train_hit_rate=len(matched_train[k])/dataset_counts['train'],target_hit_rate=len(matched_target[k])/dataset_counts[k[0]]) for k in sorted(record_pairs)],
                         candidates_sha256=sha(out/'candidates.jsonl.gz'))
            for path,h in fingerprints.items():require(sha(path)==h,'Input changed during audit: '+path)
            state['status']='PASS';emit('PASS full scan + post-run input integrity (not admission approval)')
        except Exception as exc:
            state.update(status='FAIL',error=f'{type(exc).__name__}: {exc}');emit('HARD STOP '+state['error'])
        state.update(elapsed_seconds=time.monotonic()-start,cpu_seconds=time.process_time()-cpu_start,peak_rss_bytes=rss(),finished_at=datetime.now(timezone.utc).isoformat())
        with (out/'audit.json').open('x') as f:json.dump(state,f,indent=2);f.write('\n')
    return 0 if state['status']=='PASS' else 1


if __name__=='__main__':sys.exit(main())
