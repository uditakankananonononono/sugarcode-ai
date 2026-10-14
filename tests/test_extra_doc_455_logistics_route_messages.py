"""Tests-only hardening for row 455 best_tour(): exact full error messages, status note, tuple input,
and bad entries away from the first position."""
import re
import pytest
from sugarcode.extra_doc import logistics_route as lr

T = lr.best_tour


def refuse(msg, d):
    with pytest.raises(ValueError) as e:
        T(d)
    assert re.fullmatch(re.escape(msg), str(e.value)), str(e.value)


def test_status_note_exact():
    r = T([[0, 5], [7, 0]])
    assert r["status_note"] == lr.STATUS_NOTE
    assert lr.STATUS_NOTE == ("PARTIAL: exact cheapest round trip over a supplied cost matrix only; "
                              "no time windows, capacities, vehicles or traffic")
    assert set(r) == {"cost", "order", "stops", "status_note"}


@pytest.mark.parametrize("d", ["ab", None, 5, {0: [0]}, {0: 0, 1: 1}])
def test_outer_type(d):
    refuse("dist: list required", d)


@pytest.mark.parametrize("n", [0, 1, 13])
def test_stop_count(n):
    refuse("dist: 2 to 12 stops required", [[0] * n for _ in range(n)])


def test_row_type_any_position():
    refuse("dist[1]: list required", [[0, 1], "ab"])
    refuse("dist[0]: list required", ["ab", [0, 1]])
    refuse("dist[2]: list required", [[0, 1, 2], [1, 0, 1], None])


def test_row_length_any_position():
    refuse("dist[1]: 2 entries required", [[0, 1], [1]])
    refuse("dist[0]: 2 entries required", [[0, 1, 2], [1, 0, 1]])
    refuse("dist[2]: 3 entries required", [[0, 1, 2], [1, 0, 1], [1, 0]])


def test_shape_checked_before_entries():
    refuse("dist[1]: 2 entries required", [[0, "x"], [1]])


@pytest.mark.parametrize("bad", [True, False, 1.0, "1", None, 2 ** 70 * 1.0])
def test_entry_type(bad):
    refuse("dist[1][0]: integer required", [[0, 1], [bad, 0]])
    refuse("dist[2][1]: integer required", [[0, 1, 1], [1, 0, 1], [1, bad, 0]])
    refuse("dist[0][0]: integer required", [[bad, 1], [1, 0]])


@pytest.mark.parametrize("bad", [-1, 1_000_001, 10 ** 12])
def test_entry_range(bad):
    refuse("dist[0][1]: must be within 0 to 1000000", [[0, bad], [1, 0]])
    refuse("dist[2][2]: must be within 0 to 1000000", [[0, 1, 1], [1, 0, 1], [1, 1, bad]])


def test_entry_type_checked_before_range_in_scan_order():
    refuse("dist[0][1]: must be within 0 to 1000000", [[0, -1], [True, 0]])
    refuse("dist[0][1]: integer required", [[0, True], [-1, 0]])


def test_tuple_matrix_accepted_and_inputs_not_mutated():
    d = ((0, 5), (7, 0))
    assert T(d)["cost"] == 12
    m = [[0, 2, 9], [1, 0, 6], [3, 5, 0]]
    before = [r[:] for r in m]
    T(m)
    assert m == before


def test_boundary_values_accepted():
    assert T([[0, 1_000_000], [0, 0]])["cost"] == 1_000_000
    assert T([[0] * 12 for _ in range(12)])["stops"] == 12
