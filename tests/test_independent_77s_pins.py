import json
from datetime import datetime,timezone
import pytest
from sugarcode.modules.nexus_support import store as h
T=datetime(2026,1,1,tzinfo=timezone.utc)

def rec():return h.TicketStore().open_ticket('test question',submitted_at=T)

def test_open_capacity_guard(monkeypatch):
    monkeypatch.setattr(h,'MAX_TICKETS',0)
    with pytest.raises(ValueError,match='store is full'):h.TicketStore().open_ticket('test question',submitted_at=T)

class Missing(dict):
    def __getitem__(self,key):raise AssertionError('missing id reached retrieval')

@pytest.mark.parametrize('method,args',[('get',()),('transition',('triaged',T)),('sla_status',(T,))])
def test_missing_id_checked_before_retrieval(method,args):
    s=h.TicketStore();s._t=Missing()
    with pytest.raises(KeyError):getattr(s,method)('none',*args)

def test_unknown_state_guard_stage():
    s=h.TicketStore();r=s.open_ticket('test question',submitted_at=T)
    with pytest.raises(ValueError,match='unknown state'):s.transition(r['ticket_id'],'bad',T)

def test_dump_cap_guard(monkeypatch):
    monkeypatch.setattr(h,'MAX_DUMP_CHARS',1)
    with pytest.raises(ValueError,match='dump too large'):h.TicketStore.loads('{}')

def test_ticket_count_cap_guard(monkeypatch):
    document=json.dumps({'version':1,'tickets':[rec()]})
    monkeypatch.setattr(h,'MAX_TICKETS',0)
    with pytest.raises(ValueError,match='too many tickets'):h.TicketStore.loads(document)

def test_initial_history_guard_precedes_stamp():
    r=rec();r['history']=[{'state':'closed','at':'bad'}]
    with pytest.raises(ValueError,match="history must start at 'new'"):h.TicketStore()._ingest(r)

def test_timestamp_text_guard():
    r=rec();r['history'][0]['at']=1
    with pytest.raises(ValueError,match='timestamp must be text'):h.TicketStore()._ingest(r)

def test_timestamp_timezone_guard():
    r=rec();r['history'][0]['at']='2026-01-01T00:00:00'
    with pytest.raises(ValueError,match='timestamp must carry a timezone'):h.TicketStore()._ingest(r)

class StateProbe(dict):
    def get(self,k,*a):return 'new' if k=='state' else super().get(k,*a)

def test_iteration_first_state_rechecked():
    r=rec();r['state']='closed';r['history']=[StateProbe(state='closed',at=T.isoformat())]
    with pytest.raises(ValueError,match="history must start at 'new'"):h.TicketStore()._ingest(r)
