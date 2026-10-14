import random
import pytest
from sugarcode.extra_doc.local_seo import check_locations as cl

T, V = TypeError, ValueError


class StrSub(str):
    pass


class ListSub(list):
    pass


class TupleSub(tuple):
    pass


def oracle(pages):
    # written from the stated rule: folded city = words lowercased joined with '_'
    probs = [(i, 'same_slug') for i in range(len(pages)) if pages[i][0] in [p[0] for p in pages[:i]]]
    probs += [(i, 'shared_phone') for i in range(len(pages)) if pages[i][2] in [p[2] for p in pages[:i]]]
    folds = ['_'.join(p[1].lower().split()) for p in pages]
    probs += [(i, 'slug_mismatch') for i, p in enumerate(pages) if folds[i] not in p[0]]
    first_phone = {}
    for i, p in enumerate(pages):
        f = folds[i]
        if f in first_phone and first_phone[f] != p[2]:
            probs.append((i, 'phone_split'))
        elif f not in first_phone:
            first_phone[f] = p[2]
    return {'problems': sorted(probs), 'cities': sorted(set(folds)), 'total': len(pages)}


DISCLAIMER = ('NOT_CLAIMED: this checks supplied records against one naming style. It does not say the pages rank '
              'locally, that the phones are real, or that matching slugs help. No clinical or wet-lab claim.')


def test_disclaimer_pinned():
    import sugarcode.extra_doc.local_seo as mod
    assert ' '.join(mod.__doc__.split()).split('NOT_CLAIMED: ', 1)[1] == DISCLAIMER.removeprefix('NOT_CLAIMED: ')


def test_hand_cases():
    good = [('portland_main', 'Portland', '5551234567'), ('salem_eats', 'Salem', '5559876543')]
    assert cl(good) == {'problems': [], 'cities': ['portland', 'salem'], 'total': 2}
    assert cl([]) == {'problems': [], 'cities': [], 'total': 0}
    assert cl([('portland_a', 'Portland', '1111111111'), ('portland_a', 'Portland', '2222222222')])['problems'] == [
        (1, 'phone_split'), (1, 'same_slug')]
    assert cl([('portland_a', 'Portland', '1111111111'), ('salem', 'Salem', '1111111111')])['problems'] == [
        (1, 'shared_phone')]
    assert cl([('bend', 'Portland', '1111111111')])['problems'] == [(0, 'slug_mismatch')]
    assert cl([('new_york_pizza', 'New York', '1111111111')])['problems'] == []
    assert cl([('portland_a', 'Portland', '1111111111'), ('portland_b', 'Portland', '2222222222')])['problems'] == [
        (1, 'phone_split')]
    assert cl([('portland_a', 'Portland', '1111111111'), ('portland_b', 'portland', '1111111111')])['problems'] == [
        (1, 'shared_phone')]                                       # same phone, same city: no split
    r = cl([('x_town_a', 'X Town', '1111111111'), ('x_town_b', 'x town', '2222222222'), ('x_town_c', 'X  Town', '1111111111')])
    assert r['problems'] == [(1, 'phone_split'), (2, 'shared_phone')]
    assert r['cities'] == ['x_town']
    assert cl([('cafe_spot', 'Café', '1111111111')])['problems'] == [(0, 'slug_mismatch')]   # folded city keeps é


@pytest.mark.parametrize('part', range(8))
def test_random_vs_oracle(part):
    rnd = random.Random(4130 + part)
    seen, clean = set(), 0
    cities = [('Portland', 'portland'), ('Salem', 'salem'), ('New York', 'new_york'), ('X Town', 'x_town')]
    for _ in range(60):
        pages = []
        for _ in range(rnd.randint(0, 7)):
            city, key = rnd.choice(cities)
            slug = key + '_' + rnd.choice(('a', 'b', 'zz')) if rnd.random() < 0.8 else rnd.choice(('other', 'misc'))
            phone = rnd.choice(('1111111111', '2222222222', '3333333333'))
            pages.append((slug, city if rnd.random() < 0.8 else city.upper(), phone))
        r = cl(pages)
        assert r == oracle(pages)
        seen.update(c for _, c in r['problems'])
        clean += not r['problems']
    assert len(seen) == 4 and clean >= 2


def test_limits_accepted():
    pages = [('city%02d' % k, 'City%02d' % k, '%010d' % k) for k in range(30)]
    r = cl(pages)
    assert r['problems'] == [] and r['total'] == 30 and len(r['cities']) == 30
    cl([('a' * 24, 'x' * 40, '0' * 10)])


def err(exc, msg, pages):
    with pytest.raises(exc) as e:
        cl(pages)
    assert str(e.value) == msg


SM = 'slug must be 1 to 24 lowercase identifier characters'
CL = 'city length must be 1 to 40 characters'
PH = 'phone must be exactly 10 digits'
NS = (None, 5, b'a', StrSub('a'))
BAD = ('', 'A', '1a', 'a-b', 'a' * 25, 'a\n', 'é', '_a', 'aé', 'ａ')
BPH = ('', '123456789', '12345678901', '123456789a', '１２３４５６７８９０', '555-123-4567', ' 123456789')


def _pins(err):
    for bad in (None, (), 'ab', ListSub([]), {}):
        err(T, 'pages must be an exact list', bad)
    err(V, 'page count must be at most 30', [('a', 'X', '0' * 10)] * 31)
    for bad in (None, ['a', 'X', '0' * 10], 'ab', TupleSub(('a', 'X', '0' * 10)), 5):
        err(T, 'each page must be an exact tuple', [bad])
    for bad in ((), ('a', 'X'), ('a', 'X', '0' * 10, 1)):
        err(V, 'each page must have 3 items', [bad])
    for bad in NS:
        err(T, 'slug must be an exact string', [(bad, 'X', '0' * 10)])
    for bad in BAD:
        err(V, SM, [(bad, 'X', '0' * 10)])
    for bad in NS:
        err(T, 'city must be an exact string', [('a', bad, '0' * 10)])
    for bad in ('', 'x' * 41):
        err(V, CL, [('a', bad, '0' * 10)])
    for bad in NS:
        err(T, 'phone must be an exact string', [('a', 'X', bad)])
    for bad in BPH:
        err(V, PH, [('a', 'X', bad)])


def _order(err):
    err(T, 'pages must be an exact list', 'x')
    err(V, 'page count must be at most 30', [None] * 31)
    err(T, 'each page must be an exact tuple', [None, ('a',)])
    err(V, 'each page must have 3 items', [('a',), None])
    err(T, 'slug must be an exact string', [(5, 5, 5)])
    err(V, SM, [('A', 5, 5)])
    err(T, 'city must be an exact string', [('a', 5, 5)])
    err(V, CL, [('a', '', 5)])
    err(T, 'phone must be an exact string', [('a', 'X', 5)])
    err(V, PH, [('a', 'X', '1')])
    err(T, 'slug must be an exact string', [('a', 'X', '0' * 10), (5, 5, 5)])
    err(T, 'city must be an exact string', [('a', 'X', '0' * 10), ('a', 5, 5)])


def _collect(fn):
    out = []

    def rec(exc, msg, *a):
        out.append((exc, msg) + a)
    fn(rec)
    return out


@pytest.mark.parametrize('exc,msg,t', _collect(_pins))
def test_pin(exc, msg, t):
    err(exc, msg, t)


@pytest.mark.parametrize('exc,msg,t', _collect(_order))
def test_order(exc, msg, t):
    err(exc, msg, t)
