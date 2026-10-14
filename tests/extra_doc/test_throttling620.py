import copy
import itertools
import pytest
from sugarcode.extra_doc.throttling620 import simulate_token_bucket as run

ROWS = [('a', 0, 7), ('b', 0, 4), ('c', 1, 5)]
WANT = {'requests': [('a', 0, True, 3), ('b', 0, False, 3), ('c', 1, True, 0)], 'remaining_tokens': 0, 'accepted_count': 2}


def test_hand_literal_and_no_mutation():
    before = copy.deepcopy(ROWS)
    assert run(ROWS) == WANT
    assert ROWS == before


def test_permutations_preserve_result():
    for order in itertools.permutations(ROWS):
        assert run(list(order)) == WANT


@pytest.mark.parametrize('bad', [None, (), {}, iter([]), 'x', True])
def test_outer_schema_refuses_exactly(bad):
    with pytest.raises(TypeError, match='^exact list required$'):
        run(bad)


@pytest.mark.parametrize('size', [0, 33])
def test_outer_size_refused_before_row_scan(size):
    with pytest.raises(ValueError, match='^row count must be 1..32$'):
        run([None] * size)


@pytest.mark.parametrize('bad', [None, [], {}, 'x', 1, True])
def test_tuple_row_schema_refuses_exactly(bad):
    with pytest.raises(TypeError, match='^exact tuple row required$'):
        run([bad])


@pytest.mark.parametrize('size', [0, 2, 4])
def test_row_arity_precedes_slots(size):
    with pytest.raises(ValueError, match='^wrong row arity$'):
        run([(None,) * size])


@pytest.mark.parametrize('slot', [0])
@pytest.mark.parametrize('bad', [None, 1, True, 1.0, b'a', [], {}])
def test_each_label_slot_exact_type(slot, bad):
    row = list(ROWS[0]); row[slot] = bad
    with pytest.raises(TypeError, match='^exact string label required$'):
        run([tuple(row)])


@pytest.mark.parametrize('slot', [0])
@pytest.mark.parametrize('bad', ['', 'A', 'a b', 'a'*25, 'a\n', 'é'])
def test_each_label_slot_shape_and_cap(slot, bad):
    row = list(ROWS[0]); row[slot] = bad
    with pytest.raises(ValueError, match='^label must be 1..24 lowercase identifier characters$'):
        run([tuple(row)])


@pytest.mark.parametrize('slot,low,high', [(1, 0, 1000000), (2, 1, 10)])
@pytest.mark.parametrize('bad', [None, True, False, 1.0, '1', [], {}])
def test_each_numeric_slot_strict_type(slot, low, high, bad):
    row = list(ROWS[0]); row[slot] = bad
    with pytest.raises(TypeError, match='^exact nonbool integer required$'):
        run([tuple(row)])


@pytest.mark.parametrize('slot,low,high', [(1, 0, 1000000), (2, 1, 10)])
def test_each_numeric_slot_endpoints_and_caps(slot, low, high):
    for value in (low, high):
        row = list(ROWS[0]); row[slot] = value
        assert run([tuple(row)])
    for value in (low-1, high+1, 10**1000):
        row = list(ROWS[0]); row[slot] = value
        with pytest.raises(ValueError, match='^integer outside declared range$'):
            run([tuple(row)])


def test_duplicate_identity_refused():
    with pytest.raises(ValueError, match='^duplicate '):
        run([ROWS[0], ROWS[0]])


def test_label_length_endpoints():
    for label in ('a', 'a'*24):
        row = list(ROWS[0]); row[0] = label
        assert run([tuple(row)])


def test_row_cap_accepted():
    rows = []
    for i in range(32):
        row = list(ROWS[0]); row[0] = 'person_'+str(i); rows.append(tuple(row))
    assert run(rows)


def test_refill_cap_and_rejected_request_no_charge():
    assert run([('a',0,10),('b',1,3),('c',1,2),('d',2,2),('e',100,10)])=={'requests':[('a',0,True,0),('b',1,False,2),('c',1,True,0),('d',2,True,0),('e',100,True,0)],'remaining_tokens':0,'accepted_count':4}
    assert run([('z',0,10),('a',0,1)])=={'requests':[('a',0,True,9),('z',0,False,9)],'remaining_tokens':9,'accepted_count':1}


def test_discrete_tick_oracle():
    rows=[('r_'+str(i),i//2,(i*3)%10+1) for i in range(20)]
    tokens=10;accepted={};ordered=sorted(rows,key=lambda x:(x[1],x[0]))
    for tick in range(ordered[-1][1]+1):
        if tick>0:tokens=min(10,tokens+2)
        for name,time,cost in ordered:
            if time==tick:
                if cost>tokens:accepted[name]=(False,tokens)
                else:tokens-=cost;accepted[name]=(True,tokens)
    assert run(rows)['requests']==[(n,t,*accepted[n]) for n,t,_ in ordered]
