"""Tests for nexus_support.store (unit 77s). Oracle: integer microseconds / Fraction
and an independently coded reference state machine (edge list below)."""
import json
from datetime import datetime, timedelta, timezone
from fractions import Fraction

import pytest

from sugarcode.modules.nexus_support.store import STATES, TicketStore

T0 = datetime(2026, 9, 22, 12, 0, tzinfo=timezone.utc)
Q = "How do I score a CRISPR Opt PAM guide?"  # question, sla 24h startup, urgency 0

# independent reference: allowed edges written out by hand from the design table
EDGES = {("new", "triaged"), ("new", "closed"), ("triaged", "in_progress"),
         ("triaged", "resolved"), ("triaged", "closed"), ("in_progress", "waiting_customer"),
         ("in_progress", "resolved"), ("waiting_customer", "in_progress"),
         ("waiting_customer", "resolved"), ("waiting_customer", "closed"),
         ("resolved", "in_progress"), ("resolved", "closed")}


def _store_in_state(state):
    s = TicketStore(); t = s.open_ticket(Q, submitted_at=T0)["ticket_id"]
    paths = {"new": [], "triaged": ["triaged"], "in_progress": ["triaged", "in_progress"],
             "waiting_customer": ["triaged", "in_progress", "waiting_customer"],
             "resolved": ["triaged", "resolved"], "closed": ["triaged", "closed"]}
    for i, st in enumerate(paths[state]):
        s.transition(t, st, T0 + timedelta(minutes=i + 1))
    return s, t


@pytest.mark.parametrize("a", STATES)
@pytest.mark.parametrize("b", STATES)
def test_transition_matrix_matches_reference(a, b):
    s, t = _store_in_state(a)
    if (a, b) in EDGES:
        assert s.transition(t, b, T0 + timedelta(hours=1))["state"] == b
    else:
        with pytest.raises(ValueError):
            s.transition(t, b, T0 + timedelta(hours=1))
        assert s.get(t)["state"] == a  # validate before mutate


def test_open_ticket_uses_triage_and_rejects_bad_input():
    s = TicketStore(); r = s.open_ticket(Q, submitted_at=T0)
    assert r["state"] == "new" and r["classification"] == "question"
    assert r["sla_hours"] == 24 and r["response_due_at"] == (T0 + timedelta(hours=24)).isoformat()
    for bad in ("", "   ", None, 5, b"x"):
        with pytest.raises(ValueError):
            s.open_ticket(bad)
    with pytest.raises(ValueError):
        s.open_ticket("x" * 20_001)
    with pytest.raises(ValueError):
        s.open_ticket(Q, submitted_at=T0)  # same id (same text and time)
    with pytest.raises(TypeError):
        s.open_ticket("hello", submitted_at="2026-01-01")
    assert len(s) == 1


def test_get_returns_copy():
    s = TicketStore(); t = s.open_ticket(Q, submitted_at=T0)["ticket_id"]
    s.get(t)["state"] = "closed"; s.get(t)["history"].clear()
    assert s.get(t)["state"] == "new" and len(s.get(t)["history"]) == 1
    with pytest.raises(KeyError):
        s.get("NXS-NOPE")


def test_time_must_not_go_backwards_and_must_be_datetime():
    s = TicketStore(); t = s.open_ticket(Q, submitted_at=T0)["ticket_id"]
    with pytest.raises(ValueError):
        s.transition(t, "triaged", T0 - timedelta(seconds=1))
    with pytest.raises(TypeError):
        s.transition(t, "triaged", "now")
    assert s.get(t)["state"] == "new"


def test_sla_margin_exact_before_and_after_response():
    s = TicketStore(); t = s.open_ticket(Q, submitted_at=T0)["ticket_id"]
    now = T0 + timedelta(hours=10, microseconds=7)
    st = s.sla_status(t, now)
    due_us = 24 * 3_600_000_000; now_us = 10 * 3_600_000_000 + 7
    assert Fraction(st["margin_hours_exact"]) == Fraction(due_us - now_us, 3_600_000_000)
    assert not st["responded"] and not st["breached"]
    s.transition(t, "triaged", T0 + timedelta(hours=1))
    s.transition(t, "in_progress", T0 + timedelta(hours=30))  # late response
    st = s.sla_status(t, T0 + timedelta(hours=31))
    assert st["responded"] and st["breached"]
    assert Fraction(st["margin_hours_exact"]) == Fraction(-6)


def test_exact_deadline_is_not_a_breach_one_microsecond_later_is():
    s = TicketStore(); t = s.open_ticket(Q, submitted_at=T0)["ticket_id"]
    due = T0 + timedelta(hours=24)
    assert not s.sla_status(t, due)["breached"]
    assert s.sla_status(t, due + timedelta(microseconds=1))["breached"]


def test_breaches_list_and_future_ticket_skipped():
    s = TicketStore()
    a = s.open_ticket(Q, submitted_at=T0)["ticket_id"]
    b = s.open_ticket("How do I score a PAM guide?", submitted_at=T0 + timedelta(hours=40))["ticket_id"]
    assert s.breaches(T0 + timedelta(hours=25)) == [a]  # b submitted later, skipped
    assert s.breaches(T0 + timedelta(hours=100)) == sorted([a, b])
    s.transition(a, "triaged", T0 + timedelta(hours=1)); s.transition(a, "in_progress", T0 + timedelta(hours=2))
    assert s.breaches(T0 + timedelta(hours=100)) == [b]
    with pytest.raises(ValueError):
        s.sla_status(a, T0)  # now before latest event


def test_naive_datetime_treated_as_utc_and_other_zone_normalised():
    s = TicketStore()
    t = s.open_ticket(Q, submitted_at=datetime(2026, 9, 22, 12, 0))["ticket_id"]
    ist = timezone(timedelta(hours=5, minutes=30))
    st = s.sla_status(t, datetime(2026, 9, 22, 17, 30, tzinfo=ist))  # == 12:00 UTC
    assert Fraction(st["margin_hours_exact"]) == 24


def test_counts_and_roundtrip():
    s, t = _store_in_state("waiting_customer"); s.open_ticket("Another question about PAM?", submitted_at=T0)
    assert s.counts()["waiting_customer"] == 1 and s.counts()["new"] == 1 and sum(s.counts().values()) == 2
    s2 = TicketStore.loads(s.dumps())
    assert s2.dumps() == s.dumps() and s2.get(t) == s.get(t)


@pytest.mark.parametrize("mut", [
    lambda d: d.update(version=2),
    lambda d: d.update(tickets="x"),
    lambda d: d["tickets"][0].update(state="bogus"),
    lambda d: d["tickets"][0].update(state="closed"),  # history disagrees
    lambda d: d["tickets"][0].update(sla_hours=True),
    lambda d: d["tickets"][0].update(sla_hours=float("nan")),
    lambda d: d["tickets"][0].update(priority_score=1e999),
    lambda d: d["tickets"][0].update(history=[]),
    lambda d: d["tickets"][0]["history"].append({"state": "new", "at": T0.isoformat()}),
    lambda d: d["tickets"][0]["history"][0].update(at="not-a-date"),
    lambda d: d["tickets"].append(d["tickets"][0]),  # duplicate id
    lambda d: d["tickets"].append(5),
    lambda d: d["tickets"][0].pop("inquiry"),
])
def test_loads_rejects_tampered_documents(mut):
    s = TicketStore(); s.open_ticket(Q, submitted_at=T0)
    d = json.loads(s.dumps()); mut(d)
    with pytest.raises(ValueError):
        TicketStore.loads(json.dumps(d).replace("Infinity", "1e999"))


def test_loads_rejects_garbage_and_wrong_type():
    for bad in ("", "{", "[]", "null", "[" * 100000):
        with pytest.raises(ValueError):
            TicketStore.loads(bad)
    with pytest.raises(TypeError):
        TicketStore.loads(b"{}")


def test_direct_resolution_counts_as_first_response():
    s = TicketStore(); t = s.open_ticket(Q, submitted_at=T0)["ticket_id"]
    s.transition(t, "triaged", T0 + timedelta(hours=1))
    s.transition(t, "resolved", T0 + timedelta(hours=2))
    st = s.sla_status(t, T0 + timedelta(hours=500))
    assert st["responded"] and not st["breached"] and Fraction(st["margin_hours_exact"]) == 22
    assert s.breaches(T0 + timedelta(hours=500)) == []


def test_first_response_time_is_first_response_state_not_later_ones():
    s = TicketStore(); t = s.open_ticket(Q, submitted_at=T0)["ticket_id"]
    s.transition(t, "triaged", T0 + timedelta(hours=1))
    s.transition(t, "in_progress", T0 + timedelta(hours=3))
    s.transition(t, "waiting_customer", T0 + timedelta(hours=40))
    assert Fraction(s.sla_status(t, T0 + timedelta(hours=50))["margin_hours_exact"]) == 21  # first response at 3h


def test_loads_rejects_out_of_order_history_times():
    s = TicketStore(); t = s.open_ticket(Q, submitted_at=T0)["ticket_id"]
    s.transition(t, "triaged", T0 + timedelta(hours=2))
    d = json.loads(s.dumps()); d["tickets"][0]["history"][1]["at"] = (T0 - timedelta(hours=1)).isoformat()
    with pytest.raises(ValueError):
        TicketStore.loads(json.dumps(d))


# ---- v2: aware timestamps and due-date consistency (auditor-7 finding) ----
def _doc(store):
    return json.loads(store.dumps())


def _one():
    s = TicketStore(); t = s.open_ticket(Q, submitted_at=T0)["ticket_id"]
    s.transition(t, "triaged", T0 + timedelta(hours=1))
    return s, t


@pytest.mark.parametrize("edit", [
    lambda r: r["history"][0].update(at="2026-09-22T12:00:00"),
    lambda r: r.update(submitted_at="2026-09-22T12:00:00"),
    lambda r: r.update(response_due_at="2026-09-23T12:00:00"),
    lambda r: r["history"][1].update(at="2026-09-22T13:00:00"),
])
def test_naive_timestamps_rejected_on_load_not_later_typeerror(edit):
    s, _ = _one(); d = _doc(s); edit(d["tickets"][0])
    with pytest.raises(ValueError):
        TicketStore.loads(json.dumps(d))


@pytest.mark.parametrize("edit", [
    lambda r: r.update(response_due_at="2099-01-01T00:00:00+00:00"),
    lambda r: r.update(response_due_at=(T0 + timedelta(hours=24, microseconds=1)).isoformat()),
    lambda r: r.update(submitted_at=(T0 + timedelta(hours=1)).isoformat()),
    lambda r: r.update(sla_hours=25),
    lambda r: r.update(sla_hours=0),
    lambda r: r.update(sla_hours=-24),
    lambda r: r.update(sla_hours=10**9),
])
def test_due_date_must_equal_submitted_plus_sla(edit):
    s, _ = _one(); d = _doc(s); edit(d["tickets"][0])
    with pytest.raises(ValueError):
        TicketStore.loads(json.dumps(d))


def test_loaded_offset_timestamps_are_normalised_and_usable():
    ist = timezone(timedelta(hours=5, minutes=30))
    s, t = _one(); d = _doc(s); r = d["tickets"][0]
    r["submitted_at"] = T0.astimezone(ist).isoformat()
    r["history"][0]["at"] = T0.astimezone(ist).isoformat()
    r["response_due_at"] = (T0 + timedelta(hours=24)).astimezone(ist).isoformat()
    s2 = TicketStore.loads(json.dumps(d))
    assert s2.get(t)["submitted_at"] == T0.isoformat()
    assert s2.get(t)["history"][0]["at"] == T0.isoformat()
    assert Fraction(s2.sla_status(t, T0 + timedelta(hours=2))["margin_hours_exact"]) == 22
    assert s2.dumps() == s.dumps()


@pytest.mark.parametrize("bad", [["triaged"], {"a": 1}, None, 5, b"closed", ("closed",)])
def test_transition_state_must_be_string(bad):
    s, t = _one()
    with pytest.raises(TypeError):
        s.transition(t, bad, T0 + timedelta(hours=2))
    assert s.get(t)["state"] == "triaged"


def test_loads_rejects_non_dict_history_events():
    s, _ = _one(); d = _doc(s); d["tickets"][0]["history"][1] = "x"
    with pytest.raises(ValueError):
        TicketStore.loads(json.dumps(d))


def test_submitted_must_match_first_history_event_even_if_due_is_consistent():
    s, _ = _one(); d = _doc(s); r = d["tickets"][0]
    shifted = T0 + timedelta(hours=3)
    r["submitted_at"] = shifted.isoformat()
    r["response_due_at"] = (shifted + timedelta(hours=r["sla_hours"])).isoformat()
    with pytest.raises(ValueError):
        TicketStore.loads(json.dumps(d))


def test_sla_hours_upper_bound_even_when_due_is_consistent():
    s, _ = _one(); d = _doc(s); r = d["tickets"][0]
    r["sla_hours"] = 2_000_000
    r["response_due_at"] = (T0 + timedelta(hours=2_000_000)).isoformat()
    with pytest.raises(ValueError):
        TicketStore.loads(json.dumps(d))
