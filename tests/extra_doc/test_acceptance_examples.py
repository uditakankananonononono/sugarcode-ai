import itertools
import re
import pytest
from sugarcode.extra_doc.acceptance_examples import examples
class Number(int): pass
class Items(tuple): pass

def oracle(cases):
    mismatch=[];diff=[];matched=0
    for i,(expected,observed) in enumerate(cases):
        if expected==observed: matched+=1
        else: mismatch.append(i)
        diff.append(observed-expected)
    return {'acceptance_examples_validated':False,
            'not_claimed':('user_acceptance','test_generation','software_validation'),
            'mismatch_positions':tuple(mismatch),'differences':tuple(diff),
            'matched_count':matched,'all_match':matched==len(cases)}

def refuse(cases,message):
    with pytest.raises(ValueError) as exc: examples(cases)
    assert re.fullmatch(re.escape(message),str(exc.value))

def test_oracle():
    pairs=tuple(itertools.product((-1000,0,1,1000),repeat=2))
    for n in (1,2,3):
        for cases in itertools.product(pairs,repeat=n): assert examples(cases)==oracle(cases)

def test_caps_first_last():
    for cases in (((-1000,1000),)*30,((0,0),)*30,((0,1),)+((0,0),)*29,((0,0),)*29+((1,0),)):
        assert examples(cases)==oracle(cases)

def test_outer():
    for bad in ((),(None,)*31,[(0,0)],Items(((0,0),)),None,'é'):
        refuse(bad,'cases: tuple of 1 to 30 pairs required')

def test_nested_shapes_values_and_order():
    for pos in (0,1,29):
        for bad in (None,(),(0,), (0,0,0),[0,0],Items((0,0)),'Ж'):
            rows=[(0,0)]*30;rows[pos]=bad
            refuse(tuple(rows),f'cases[{pos}]: pair (expected, observed) required')
        for j,name in enumerate(('expected','observed')):
            for bad in (-1001,1001,True,False,None,Number(1),1.0,'é','ａ','Ж'):
                row=[0,0];row[j]=bad;rows=[(0,0)]*30;rows[pos]=tuple(row)
                refuse(tuple(rows),f'cases[{pos}].{name}: whole number -1000 to 1000 required')
