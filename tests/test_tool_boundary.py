import pytest
from sugarcode.llm.tools import Tool

def test_actual_dispatch_and_validation(monkeypatch):
 from sugarcode.llm.tool_boundary import checked_call
 from sugarcode.llm import tools
 t=Tool('identity','canary','identity','actual identity',{'properties':{'x':{'type':'integer'}},'required':['x']})
 calls=[]
 def run(name,args):calls.append(args);return {'result':args['x']+1}
 monkeypatch.setattr(tools,'catalog',lambda:{'identity':t});monkeypatch.setattr(tools,'call_tool',run)
 for x in ['null','42','[1]',{'x':'wrong'},{'x':True},{'x':float('nan')},{'bad':2}]:
  assert 'error' in checked_call('identity',x)
 assert calls==[]
 assert checked_call('identity','{"x":2}')=={'result':3} and calls==[{'x':2}]

def test_real_python_tool_and_load_failure(monkeypatch):
 from sugarcode.llm.tool_boundary import checked_call
 from sugarcode.llm import tools
 import types
 t=Tool('identity','canary','identity','real identity',{'properties':{'x':{'type':'array','items':{'type':'string'}}},'required':['x']})
 monkeypatch.setattr(tools,'catalog',lambda:{'identity':t})
 monkeypatch.setattr(tools.importlib,'import_module',lambda name:types.SimpleNamespace(identity=lambda x:list(reversed(x))))
 assert checked_call('identity',{'x':['a','b']})=={'result':['b','a']}
 def fail(name):raise ImportError('canary loading failed')
 monkeypatch.setattr(tools.importlib,'import_module',fail)
 assert 'ImportError' in checked_call('identity',{'x':['a']})['error']

def test_catalog_and_unknown_schema_refuse(monkeypatch):
 from sugarcode.llm.tool_boundary import checked_call
 from sugarcode.llm import tools
 def fail():raise RuntimeError('catalog unavailable')
 monkeypatch.setattr(tools,'catalog',fail);assert 'error' in checked_call('x',{})
 monkeypatch.setattr(tools,'catalog',lambda:{'x':Tool('x','x','x','x',{'properties':{'x':{'type':'mystery'}},'required':['x']})})
 assert 'error' in checked_call('x',{'x':1})

@pytest.mark.parametrize('schema,args',[
 ({'properties':{'x':{'type':'string','enum':['ok']}},'required':[]},{}),
 ({'properties':{'x':{'type':'array','items':{'type':'string','enum':['ok']}}},'required':['x']},{'x':[]}),
 ({'properties':{'x':{'type':'object','additionalProperties':{'type':'string','enum':['ok']}}},'required':['x']},{'x':{}}),
])
def test_schema_preflight_refuses_unknown_even_absent_values(monkeypatch,schema,args):
 from sugarcode.llm.tool_boundary import checked_call
 from sugarcode.llm import tools
 calls=[]
 monkeypatch.setattr(tools,'catalog',lambda:{'x':Tool('x','x','x','spy',schema)})
 monkeypatch.setattr(tools,'call_tool',lambda name,value:calls.append(value) or {'result':'SIDE EFFECT SPY'})
 result=checked_call('x',args)
 assert calls==[] and 'error' in result

@pytest.mark.parametrize('error',[RecursionError,MemoryError,UnicodeDecodeError,OSError])
def test_boundary_handles_catalog_exceptions(monkeypatch,error):
 from sugarcode.llm.tool_boundary import checked_call
 from sugarcode.llm import tools
 def fail():
  if error is UnicodeDecodeError:raise error('utf8',b'x',0,1,'invalid')
  raise error('instrumented fault')
 monkeypatch.setattr(tools,'catalog',fail)
 assert error.__name__ in checked_call('x',{})['error']

def test_boundary_recursive_schema_and_deep_json(monkeypatch):
 from sugarcode.llm.tool_boundary import checked_call
 from sugarcode.llm import tools
 s={'type':'array'};s['items']=s;calls=[]
 monkeypatch.setattr(tools,'catalog',lambda:{'x':Tool('x','x','x','x',{'properties':{'x':s},'required':[]})})
 monkeypatch.setattr(tools,'call_tool',lambda *a:calls.append(a))
 assert 'error' in checked_call('x',{}) and not calls
 assert 'error' in checked_call('x','['*5000+']'*5000)
