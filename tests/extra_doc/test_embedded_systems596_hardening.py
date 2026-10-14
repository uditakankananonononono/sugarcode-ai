import pytest
from sugarcode.extra_doc.embedded_systems596 import simulate_register_writes as run

T, V = TypeError, ValueError
ROW = ('a', 170, 15, 5)
SLOTS = [(0, 255), (0, 255), (0, 255)]        # (low, high) for each integer slot after the label
DUP = 'duplicate step'
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


def oracle(prior, mask, value):
    bits = []
    for b in range(8):
        bits.append((value >> b) & 1 if (mask >> b) & 1 else (prior >> b) & 1)
    return sum(bit << b for b, bit in enumerate(bits))


def test_values_vs_bitwise_oracle_and_sorting():
    import random
    rnd = random.Random(596)
    for _ in range(300):
        rows = [('s%d' % i, rnd.randint(0, 255), rnd.choice([0, 255, rnd.randint(0, 255)]), rnd.randint(0, 255))
                for i in range(rnd.randint(1, 8))]
        rnd.shuffle(rows)
        got = run(rows)
        assert got == {'writes': [(s, oracle(p, m, v)) for s, p, m, v in sorted(rows)]}
        assert [w[0] for w in got['writes']] == sorted(r[0] for r in rows)
    assert run([('b', 0, 255, 255), ('a', 255, 0, 0)]) == {'writes': [('a', 255), ('b', 255)]}
    # label order is plain string order: 'a_' sorts before 'a1', 'a10' before 'a2'
    assert [w[0] for w in run([('a2', 0, 0, 0), ('a10', 0, 0, 0), ('a_', 0, 0, 0), ('a1', 0, 0, 0)])['writes']] == ['a1', 'a10', 'a2', 'a_']
    assert type(run([('a', 1, 1, 1)])['writes'][0][1]) is int
