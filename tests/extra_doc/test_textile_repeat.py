import random
from fractions import Fraction as F
import pytest
from sugarcode.extra_doc.textile_repeat import build_repeat as br


def oracle(tw, th, motifs, drop, fw, fl):
    rows, over, cov = [], 0, 0
    for r in range(th):
        s = ''
        for c in range(tw):
            hit = [m for m in motifs
                   if (r - m[1]) % th < m[3] and (c - m[0]) % tw < m[2]]
            if not hit:
                s += '.'
            elif len(hit) == 1:
                s += hit[0][4]
                cov += 1
            else:
                s += '*'
                over += 1
                cov += 1
        rows.append(s)
    # swatch: second tile is the first shifted down by drop rows
    sw = []
    for r in range(th):
        sw.append(rows[r] + rows[(r + th - drop) % th])
    ceil = lambda a, b: (a + b - 1) // b
    return rows, over, cov, sw, dict(across=fw // tw, down=fl // th, leftover_width=fw - (fw // tw) * tw,
                                     leftover_length=fl - (fl // th) * th, repeats_to_cover=ceil(fw, tw) * ceil(fl, th))


def test_random_vs_oracle():
    rnd = random.Random(3)
    for _ in range(400):
        tw, th = rnd.randint(1, 9), rnd.randint(1, 9)
        motifs = [(rnd.randrange(tw), rnd.randrange(th), rnd.randint(1, tw), rnd.randint(1, th), rnd.choice('abcXY'))
                  for _ in range(rnd.randint(1, 4))]
        drop, fw, fl = rnd.randrange(th), rnd.randint(1, 60), rnd.randint(1, 60)
        r = br(tw, th, motifs, drop, fw, fl)
        rows, over, cov, sw, fab = oracle(tw, th, motifs, drop, fw, fl)
        assert r['tile'] == rows and r['overlap_cells'] == over and r['covered_cells'] == cov
        assert r['coverage'] == F(cov, tw * th) and r['swatch'] == sw and r['fabric'] == fab


def test_hand_exact():
    # 4x3 tile; motif at (3,2) size 2x2 covers (3,2),(0,2),(3,0),(0,0)
    r = br(4, 3, [(3, 2, 2, 2, 'a')], 1, 9, 7)
    assert r['tile'] == ['a..a', '....', 'a..a']
    assert r['covered_cells'] == 4 and r['overlap_cells'] == 0 and r['coverage'] == F(1, 3)
    # drop 1: second tile row r is first tile row r-1 mod 3
    assert r['swatch'] == ['a..a' + 'a..a', '....' + 'a..a', 'a..a' + '....']
    assert r['fabric'] == {'across': 2, 'down': 2, 'leftover_width': 1, 'leftover_length': 1, 'repeats_to_cover': 9}


def test_overlap_marker():
    r = br(3, 1, [(0, 0, 2, 1, 'a'), (1, 0, 2, 1, 'b')], 0, 3, 1)
    assert r['tile'] == ['a*b'] and r['overlap_cells'] == 1 and r['covered_cells'] == 3 and r['coverage'] == 1
    assert br(2, 2, [(0, 0, 2, 2, 'a')], 0, 2, 2)['coverage'] == 1
    assert br(2, 2, [(0, 0, 1, 1, 'a')], 0, 2, 2)['coverage'] == F(1, 4)


def test_drop_edges():
    m = [(0, 0, 1, 1, 'a')]
    assert br(2, 3, m, 0, 2, 3)['swatch'] == ['a.a.', '....', '....']
    assert br(2, 3, m, 2, 2, 3)['swatch'] == ['a...', '....', '..a.']


def test_caps_accept():
    br(32, 32, [(31, 31, 32, 32, 'a')] * 16, 31, 1000, 1000)
    br(1, 1, [(0, 0, 1, 1, '!')], 0, 1, 1)
    br(1, 1, [(0, 0, 1, 1, '~')], 0, 1, 1)
    br((4), 4, ((0, 0, 1, 1, 'a'),), 0, 1, 1)


def err(exc, msg, *a):
    with pytest.raises(exc) as e:
        br(*a)
    assert str(e.value) == msg


M = [(0, 0, 1, 1, 'a')]
T, V = TypeError, ValueError


def test_pins():
    for bad in (True, 1.0, '1', None):
        err(T, 'tile_w must be a nonbool int', bad, 2, M, 0, 1, 1)
        err(T, 'tile_h must be a nonbool int', 2, bad, M, 0, 1, 1)
        err(T, 'drop must be a nonbool int', 2, 2, M, bad, 1, 1)
        err(T, 'fabric_w must be a nonbool int', 2, 2, M, 0, bad, 1)
        err(T, 'fabric_l must be a nonbool int', 2, 2, M, 0, 1, bad)
        for i, nm in enumerate('xywh'):
            m = [0, 0, 1, 1, 'a']
            m[i] = bad
            err(T, 'motif %s must be a nonbool int' % nm, 2, 2, [tuple(m)], 0, 1, 1)
    msg = 'tile size must be between 1 and 32 cells each way'
    for a in ((0, 2), (33, 2), (2, 0), (2, 33)):
        err(V, msg, *a, M, 0, 1, 1)
    err(T, 'motifs must be a list or tuple', 2, 2, 'a', 0, 1, 1)
    err(V, 'motif count must be between 1 and 16', 2, 2, [], 0, 1, 1)
    err(V, 'motif count must be between 1 and 16', 2, 2, M * 17, 0, 1, 1)
    err(T, 'each motif must be (x, y, w, h, ch)', 2, 2, [3], 0, 1, 1)
    err(T, 'each motif must be (x, y, w, h, ch)', 2, 2, [(0, 0, 1, 1)], 0, 1, 1)
    err(T, 'each motif must be (x, y, w, h, ch)', 2, 2, [(0, 0, 1, 1, 'a', 'b')], 0, 1, 1)
    err(T, 'motif ch must be str', 2, 2, [(0, 0, 1, 1, 1)], 0, 1, 1)
    o = 'motif origin must lie inside the tile'
    for m in ((-1, 0, 1, 1, 'a'), (2, 0, 1, 1, 'a'), (0, -1, 1, 1, 'a'), (0, 2, 1, 1, 'a')):
        err(V, o, 2, 2, [m], 0, 1, 1)
    s = 'motif size must be between 1 and the tile size'
    for m in ((0, 0, 0, 1, 'a'), (0, 0, 3, 1, 'a'), (0, 0, 1, 0, 'a'), (0, 0, 1, 3, 'a')):
        err(V, s, 2, 2, [m], 0, 1, 1)
    c = "motif ch must be one printable non-space character other than '.' and '*'"
    for ch in ('', 'ab', ' ', '.', '*', '\x7f', '\u00e9', '\t'):
        err(V, c, 2, 2, [(0, 0, 1, 1, ch)], 0, 1, 1)
    err(V, 'drop must be between 0 and tile_h - 1', 2, 2, M, -1, 1, 1)
    err(V, 'drop must be between 0 and tile_h - 1', 2, 2, M, 2, 1, 1)
    f = 'fabric size must be between 1 and 1000 cells'
    for a in ((0, 1), (1001, 1), (1, 0), (1, 1001)):
        err(V, f, 2, 2, M, 0, *a)


def test_validation_precedes_rendering_and_covers_every_motif():
    for pos in range(3):
        ms = [(0, 0, 1, 1, 'a')] * 3
        ms[pos] = (0, 0, 1, 1, 7)
        err(T, 'motif ch must be str', 2, 2, ms, 0, 1, 1)
    err(V, 'drop must be between 0 and tile_h - 1', 2, 2, [(0, 0, 2, 2, 'a'), (0, 0, 2, 2, 'b')], 5, 1, 1)
