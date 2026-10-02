import json
from pathlib import Path
import pytest
from cs336_alignment import qwen_baseline as b

@pytest.fixture(scope='module')
def tasks():
    return b.load_tasks()[0]


def test_pinned_selection_and_coverage(tasks):
    x=b.select(tasks,'PILOT',0)
    assert x==b.select(tasks,'PILOT',0)
    assert all(len(v)==20 for v in x.values())
    assert len({v['raw_input']['subject'] for v in x['mmlu']})==20
    assert len({(v['raw_input']['harm_area'],v['raw_input']['category']) for v in x['simple_safety_tests']})==10
    smoke=b.select(tasks,'SMOKE',0)
    assert all(smoke[t]==x[t][:1] for t in b.TASKS)


def test_official_prompt_no_gold_or_chat(tasks):
    for task in b.TASKS:
        example=tasks[task][0]
        prompt=b.render(task,example)
        assert prompt.startswith('# Instruction\n')
        assert prompt.endswith('# Answer:\n```\n')
        assert '<|im_start|>' not in prompt
        if task=='gsm8k':assert example['raw_input']['answer'] not in prompt
        if task=='alpaca_eval':assert example['raw_input']['output'] not in prompt


@pytest.mark.parametrize('task,text,gold,answer,correct',[
    ('mmlu','', 'A',None,False),
    ('mmlu','The correct answer is B.','A','B',False),
    ('mmlu','The correct answer is A. The correct answer is B.','A',None,False),
    ('gsm8k','The result is 1,234.00.','1234','1234.00',True),
    ('gsm8k','24 then 72 then 73','72','73',False),
])
def test_scoring_uses_unchanged_parser(task,text,gold,answer,correct):
    result=b.score(dict(task=task,raw_response=text,ground_truth=gold))
    assert result['parsed_answer']==answer
    assert result['correct']==correct


def test_judged_tasks_have_no_fake_scores():
    for task in ('alpaca_eval','simple_safety_tests'):
        assert b.score(dict(task=task,raw_response=''))==dict(parsed_answer=None,correct=None,parse_failure=None,evaluation_status='pending_judge')


@pytest.fixture
def prepared(tmp_path):
    directory=tmp_path/'dry'
    b.prepare(directory,'CPU_DRY_RUN')
    return directory


def add_raw(directory,response=''):
    m,requests,_=b.validate(directory)
    row={**requests[0], 'manifest_sha256':b.sha(directory/'manifest.json'),'raw_response':response}
    path=directory/'raw'/f'{row["task"]}-{row["request_index"]:04d}.jsonl'
    digest=b.write_new(path,[row],jsonl=True)
    path.with_suffix('.jsonl.sha256').write_text(digest+'\n')
    return path


def test_resume_preserves_empty_completed_result(prepared):
    path=add_raw(prepared)
    before=path.read_bytes()
    _,requests,raw=b.validate(prepared)
    assert len(requests)==4 and len(raw)==1 and raw[0]['raw_response']==''
    assert path.read_bytes()==before
    with pytest.raises(FileExistsError):b.write_new(path,[{}],jsonl=True)


def test_resume_stops_on_ambiguous_generation(prepared):
    b.write_new(prepared/'pending.json',{'request_indices':[0]})
    with pytest.raises(ValueError,match='pending'):b.validate(prepared)


def test_manifest_and_raw_corruption_stop(prepared):
    path=add_raw(prepared)
    path.write_text('{corrupted}\n')
    with pytest.raises(ValueError,match='hash'):b.validate(prepared)
    (prepared/'manifest.json').write_text('{}\n')
    with pytest.raises(ValueError,match='Manifest hash'):b.validate(prepared)


def test_id_mismatch_even_with_new_file_checksum_stops(prepared):
    path=add_raw(prepared)
    row=json.loads(path.read_text());row['example_id']='wrong'
    path.write_text(json.dumps(row)+'\n')
    path.with_suffix('.jsonl.sha256').write_text(b.sha(path)+'\n')
    with pytest.raises(ValueError,match='identity'):b.validate(prepared)


def test_generation_count_mismatch_hard_stops_before_raw(tmp_path,monkeypatch):
    import sys
    from types import SimpleNamespace
    directory=tmp_path/'smoke'
    b.prepare(directory,'SMOKE')
    model_path=tmp_path/'mock-weights'
    model_path.mkdir()
    config=json.loads(b.CONFIG.read_text())
    b.write_new(model_path/'weights-manifest.json',dict(model=config['model'],revision=config['model_revision'],files={}))
    class FakeMonitor:
        samples=[]
        def start(self):pass
        def finish(self):return {'method':'unit-test mock, no GPU','peak_mib':None}
    class WrongCountEngine:
        def __init__(self,**kwargs):self.llm_engine=SimpleNamespace(vllm_config='unit-test mock')
        def generate(self,*args,**kwargs):return []
    monkeypatch.setattr(b,'VramMonitor',FakeMonitor)
    monkeypatch.setitem(sys.modules,'vllm',SimpleNamespace(LLM=WrongCountEngine,SamplingParams=lambda **kw:kw))
    with pytest.raises(ValueError,match='count mismatch'):b.run(directory,model_path)
    assert (directory/'failed.json').exists()
    assert (directory/'pending.json').exists()
    assert not list((directory/'raw').glob('*.jsonl'))
    with pytest.raises(ValueError,match='Prior infra failure'):b.run(directory,model_path)
