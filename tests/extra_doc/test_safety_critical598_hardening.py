import pytest
from sugarcode.extra_doc.safety_critical598 import review_interlocks as run

T, V = TypeError, ValueError
ROW = ('a', 0, 1, 0)
SLOTS = [(0, 1), (0, 1), (0, 1)]        # (low, high) for each integer slot after the label
DUP = 'duplicate operation'
LABEL_MSG = 'label must be 1..24 lowercase identifier characters'


class StrSub(str):
    pass


class IntSub(int):
    pass


class ListSub(list):
    pass


class TupleSub(tuple):
    pass


def err(exc, msg, rows):
    with pytest.raises(exc) as e:
        run(rows)
    assert str(e.value) == msg


def with_(slot, value, base=ROW):
    r = list(base)
    r[slot] = value
    return tuple(r)


def test_subclass_witnesses_at_every_slot_and_container():
    err(T, 'exact list required', ListSub([ROW]))
    err(T, 'exact list required', (ROW,))
    err(T, 'exact tuple row required', [TupleSub(ROW)])
    err(T, 'exact tuple row required', [ROW, TupleSub(with_(0, 'zz'))])
    err(T, 'exact string label required', [with_(0, StrSub('ok'))])
    for k in range(len(SLOTS)):
        err(T, 'exact nonbool integer required', [with_(k + 1, IntSub(SLOTS[k][0]))])
        err(T, 'exact nonbool integer required', [with_(k + 1, IntSub(SLOTS[k][1]))])
        err(T, 'exact nonbool integer required', [with_(k + 1, True)])
        err(T, 'exact nonbool integer required', [with_(k + 1, False)])
    # plain types are accepted and the input is untouched
    rows = [ROW]
    assert run(rows)
    assert rows == [ROW]


def test_refusal_before_cap_and_check_order():
    err(T, 'exact list required', ListSub([ROW] * 40))                # refused by type, not by count
    err(V, 'row count must be 1..32', [])
    err(V, 'row count must be 1..32', [None] * 33)                     # count before any row is looked at
    err(T, 'exact tuple row required', [None] * 32)                    # the cap is inclusive
    # row shape (type then arity) is checked for every row before any slot is read
    bad_slot = with_(1, 10 ** 9)
    err(T, 'exact tuple row required', [bad_slot, None])
    err(V, 'wrong row arity', [bad_slot, ROW + (1,)])
    err(V, 'wrong row arity', [ROW + (1,), None])                    # rows are checked in order: the first bad row decides
    err(T, 'exact tuple row required', [None, ROW + (1,)])
    err(V, 'wrong row arity', [ROW[:-1], ROW])
    # slots are read row by row, label first, then the integers in order
    err(V, LABEL_MSG, [with_(0, 'Bad'), with_(1, 'x')])
    err(T, 'exact string label required', [with_(0, 5), with_(0, 'Bad')])
    err(V, 'integer outside declared range', [with_(1, 10 ** 9), with_(0, 5)])
    err(T, 'exact nonbool integer required', [with_(1, 'x'), with_(1, 10 ** 9)])
    for k in range(len(SLOTS) - 1):
        lo, hi = SLOTS[k]
        err(V, 'integer outside declared range', [with_(k + 1, hi + 1, with_(k + 2, 'x'))])
        err(T, 'exact nonbool integer required', [with_(k + 1, 'x', with_(k + 2, hi + 10 ** 9))])
    err(V, LABEL_MSG, [with_(0, 'Bad', with_(1, 'x'))])
    # the duplicate check happens after every slot is validated
    err(V, 'integer outside declared range', [ROW, ROW, with_(0, 'other', with_(1, 10 ** 9))])
    err(V, DUP, [ROW, ROW])
    err(V, DUP, [ROW, with_(0, 'other'), ROW])


def test_label_edges_and_no_hidden_character_forms():
    for label in ('a', 'a' * 24, 'a1', 'z_9', 'a_'):
        run([with_(0, label)])
    for label in ('', 'a' * 25, 'A', '1a', '_a', 'a-b', 'a b', 'a\n', '\na', 'a\x00', 'é', 'a\u0661'):
        err(V, LABEL_MSG, [with_(0, label)])
    for k, (lo, hi) in enumerate(SLOTS):
        for v in (lo, hi):
            run([with_(k + 1, v)])
        for v in (lo - 1, hi + 1, -10 ** 30, 10 ** 30):
            err(V, 'integer outside declared range', [with_(k + 1, v)])


def test_truth_table_vs_independent_enumeration():
    import itertools
    for f, g, s in itertools.product((0, 1), repeat=3):
        want = {(0, 1, 0): True}.get((f, g, s), False)
        assert run([('op', f, g, s)]) == {'eligibility': [('op', want)]}
    assert [r for r in itertools.product((0, 1), repeat=3) if run([('op',) + r])['eligibility'][0][1]] == [(0, 1, 0)]
    rows = [('zz', 0, 1, 0), ('aa', 1, 1, 0), ('mm', 0, 0, 0), ('bb', 0, 1, 1)]
    got = run(rows)
    assert got == {'eligibility': [('aa', False), ('bb', False), ('mm', False), ('zz', True)]}
    assert all(type(x[1]) is bool for x in got['eligibility'])
    assert rows[0] == ('zz', 0, 1, 0)
