import itertools
import pytest
from sugarcode.extra_doc.smart_contract588 import simulate


def oracle(events):
    # Declarative transition table; validity of funded exit requires exact amount.
    table={('empty','deposit','buyer'):('funded',None),
           ('funded','release','arbiter'):('released','seller'),
           ('funded','refund','arbiter'):('refunded','buyer')}
    state='empty'; balance=0;recipient=None;ok=[];bad=[]
    for i,(op,actor,amount) in enumerate(events):
        transition=table.get((state,op,actor))
        if transition is None or (state=='funded' and amount != balance):
            bad.append(i);continue
        state,recipient=transition;balance=amount if state=='funded' else 0;ok.append(i)
    return state,balance,recipient,ok,bad


def test_exhaustive_transition_oracle():
    vocabulary=list(itertools.product(('deposit','release','refund'),('buyer','seller','arbiter'),(1,2)))
    for events in itertools.product(vocabulary,repeat=3):
        rows=list(events);got=simulate(rows)
        assert tuple(got[k] for k in ('state','balance','recipient','accepted','rejected')) == oracle(rows)
        assert got['money_moved'] is False and got['claim']=='PARTIAL'


def test_bounds_order_terminal_no_mutation():
    rows=[('deposit','buyer',1000000),('refund','arbiter',1000000),('deposit','buyer',1)]
    before=list(rows);got=simulate(rows)
    assert got['state']=='refunded' and got['accepted']==[0,1] and got['rejected']==[2]
    assert rows==before
    assert simulate([])['state']=='empty'
    assert len(simulate([('release','seller',1)]*100)['rejected'])==100

class L(list):pass
class T(tuple):pass
class S(str):pass
class I(int):pass

@pytest.mark.parametrize('events,message',[
 (L(),'events must be an exact list with 0..100 entries'),
 ([None],'event must be an operation, actor, amount tuple'),
 ([T(('deposit','buyer',1))],'event must be an operation, actor, amount tuple'),
 *[([(x,'buyer',1)],'operation must be deposit, release or refund') for x in (None,S('deposit'),'\t','\u00a0','\u3000','\u2003','\u0085','\u200b')],
 *[([('deposit',x,1)],'actor must be buyer, seller or arbiter') for x in (None,S('buyer'),'\t','\u00a0','\u3000','\u2003','\u0085','\u200b')],
 *[([('deposit','buyer',x)],'amount must be an integer in 1..1000000') for x in (True,I(1),0,1000001)],
 ([('deposit','buyer',1)]*101,'events must be an exact list with 0..100 entries'),
])
def test_reject_and_messages(events,message):
    with pytest.raises(ValueError) as exc:simulate(events)
    assert str(exc.value)==message
