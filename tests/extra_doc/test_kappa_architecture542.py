import copy
import itertools
import pytest
from sugarcode.extra_doc.kappa_architecture542 import replay_stream as run

ROWS = [('a', 'x', 2, 7), ('b', 'y', 1, -3), ('c', 'x', 3, 2)]
WANT = {'state': [('x', 9), ('y', -3)], 'trace': [('b', 'y', 1, 0, -3), ('a', 'x', 2, 0, 7), ('c', 'x', 3, 7, 9)], 'events': 3}


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


@pytest.mark.parametrize('size', [0, 3, 5])
def test_row_arity_precedes_slots(size):
    with pytest.raises(ValueError, match='^wrong row arity$'):
        run([(None,) * size])


@pytest.mark.parametrize('slot', [0, 1])
@pytest.mark.parametrize('bad', [None, 1, True, 1.0, b'a', [], {}])
def test_each_label_slot_exact_type(slot, bad):
    row = list(ROWS[0]); row[slot] = bad
    with pytest.raises(TypeError, match='^exact string label required$'):
        run([tuple(row)])


@pytest.mark.parametrize('slot', [0, 1])
@pytest.mark.parametrize('bad', ['', 'A', 'a b', 'a'*25, 'a\n', 'é'])
def test_each_label_slot_shape_and_cap(slot, bad):
    row = list(ROWS[0]); row[slot] = bad
    with pytest.raises(ValueError, match='^label must be 1..24 lowercase identifier characters$'):
        run([tuple(row)])


@pytest.mark.parametrize('slot,low,high', [(2, 0, 1000000), (3, -1000000, 1000000)])
@pytest.mark.parametrize('bad', [None, True, False, 1.0, '1', [], {}])
def test_each_numeric_slot_strict_type(slot, low, high, bad):
    row = list(ROWS[0]); row[slot] = bad
    with pytest.raises(TypeError, match='^exact nonbool integer required$'):
        run([tuple(row)])


@pytest.mark.parametrize('slot,low,high', [(2, 0, 1000000), (3, -1000000, 1000000)])
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
        row = list(ROWS[0]); row[0] = 'person_'+str(i); row[2] = i; rows.append(tuple(row))
    assert run(rows)


def test_independent_replay_order_each_slot_and_duplicate_keys():
    rows=[('e_'+str(i),'key_'+str(i%3),i,(-1)**i*i) for i in range(32)]
    result=run(rows);expected={}
    for event,key,seq,delta in rows:expected[key]=sum(row[3] for row in rows if row[1]==key)
    assert result['state']==sorted(expected.items())
    for event,key,seq,before,after in result['trace']:
        assert before==sum(row[3] for row in rows if row[1]==key and row[2]<seq)
        assert after==sum(row[3] for row in rows if row[1]==key and row[2]<=seq)
    with pytest.raises(ValueError,match='^duplicate event$'):run([('a','x',1,1),('a','y',2,2)])
    with pytest.raises(ValueError,match='^duplicate key sequence$'):run([('a','x',1,1),('b','x',1,2)])
    assert run([('b','y',1,2),('a','x',1,1)])['trace'][0][0]=='a'


def test_equal_sequence_tie_is_event_not_key_or_delta():
    rows=[('a','z',5,9),('b','a',5,-3)]
    for order in (rows,list(reversed(rows))):
        assert run(order)['trace']==[('a','z',5,0,9),('b','a',5,0,-3)]
