import itertools
import re
import pytest
from sugarcode.extra_doc.cash_runway import runway
class Number(int): pass
class Items(tuple): pass

def oracle(periods,cash):
    closing=[];first=None
    for i in range(len(periods)):
        revenues=sum(row[0] for row in periods[:i+1])
        expenses=sum(row[1] for row in periods[:i+1])
        balance=cash+revenues-expenses
        closing.append(balance)
        if first is None and balance<0: first=i
    return {'cash_runway_validated':False,
            'not_claimed':('financial_prediction','business_model','accounting_validation'),
            'closing_balances':tuple(closing),'final_cash':closing[-1],
            'first_negative':first,'nonnegative_throughout':first is None}

def refuse(args,message):
    with pytest.raises(ValueError) as exc: runway(*args)
    assert re.fullmatch(re.escape(message),str(exc.value))

def test_oracle():
    pairs=tuple(itertools.product((0,1,3),repeat=2))
    for n in (1,2,3):
        for periods in itertools.product(pairs,repeat=n):
            for cash in (0,1,2,1000000): assert runway(periods,cash)==oracle(periods,cash)

def test_caps_negative_boundaries():
    for periods in (((0,1000000),)*24,((1000000,0),)*24,((0,0),)*24,((0,1),)+((1,0),)*23,((0,0),)*23+((0,1),)):
        for cash in (0,1,1000000): assert runway(periods,cash)==oracle(periods,cash)

def test_shape_and_cash_order():
    for bad in ((),(None,)*25,[(0,0)],Items(((0,0),)),None,'é'):
        refuse((bad,None),'periods: tuple of 1 to 24 pairs required')
    for bad in (-1,1000001,True,False,None,Number(1),1.0,'é','ａ','Ж'):
        refuse(((None,),bad),'starting_cash: whole number 0 to 1000000 required')

def test_nested_shapes_and_values():
    for pos in (0,1,23):
        for bad in (None,(),(0,), (0,0,0),[0,0],Items((0,0)),'Ж'):
            rows=[(0,0)]*24;rows[pos]=bad
            refuse((tuple(rows),0),f'periods[{pos}]: pair (revenue, expense) required')
        for j,name in enumerate(('revenue','expense')):
            for bad in (-1,1000001,True,False,None,Number(1),1.0,'é','ａ','Ж'):
                row=[0,0];row[j]=bad
                rows=[(0,0)]*24;rows[pos]=tuple(row)
                refuse((tuple(rows),0),f'periods[{pos}].{name}: whole number 0 to 1000000 required')
