"""Tests-only hardening for row 448 route(): every refusal pinned to its exact full message.
Message strings are the module's own; each case is built so only that one check can fire."""
import re
import pytest
from sugarcode.extra_doc.support_routing448 import route

Q = '1..8 queues before scan'
S = '0..64 starts before scan'
PAIR = 'queue pair cost outgoing'
OUT8 = '0..8 outgoing before scan'
COST = 'terminal cost None or bounded integer'
IDX = 'valid integer outgoing indices'
UNI = 'unique outgoing indices'
SIDX = 'valid integer starting indices'


class L(list):
    pass


class T2(tuple):
    pass


class I(int):
    pass


def refuse(msg, qs, ss):
    with pytest.raises(ValueError) as e:
        route(qs, ss)
    assert re.fullmatch(re.escape(msg), str(e.value)), str(e.value)


@pytest.mark.parametrize('qs', [None, (), [], [(0, [])] * 9, L([(0, [])]), ((0, []),)])
def test_queue_count_and_type(qs):
    refuse(Q, qs, [])


@pytest.mark.parametrize('ss', [None, (), [0] * 65, L([0])])
def test_starts_count_and_type(ss):
    refuse(S, [(0, [])], ss)


@pytest.mark.parametrize('qs', [
    [[0, []]], [(0,)], [(0, [], None)], [()], [{0: 0, 1: []}],
    [(0, []), (0,)], [(0, []), [0, []]], [(0, []), (0, [], 0)]])
def test_pair_shape(qs):
    refuse(PAIR, qs, [])


def test_pair_subclass_refused():
    refuse(PAIR, [T2((0, []))], [])


@pytest.mark.parametrize('qs', [
    [(0, None)], [(0, (0,))], [(0, L())], [(0, [0] * 9)], [(0, [0] * 9), (0, [])],
    [(0, []), (0, [0] * 9)], [(0, []), (0, None)]])
def test_outgoing_container_and_cap(qs):
    refuse(OUT8, qs, [])


def test_eight_outgoing_boundary_is_not_the_cap_message():
    q = [(None, list(range(8)))] + [(0, [])] * 7
    assert route(q, [0])['routes'][0]['terminal'] == 1


@pytest.mark.parametrize('bad', [True, False, 1.0, '0', -1, 10 ** 6 + 1, I(0)])
def test_cost_refusals_first_and_later(bad):
    refuse(COST, [(bad, [])], [])
    refuse(COST, [(0, []), (bad, [])], [])


@pytest.mark.parametrize('qs', [
    [(0, [True])], [(0, [0, True])], [(0, [-1])], [(0, [1])], [(0, ['0'])], [(0, [1.0])],
    [(0, [I(0)])], [(0, []), (0, [0, 2])], [(0, []), (0, [0, True])]])
def test_outgoing_index_refusals(qs):
    refuse(IDX, qs, [])


@pytest.mark.parametrize('qs', [[(0, [0, 0])], [(0, []), (0, [1, 0, 1])]])
def test_unique_outgoing(qs):
    refuse(UNI, qs, [])


@pytest.mark.parametrize('ss', [[True], [0, True], [-1], [1], ['0'], [1.0], [I(0)], [0, 0, 5]])
def test_start_index_refusals(ss):
    refuse(SIDX, [(0, [])], ss)


def test_order_of_checks_first_failure_wins():
    refuse(Q, None, None)
    refuse(PAIR, [(0,), (0, [0] * 9)], [])
    refuse(OUT8, [(0, [0] * 9), (True, [])], [])
    refuse(COST, [(True, [5])], [])
    refuse(IDX, [(0, [5, 5])], [])
    refuse(UNI, [(0, [0, 0])], [True])
