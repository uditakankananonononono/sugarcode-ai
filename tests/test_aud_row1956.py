"""Auditor pins for row 1956 count_anchors (probed outputs)."""
from sugarcode.extra_doc import ai_policy as mod


def test_pin_shared_pillar_excluded():
    # x1 scored by A and B -> shared; x2 anchored by A alone
    rows = [('A', 'x1', 5), ('B', 'x1', 9), ('A', 'x2', 3)]
    assert mod.count_anchors(rows) == {
        'total': 3, 'anchors': {'A': 1}, 'count': 1,
        'shared': ['x1'], 'leader': 'A'}


def test_pin_most_anchors_leads():
    rows = [('A', 'x1', 5), ('A', 'x2', 5), ('B', 'x3', 5),
            ('B', 'x4', 5), ('B', 'x5', 5)]
    assert mod.count_anchors(rows) == {
        'total': 5, 'anchors': {'A': 2, 'B': 3}, 'count': 5,
        'shared': [], 'leader': 'B'}


def test_pin_all_shared_no_leader():
    rows = [('A', 'x1', 1), ('B', 'x1', 2), ('C', 'x1', 3)]
    assert mod.count_anchors(rows) == {
        'total': 3, 'anchors': {}, 'count': 0,
        'shared': ['x1'], 'leader': None}
