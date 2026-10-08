"""Dispatch canaries only; no model/provider acceptance claim."""
from types import SimpleNamespace
import pytest
from sugarcode.llm import agent,providers

class Client:
 supports_tools=False
 def __init__(self,kind,fail=False):self.kind=kind;self.profile=kind;self.calls=0;self.fail=fail
 def chat(self,*args,**kwargs):
  self.calls+=1
  if self.fail:raise providers.ProviderError('unavailable')
  return {'content':'instrumented answer'}

@pytest.fixture
def no_tools(monkeypatch):
 monkeypatch.setattr(agent,'route_modules',lambda *a,**kw:[])
 monkeypatch.setattr(agent,'tools_for_modules',lambda *a,**kw:[])

def test_hosted_profile_refused(no_tools,monkeypatch):
 c=Client('hosted_free');monkeypatch.setattr(agent,'resolve',lambda *a,**kw:c)
 r=agent.ask('private canary',profile='hosted',private=True)
 assert r.answer is None and c.calls==0

def test_hosted_fallback_never_called(no_tools,monkeypatch):
 local=Client('local',True);hosted=Client('hosted_paid')
 monkeypatch.setattr(agent,'resolve_route',lambda **kw:([local,hosted],[]))
 r=agent.ask('private canary',private=True)
 assert r.answer is None and local.calls==1 and hosted.calls==0

def test_resolver_filters_before_construction(monkeypatch):
 profiles={'local':SimpleNamespace(kind='local'),'hosted':SimpleNamespace(kind='hosted_free')}
 calls=[]
 monkeypatch.setattr(providers,'load_profiles',lambda env:profiles)
 monkeypatch.setattr(providers,'resolve',lambda name,**kw:calls.append(name) or Client('local'))
 clients,skipped=providers.resolve_route(env={},route='local,hosted',private=True)
 assert calls==['local'] and len(clients)==1 and skipped

def test_cli_propagates_private(monkeypatch):
 from sugarcode import cli
 calls=[]
 monkeypatch.setattr(agent,'ask',lambda *a,**kw:calls.append(kw) or agent.AskResult('ok','local',[]))
 monkeypatch.setattr(cli,'_emit',lambda *a:None)
 assert cli.main(['ask','canary','--private'])==0 and calls[0]['private'] is True

def test_nonprivate_unchanged(no_tools,monkeypatch):
 c=Client('hosted_free');monkeypatch.setattr(agent,'resolve_route',lambda **kw:([c],[]))
 assert agent.ask('ordinary canary').answer=='instrumented answer' and c.calls==1
