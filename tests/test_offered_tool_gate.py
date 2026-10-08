from sugarcode.llm.agent import _run
from sugarcode.llm.tools import catalog

class Client:
 supports_tools=True
 def __init__(self,name,count=1):self.name=name;self.step=0;self.count=count;self.results=[]
 def chat(self,messages,tools=None):
  self.step+=1
  if self.step==1:return {'tool_calls':[{'id':str(i),'function':{'name':self.name,'arguments':'{"points":1}'}} for i in range(self.count)]}
  self.results=[m for m in messages if m['role']=='tool'];return {'content':'done'}

def test_actual_unoffered_catalog_tool_does_not_execute(monkeypatch):
 catalog()
 import sugarcode.modules.acmg_bayesian as module
 calls=[];monkeypatch.setattr(module,'classify_points',lambda **kw:calls.append(kw) or 'called')
 client=Client('acmg_bayesian__classify_points')
 answer,trace=_run(client,'question',[],2)
 assert calls==[] and not trace[0]['ok'] and 'not offered' in client.results[0]['content']

def test_actual_offered_tool_runs():
 tool=catalog()['acmg_bayesian__classify_points'];client=Client(tool.name)
 answer,trace=_run(client,'question',[tool],2)
 assert answer=='done' and trace[0]['ok']

def test_per_response_dispatch_budget(monkeypatch):
 catalog()
 import sugarcode.modules.acmg_bayesian as module
 calls=[];monkeypatch.setattr(module,'classify_points',lambda **kw:calls.append(kw) or 'called')
 tool=catalog()['acmg_bayesian__classify_points'];client=Client(tool.name,100)
 _run(client,'question',[tool],2)
 assert len(calls)<=24
