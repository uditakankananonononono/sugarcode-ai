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
