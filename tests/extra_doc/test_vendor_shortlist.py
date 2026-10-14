"""Exhaustive small-score oracle, separate from the shipped selection code."""
import itertools
import re
import pytest
from sugarcode.extra_doc.vendor_shortlist import shortlist

class Number(int): pass
class Items(tuple): pass

def oracle(scores, minimum):
    chosen = []
    best = scores[0]
    for position, value in enumerate(scores):
        if value >= minimum:
            chosen.append(position)
        if value > best:
            best = value
    ties = []
    for position, value in enumerate(scores):
        if value == best:
            ties.append(position)
    return {'vendor_shortlist_validated': False,
            'not_claimed': ('score_validity','supplier_quality','selection_advice'),
            'qualified_positions': tuple(chosen), 'qualified_count': len(chosen),
            'any_qualified': bool(chosen), 'best_score': best, 'best_positions': tuple(ties)}

def refuse(scores, minimum, message):
    with pytest.raises(ValueError, match=re.escape(message)+'$') as exc:
        shortlist(scores, minimum)
    assert re.fullmatch(re.escape(message),str(exc.value))

def test_independent_exhaustive_oracle():
    for n in (2,3,4):
        for scores in itertools.product((0,1,50,100),repeat=n):
            for threshold in (0,1,49,50,51,99,100):
                assert shortlist(scores,threshold) == oracle(scores,threshold)

def test_caps_and_position_pins():
    for scores in ((0,)*15, (100,)*15, (0,100), (100,0), (1,1), tuple(range(15)), tuple(reversed(range(15)))):
        for threshold in (0,1,14,100):
            assert shortlist(scores,threshold) == oracle(scores,threshold)

def test_container_types_and_lengths():
    for scores in ((), (1,), (1,)*16, [1,2], Items((1,2)), None, 'éЖ'):
        refuse(scores,0,'scores: tuple of 2 to 15 entries required')

def test_score_types_and_bounds_at_all_positions():
    for pos in (0,1,14):
        for value in (-1,101,False,True,None,1.0,Number(1),'é','ａ','Ж','1'):
            scores = [1]*15; scores[pos] = value
            refuse(tuple(scores),1,f'scores[{pos}]: whole number 0 to 100 required')

def test_minimum_types_and_bounds():
    for value in (-1,101,True,False,None,1.0,Number(1),'é','ａ','Ж'):
        refuse((0,100),value,'minimum: whole number 0 to 100 required')

def test_order():
    refuse((None,)*16,None,'scores: tuple of 2 to 15 entries required')
    refuse((None,101),None,'scores[0]: whole number 0 to 100 required')
    refuse((0,101),None,'scores[1]: whole number 0 to 100 required')
