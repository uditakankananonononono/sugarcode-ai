import pytest
from sugarcode.llm.tools import call_tool

@pytest.mark.parametrize('arguments',['[]','null','42','true',[],None,42])
def test_nonobject_refuses_without_exception(arguments):
 result=call_tool('acmg_bayesian__classify_points',arguments)
 assert result.get('error')=='arguments must be a JSON object'

@pytest.mark.parametrize('value',[True,'1',1.5,None])
def test_integer_type_refuses_before_real_dispatch(monkeypatch,value):
 import sugarcode.modules.acmg_bayesian as module
 calls=[];monkeypatch.setattr(module,'classify_points',lambda **kw:calls.append(kw))
 assert call_tool('acmg_bayesian__classify_points',{'points':value}).get('error','').startswith('invalid argument points')
 assert calls==[]

def test_actual_function_remains_runnable():
 assert 'result' in call_tool('acmg_bayesian__classify_points',{'points':1})

def test_real_cli_nonobject_refusal():
 import subprocess,sys,os,json
 from pathlib import Path
 p=subprocess.run([sys.executable,'-m','sugarcode.cli','tool','acmg_bayesian__classify_points','null'],capture_output=True,text=True,env=dict(os.environ,PYTHONPATH=str(Path(__file__).resolve().parents[1]/'src')))
 assert p.returncode==1 and json.loads(p.stdout)['error']=='arguments must be a JSON object' and not p.stderr

def test_recursive_declared_collection_types():
 from sugarcode.llm.tools import _argument_valid
 assert _argument_valid([1,2],{'type':'array','items':{'type':'integer'}})
 assert not _argument_valid([True],{'type':'array','items':{'type':'integer'}})
 assert not _argument_valid({'a':float('nan')},{'type':'object','additionalProperties':{'type':'number'}})
 assert _argument_valid(None,{'type':'integer','nullable':True})
