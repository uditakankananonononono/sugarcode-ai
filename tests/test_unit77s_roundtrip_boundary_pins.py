import json
from datetime import datetime,timedelta,timezone
import pytest
from sugarcode.modules.nexus_support import store as m
T=datetime(2026,1,1,tzinfo=timezone.utc)

@pytest.mark.parametrize('inquiry,tier,hours',[
 ('urgent security breach asap critical','startup',1.14),
 ('urgent security breach asap critical','academic',1.14),
 ('bug crash error urgent','startup',4.57),
 ('bug crash error urgent','enterprise',2.29),
 ('bug crash error urgent','academic',4.57),
 ('URGENT!!! outage production down critical bug asap now emergency','startup',3.56),
 ('URGENT!!! outage production down critical bug asap now emergency','enterprise',1.78),
 ('URGENT!!! outage production down critical bug asap now emergency','academic',3.56)])
def test_urgent_deadline_uses_displayed_sla_and_roundtrips(inquiry,tier,hours):
    s=m.TicketStore();r=s.open_ticket(inquiry,tier=tier,submitted_at=T)
    assert r['sla_hours']==hours
    assert r['response_due_at']==(T+timedelta(hours=hours)).isoformat()
    assert m.TicketStore.loads(s.dumps()).get(r['ticket_id'])==r


def test_inquiry_limit_exact_and_transition_same_timestamp():
    s=m.TicketStore();r=s.open_ticket('x'*20000,submitted_at=T)
    s.transition(r['ticket_id'],'triaged',T)
    assert m.TicketStore.loads(s.dumps()).get(r['ticket_id'])['state']=='triaged'
    with pytest.raises(ValueError,match='exceeds'):s.open_ticket('x'*20001,submitted_at=T)

@pytest.mark.parametrize('hours,valid',[(0,False),(1000000,True),(1000001,False)])
def test_sla_admission_upper_and_lower_exact(hours,valid):
    s=m.TicketStore();r=s.open_ticket('question',submitted_at=T)
    r['sla_hours']=hours;r['response_due_at']=(T+timedelta(hours=hours)).isoformat()
    if valid:assert m.TicketStore.loads(json.dumps({'version':1,'tickets':[r]})).get(r['ticket_id'])['sla_hours']==hours
    else:
        with pytest.raises(ValueError,match='out of range'):m.TicketStore()._ingest(r)


def test_exact_loaded_capacity_and_dump_character_limit(monkeypatch):
    s=m.TicketStore();s.open_ticket('question',submitted_at=T)
    text=s.dumps()
    monkeypatch.setattr(m,'MAX_TICKETS',1)
    monkeypatch.setattr(m,'MAX_DUMP_CHARS',len(text))
    assert len(m.TicketStore.loads(text))==1


def test_breach_at_latest_event_equality():
    s=m.TicketStore();r=s.open_ticket('question',submitted_at=T)
    now=T+timedelta(hours=30)
    s.transition(r['ticket_id'],'triaged',now)
    assert s.breaches(now)==[r['ticket_id']]

def test_store_capacity_declared10000(monkeypatch):
    class Records(dict):
        def __init__(self,size):super().__init__();self.size=size
        def __len__(self):return self.size
    s=m.TicketStore();s._t=Records(9999)
    assert s.open_ticket('question',submitted_at=T)['state']=='new'
    s._t=Records(10000)
    with pytest.raises(ValueError,match='store is full'):s.open_ticket('question',submitted_at=T)

@pytest.mark.parametrize('size,valid',[(50000000,True),(50000001,False)])
def test_declared_dump_character_cap_without_large_allocation(monkeypatch,size,valid):
    class SizedText(str):
        def __len__(self):return size
    text=SizedText('{"version":1,"tickets":[]}')
    loads=json.loads
    monkeypatch.setattr(m.json,'loads',lambda value:loads(str(value)))
    if valid:assert len(m.TicketStore.loads(text))==0
    else:
        with pytest.raises(ValueError,match='dump too large'):m.TicketStore.loads(text)

def test_whitespace_and_default_now(monkeypatch):
    class Clock(datetime):
        @classmethod
        def now(cls,tz):return T
    monkeypatch.setattr(m,'datetime',Clock)
    with pytest.raises(ValueError):m.TicketStore().open_ticket('   ')
    r=m.TicketStore().open_ticket('question')
    assert r['submitted_at']==T.isoformat() and r['response_due_at']==(T+timedelta(hours=24)).isoformat()


def test_latest_transition_time_and_first_response_value():
    s=m.TicketStore();r=s.open_ticket('question',submitted_at=T);tid=r['ticket_id']
    s.transition(tid,'triaged',T+timedelta(hours=2))
    with pytest.raises(ValueError,match='previous event'):s.transition(tid,'in_progress',T+timedelta(hours=1))
    s.transition(tid,'in_progress',T+timedelta(hours=3))
    s.transition(tid,'waiting_customer',T+timedelta(hours=30))
    assert s.sla_status(tid,T+timedelta(hours=31))['first_response_at']==(T+timedelta(hours=3)).isoformat()
    assert s.breaches(T+timedelta(hours=25))==[]

@pytest.mark.parametrize('document',[{'version':1,'tickets':{}},{'version':1,'tickets':None}])
def test_nonlist_persisted_tickets_are_value_error(document):
    with pytest.raises(ValueError,match='unsupported store document'):m.TicketStore.loads(json.dumps(document))

@pytest.mark.parametrize('field,value',[('priority_score',True),('priority_score','1'),('sla_hours',True),('sla_hours','1')])
def test_persisted_numbers_type_refusal(field,value):
    r=m.TicketStore().open_ticket('question',submitted_at=T);r[field]=value
    with pytest.raises(ValueError,match='finite number'):m.TicketStore()._ingest(r)


def test_nondict_first_history_and_unhashable_state_refusal():
    r=m.TicketStore().open_ticket('question',submitted_at=T)
    r['history']=[1]
    with pytest.raises(ValueError,match='history must start'):m.TicketStore()._ingest(r)
    r=m.TicketStore().open_ticket('question',submitted_at=T)
    r['history'].append({'state':[1],'at':T.isoformat()})
    with pytest.raises(ValueError,match='malformed history event'):m.TicketStore()._ingest(r)


def test_exact_one_hour_sla_accepted():
    r=m.TicketStore().open_ticket('question',submitted_at=T)
    r['sla_hours']=1.;r['response_due_at']=(T+timedelta(hours=1)).isoformat()
    s=m.TicketStore.loads(json.dumps({'version':1,'tickets':[r]}))
    assert s.get(r['ticket_id'])['sla_hours']==1.
