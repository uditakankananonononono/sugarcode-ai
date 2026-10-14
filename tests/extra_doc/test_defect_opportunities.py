import itertools
import re
from fractions import Fraction
import pytest
from sugarcode.extra_doc.defect_opportunities import defects
class Number(int): pass
class Items(tuple): pass

def oracle(batches,limit):
    total=0; opportunities=0
    for d,n in batches: total+=d;opportunities+=n
    rate=Fraction(total,opportunities)*1000000
    return {'defect_opportunities_validated':False,
            'not_claimed':('sigma_level','process_capability','defect_reduction'),
            'defects':total,'opportunities':opportunities,
            'ppm':int(rate),'within_limit':rate<=limit}

def refuse(batches,limit,message):
    with pytest.raises(ValueError) as exc: defects(batches,limit)
    assert re.fullmatch(re.escape(message),str(exc.value))

def test_fraction_oracle():
    choices=((0,1),(1,1),(0,3),(1,3),(2,3),(3,3))
    for n in (1,2,3):
        for batches in itertools.product(choices,repeat=n):
            for limit in (0,1,333333,333334,500000,999999,1000000):
                assert defects(batches,limit)==oracle(batches,limit)

def test_caps_exact_threshold():
    for batches in (((0,10000),)*20,((10000,10000),)*20,((1,2),),((0,1),(1,1))):
        for limit in (0,1,500000,1000000): assert defects(batches,limit)==oracle(batches,limit)

def test_container():
    for bad in ((),(None,)*21,[(0,1)],Items(((0,1),)),None,'é'):
        refuse(bad,None,'batches: tuple of 1 to 20 pairs required')

def test_rows_types_shape_and_values():
    for pos in (0,1,19):
        for bad in (None,(),(0,), (0,1,2),[0,1],Items((0,1)),'Ж'):
            rows=[(0,1)]*20;rows[pos]=bad
            refuse(tuple(rows),None,f'batches[{pos}]: pair (defects, opportunities) required')
        for bad in (0,-1,10001,True,False,None,Number(1),1.0,'é','ａ','Ж'):
            rows=[(0,1)]*20;rows[pos]=(None,bad)
            refuse(tuple(rows),None,f'batches[{pos}].opportunities: whole number 1 to 10000 required')
        for bad in (-1,2,True,False,None,Number(1),1.0,'é','ａ','Ж'):
            rows=[(0,1)]*20;rows[pos]=(bad,1)
            refuse(tuple(rows),None,f'batches[{pos}].defects: whole number 0 to opportunities required')

def test_limit():
    for bad in (-1,1000001,True,False,None,Number(1),1.0,'é','ａ','Ж'):
        refuse(((0,1),),bad,'ppm_limit: whole number 0 to 1000000 required')
