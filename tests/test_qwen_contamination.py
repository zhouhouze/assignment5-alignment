"""Synthetic detection contracts; no online data or semantic models."""
import importlib.util
from pathlib import Path
import pytest

spec=importlib.util.spec_from_file_location('audit_contamination',Path(__file__).resolve().parents[1]/'scripts/audit_qwen_contamination.py')
a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
TEXT=' '.join('word'+str(i) for i in range(50))
REF={'dataset':'validation','example_id':'1'}


def matches(target,query):
    index=a.Index();index.add(REF,'prompt',target)
    return list(index.query(query))


def test_exact():
    hit=matches(TEXT,TEXT)
    assert len(hit)==1 and hit[0][1]['method']=='exact'


@pytest.mark.parametrize('text',['  '+TEXT.upper()+'  ',TEXT.replace(' ', ',\n'),TEXT.replace('word0','ｗｏｒｄ０')])
def test_normalization(text):
    assert matches(TEXT,text)[0][1]['method']=='normalized_equal'


def test_local_rewrite_and_template_similarity_are_only_candidates():
    hit=matches(TEXT,TEXT.replace('word25','different'))
    assert len(hit)==1 and hit[0][1]['method']=='ngram_candidate'
    assert hit[0][1]['category']=='Near Duplicate Candidate'
    # A shared template can score highly despite different payloads; not human confirmation.
    assert matches(TEXT+' payload',TEXT+' otherpayload')[0][1]['category']=='Near Duplicate Candidate'


def test_containment():
    hit=matches(TEXT,'prefix '*100+TEXT+' suffix '*100)
    assert hit[0][1]['containment']==1 and hit[0][1]['method']=='ngram_candidate'


def test_unrelated():assert matches(TEXT,'unrelated text about cats and forests '*20)==[]


def test_short_false_positive_control():
    assert matches('Yes.','YES')[0][1]['short_text'] is True
    assert matches('The answer is two','The answer is three')==[]


def test_multi_anchor_dedup_and_pair_isolation():
    index=a.Index();index.add(REF,'prompt',TEXT);index.add(REF,'pair',TEXT,near=False)
    assert len(list(index.query(TEXT)))==1
    assert len(list(index.query(TEXT,pair_only=True)))==1


@pytest.mark.parametrize('task,row,keys',[
 ('mmlu',['Question','one','two','three','four','B'],['question','question_with_options','correct_option_text']),
 ('gsm8k',{'question':'Question','answer':'reason #### 2'},['question','answer_rationale_and_gold']),
 ('alpaca_eval',{'instruction':'Instruction','output':'Reference','dataset':'source','generator':'gpt4'},['instruction','gpt4_reference_output']),
 ('simple_safety_tests',{'id':'sst_1','prompts_final':'Request','harm_area':'area','category':'category'},['prompts_final'])])
def test_distinct_benchmark_schemas(task,row,keys):
    result=a.benchmark_fields(task,row);assert list(result)==keys
    if task=='mmlu':assert result['correct_option_text']=='two'


@pytest.mark.parametrize('task,row',[('mmlu',['bad']),('gsm8k',{'question':'x','answer':'no delimiter'}),('alpaca_eval',{'instruction':'x'}),('simple_safety_tests',{'id':'x'})])
def test_wrong_schema_stops(task,row):
    with pytest.raises(ValueError):a.benchmark_fields(task,row)


def test_sha_mismatch_stops(tmp_path,monkeypatch):
    p=tmp_path/'pin';p.write_text('changed')
    monkeypatch.setattr(a,'PINS',{'pin':'0'*64})
    with pytest.raises(ValueError,match='Frozen identity mismatch'):a.check_identity(tmp_path,tmp_path)


def test_output_protection(tmp_path):
    data=tmp_path/'data';data.mkdir();out=a.new_output(tmp_path/'out',[data])
    (out/'evidence').write_text('keep')
    with pytest.raises(FileExistsError):a.new_output(out,[data])
    link=tmp_path/'alias';link.symlink_to(data,target_is_directory=True)
    with pytest.raises(ValueError):a.new_output(link/'new',[data])
    assert (out/'evidence').read_text()=='keep'


def test_budget_stop(monkeypatch):
    monkeypatch.setitem(a.PARAMS,'comparisons_limit',0)
    with pytest.raises(ValueError,match='budget'):matches(TEXT,TEXT)
