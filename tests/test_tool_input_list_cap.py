import pytest
from sugarcode.llm.agent import _run
from sugarcode.llm.providers import ProviderError
from sugarcode.llm.tools import catalog
from test_offered_tool_gate import Client

def test_oversized_input_refuses_before_any_dispatch(monkeypatch):
 catalog()
 import sugarcode.modules.acmg_bayesian as module
 calls=[];monkeypatch.setattr(module,'classify_points',lambda **kw:calls.append(kw))
 tool=catalog()['acmg_bayesian__classify_points']
 with pytest.raises(ProviderError,match='call list'):_run(Client(tool.name,25),'question',[tool],2)
 assert calls==[]

def test_boundary_24_valid_calls_run():
 tool=catalog()['acmg_bayesian__classify_points'];client=Client(tool.name,24)
 answer,trace=_run(client,'question',[tool],2)
 assert len(trace)==24 and all(row['ok'] for row in trace)

@pytest.mark.parametrize('value',[{},'calls',42])
def test_nonlist_response_refuses(value):
 class Bad:
  supports_tools=True
  def chat(self,*args,**kwargs):return {'tool_calls':value}
 with pytest.raises(ProviderError,match='call list'):_run(Bad(),'question',[],2)
