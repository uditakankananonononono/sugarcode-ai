"""Unit 77s second-look pins (tests only, PARTIAL): survivors of an independent AST-mutation sweep of
nexus_support/store.py. Expected values are literals from the store's documented limits (MAX_TICKETS=10_000,
MAX_INQUIRY_CHARS=20_000, MAX_DUMP_CHARS=50_000_000, sla_hours in (0, 1_000_000]). Exact refusal messages are
matched so message-only mutants die too. No claim beyond the store's toy ticket arithmetic."""
import copy
import json
from datetime import datetime, timedelta, timezone

import pytest

from sugarcode.modules.nexus_support import store as st
from sugarcode.modules.nexus_support.store import TicketStore

T0 = datetime(2026, 9, 22, 12, 0, tzinfo=timezone.utc)
Q = "How do I score a CRISPR Opt PAM guide?"


def _base():
    s = TicketStore(); s.open_ticket(Q, submitted_at=T0)
    return json.loads(s.dumps())


def _load(doc):
    return TicketStore.loads(json.dumps(doc))


def _bad(doc, msg):
    with pytest.raises(ValueError) as e:
        _load(doc)
    assert str(e.value) == msg


def _many(n):
    doc = _base(); rec = doc["tickets"][0]
    doc["tickets"] = [dict(copy.deepcopy(rec), ticket_id=f"X{i:05d}") for i in range(n)]
    return doc


def test_limit_constants():
    assert (st.MAX_TICKETS, st.MAX_INQUIRY_CHARS, st.MAX_DUMP_CHARS) == (10_000, 20_000, 50_000_000)


def test_ticket_count_cap_exact_on_load_and_open():
    s = _load(_many(10_000)); assert len(s) == 10_000
    _bad(_many(10_001), "too many tickets")
    with pytest.raises(ValueError) as e:
        s.open_ticket("another unique question about PAM", submitted_at=T0 + timedelta(days=1))
    assert str(e.value) == "store is full (10000 tickets)" and len(s) == 10_000
    s9 = _load(_many(9_999))
    s9.open_ticket("another unique question about PAM", submitted_at=T0 + timedelta(days=1)); assert len(s9) == 10_000


def test_inquiry_cap_exact():
    s = TicketStore()
    s.open_ticket("a" * 20_000, submitted_at=T0)
    with pytest.raises(ValueError) as e:
        s.open_ticket("a" * 20_001, submitted_at=T0)
    assert str(e.value) == "inquiry exceeds 20000 characters"


def test_dump_size_cap_exact():
    text = json.dumps(_base())
    pad = 50_000_000 - len(text)
    assert TicketStore.loads(text + " " * pad) is not None            # exactly 50_000_000 chars accepted
    with pytest.raises(ValueError) as e:
        TicketStore.loads(text + " " * (pad + 1))
    assert str(e.value) == "dump too large"


def test_dumps_keys_sorted():
    s = TicketStore(); s.open_ticket(Q, submitted_at=T0)
    t = s.dumps()
    assert t == json.dumps(json.loads(t), sort_keys=True)


def test_breaches_evaluates_ticket_whose_latest_event_equals_now_and_skips_later_ones():
    s = TicketStore()
    a = s.open_ticket(Q, submitted_at=T0)["ticket_id"]            # due T0+24h
    s.transition(a, "triaged", T0 + timedelta(hours=1))
    s.transition(a, "in_progress", T0 + timedelta(hours=30))     # first response 6h late; latest event == now
    assert s.breaches(T0 + timedelta(hours=30)) == [a]            # tie is evaluated, not skipped (>= mutant)
    # latest event (30h) is after history[0] (0h): at now=5h it must be skipped, not raise
    assert s.breaches(T0 + timedelta(hours=5)) == []


def test_transition_time_rules():
    s = TicketStore(); t = s.open_ticket(Q, submitted_at=T0)["ticket_id"]
    s.transition(t, "triaged", T0 + timedelta(hours=1))
    s.transition(t, "in_progress", T0 + timedelta(hours=5))
    with pytest.raises(ValueError) as e:                           # earlier than the LAST event, later than the first
        s.transition(t, "resolved", T0 + timedelta(hours=2))
    assert str(e.value) == "transition time precedes the previous event"
    assert s.transition(t, "resolved", T0 + timedelta(hours=5))["state"] == "resolved"   # equal time allowed


def test_unknown_state_message():
    s = TicketStore(); t = s.open_ticket(Q, submitted_at=T0)["ticket_id"]
    with pytest.raises(ValueError) as e:
        s.transition(t, "bogus", T0 + timedelta(hours=1))
    assert str(e.value) == "unknown state 'bogus'"


@pytest.mark.parametrize("key,val", [("inquiry", 5), ("state", None), ("classification", 1), ("priority", []),
                                     ("tier", 2), ("submitted_at", 3), ("response_due_at", {}), ("history", "x"),
                                     ("routed_to", [])])
def test_wrong_type_field_refused(key, val):
    doc = _base(); doc["tickets"][0][key] = val
    _bad(doc, f"ticket field {key!r} missing or wrong type")
    doc = _base(); del doc["tickets"][0][key]
    _bad(doc, f"ticket field {key!r} missing or wrong type")


@pytest.mark.parametrize("key", ["priority_score", "sla_hours"])
@pytest.mark.parametrize("bad", [True, "1", None, float("nan"), float("inf"), float("-inf")])
def test_numeric_field_refused(key, bad):
    doc = _base(); doc["tickets"][0][key] = bad
    with pytest.raises(ValueError) as e:
        TicketStore.loads(json.dumps(doc))   # json.dumps emits NaN/Infinity tokens; json.loads accepts them
    assert str(e.value) == f"ticket field {key!r} must be a finite number"


def test_bad_state_and_duplicate_id_message():
    doc = _base(); doc["tickets"][0]["state"] = "bogus"
    _bad(doc, "bad state or duplicate ticket id")
    doc = _base(); doc["tickets"].append(copy.deepcopy(doc["tickets"][0]))
    _bad(doc, "bad state or duplicate ticket id")


def test_history_start_message():
    doc = _base(); doc["tickets"][0]["history"][0]["state"] = "triaged"
    _bad(doc, "history must start at 'new'")


def test_timestamp_text_and_timezone_messages():
    doc = _base(); doc["tickets"][0]["history"][0]["at"] = 5
    _bad(doc, "timestamp must be text")
    doc = _base(); doc["tickets"][0]["history"][0]["at"] = "2026-09-22T12:00:00"
    _bad(doc, "timestamp must carry a timezone")
    doc = _base(); doc["tickets"][0]["history"][0]["at"] = "not a time"
    _bad(doc, "malformed timestamp")


def _two_event_doc(second_at, second_state="triaged"):
    doc = _base(); rec = doc["tickets"][0]
    rec["history"].append({"state": second_state, "at": second_at}); rec["state"] = second_state
    return doc


def test_history_order_equal_allowed_earlier_refused_illegal_edge_refused():
    assert len(_load(_two_event_doc(T0.isoformat()))) == 1                       # equal stamps are legal
    _bad(_two_event_doc((T0 - timedelta(seconds=1)).isoformat()), "history is not a legal ordered path")
    _bad(_two_event_doc((T0 + timedelta(hours=1)).isoformat(), "resolved"), "history is not a legal ordered path")
    _bad(_two_event_doc("2026-09-22T13:00:00+00:00", "in_progress"), "history is not a legal ordered path")


def test_state_and_submitted_mismatch_messages():
    doc = _base(); doc["tickets"][0]["state"] = "triaged"
    _bad(doc, "state does not match history")
    doc = _base(); doc["tickets"][0]["submitted_at"] = (T0 + timedelta(hours=1)).isoformat()
    _bad(doc, "submitted_at does not match history[0]")


def _sla_doc(h, submitted=T0):
    doc = _base(); rec = doc["tickets"][0]
    rec["sla_hours"] = h; rec["submitted_at"] = submitted.isoformat()
    rec["history"] = [{"state": "new", "at": submitted.isoformat()}]
    rec["response_due_at"] = (submitted + timedelta(hours=h)).isoformat()
    return doc


@pytest.mark.parametrize("h", [0.5, 0.001, 1, 1_000_000])
def test_sla_hours_accepted(h):
    assert len(_load(_sla_doc(h))) == 1


@pytest.mark.parametrize("h", [0, -1, 1_000_001, 1_000_000.5])
def test_sla_hours_refused(h):
    doc = _sla_doc(1); doc["tickets"][0]["sla_hours"] = h
    _bad(doc, "sla_hours out of range")


def test_sla_overflow_and_due_mismatch_messages():
    far = datetime(9999, 6, 1, tzinfo=timezone.utc)
    doc = _sla_doc(1); rec = doc["tickets"][0]
    rec["sla_hours"] = 1_000_000; rec["submitted_at"] = far.isoformat()
    rec["history"] = [{"state": "new", "at": far.isoformat()}]
    _bad(doc, "sla_hours out of range")
    doc = _sla_doc(2); doc["tickets"][0]["response_due_at"] = (T0 + timedelta(hours=3)).isoformat()
    _bad(doc, "response_due_at inconsistent with submitted_at + sla_hours")
