"""Auditor pins for row 1955 count_custodies (probed outputs)."""
from sugarcode.extra_doc import ai_regulation as mod


def test_pin_same_act_max_still_contested():
    # A raises its own s1 level to 7, but B ties the peak: contested, no leader
    rows = [('A', 's1', 5), ('A', 's1', 7), ('B', 's1', 7)]
    assert mod.count_custodies(rows) == {
        'total': 3, 'custodies': {}, 'count': 0,
        'contested': ['s1'], 'leader': None}


def test_pin_tied_custody_first_supplied_leads():
    # A takes s1 alone; A and B tie the s2 peak (contested); B takes s3 alone
    rows = [('A', 's1', 5), ('B', 's2', 6), ('B', 's3', 6), ('A', 's2', 6)]
    assert mod.count_custodies(rows) == {
        'total': 4, 'custodies': {'A': 1, 'B': 1}, 'count': 2,
        'contested': ['s2'], 'leader': 'A'}


def test_pin_late_act_can_still_lead():
    rows = [('A', 's1', 4), ('B', 's2', 9), ('A', 's3', 2), ('B', 's1', 4)]
    assert mod.count_custodies(rows) == {
        'total': 4, 'custodies': {'B': 1, 'A': 1}, 'count': 2,
        'contested': ['s1'], 'leader': 'A'}
