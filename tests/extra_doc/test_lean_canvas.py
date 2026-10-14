"""Row 365 tests: oracle, caps at N and N+1, exact messages, exact-type pins, check order."""
import pytest

from sugarcode.extra_doc.lean_canvas import BLOCKS, check_canvas as cc


class L(list):
    pass


class S(str):
    pass


def refuses(error, msg, a):
    with pytest.raises(error) as e:
        cc(a)
    assert type(e.value) is error and str(e.value) == msg


TY = 'blocks must be a list or tuple'
NINE = 'exactly nine blocks required'
ROW = 'blocks must be lists or tuples of at most five entries'
ENT = 'entries must be strings of length 1 through 64'


def mk(**kw):
    b = [[] for _ in range(9)]
    for k, v in kw.items():
        b[BLOCKS.index(k)] = v
    return b


def test_names():
    assert BLOCKS == ('problem', 'customer_segments', 'unique_value_proposition', 'solution', 'channels',
                      'revenue_streams', 'cost_structure', 'key_metrics', 'unfair_advantage')


def test_literals_and_oracle():
    assert cc(mk()) == {'counts': [0] * 9, 'empty_blocks': list(BLOCKS), 'filled_count': 0,
                        'all_filled': False, 'idea_validated': False}
    r = cc(mk(problem=['a'], solution=['b', 'c'], unfair_advantage=['d'] * 5))
    assert r['counts'] == [1, 0, 0, 2, 0, 0, 0, 0, 5] and r['filled_count'] == 3
    assert r['empty_blocks'] == [b for b in BLOCKS if b not in ('problem', 'solution', 'unfair_advantage')]
    assert r['all_filled'] is False
    full = cc([['x']] * 9)
    assert full['all_filled'] is True and full['filled_count'] == 9 and full['empty_blocks'] == []
    assert cc([['x']] * 8 + [[]])['empty_blocks'] == ['unfair_advantage']
    assert cc(tuple(('x',) for _ in range(9)))['all_filled'] is True
    for i in range(9):
        b = [['x']] * 9
        b[i] = []
        assert cc(b)['empty_blocks'] == [BLOCKS[i]] and cc(b)['all_filled'] is False


def test_caps_n_and_n_plus_1():
    assert cc(mk(problem=['a'] * 5))['counts'][0] == 5
    refuses(ValueError, ROW, mk(problem=['a'] * 6))
    refuses(ValueError, ROW, mk(unfair_advantage=['a'] * 6))
    assert cc(mk(problem=['a' * 64]))['filled_count'] == 1
    refuses(ValueError, ENT, mk(problem=['a' * 65]))
    refuses(ValueError, ENT, mk(problem=['a', '']))
    refuses(ValueError, ENT, mk(unfair_advantage=['']))
    refuses(ValueError, NINE, [[]] * 8)
    refuses(ValueError, NINE, [[]] * 10)


def test_exact_types():
    refuses(TypeError, TY, L([[]] * 9))
    for b in (None, 'abc', {1}, {1: 1}, 5):
        refuses(TypeError, TY, b)
    refuses(ValueError, ROW, [L()] + [[]] * 8)
    refuses(ValueError, ROW, [[]] * 8 + ['ab'])
    refuses(ValueError, ROW, [[]] * 8 + [None])
    for b in (S('a'), 1, None, b'a', ['a'], True):
        refuses(ValueError, ENT, mk(problem=[b]))
        refuses(ValueError, ENT, mk(problem=['a', b]))
        refuses(ValueError, ENT, mk(unfair_advantage=[b]))
    src = [['a']] * 9
    r = cc(src)
    r['counts'].append(1)
    assert src == [['a']] * 9


def test_check_order():
    refuses(TypeError, TY, 1)
    refuses(ValueError, NINE, [5])
    refuses(ValueError, ROW, [['a'] * 6, 5, 5, 5, 5, 5, 5, 5, 5])
    refuses(ValueError, ENT, [[1]] + [[]] * 8)
