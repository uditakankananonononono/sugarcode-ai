import random
import re
from fractions import Fraction as F
import pytest
from sugarcode.extra_doc.comic_script import check_comic_script as chk

WORDS = ['hero', 'runs', 'fast', 'the', 'door', 'opens', 'wide', 'no', 'wait', 'look']


def phrase(rnd, n):
    return ' '.join(rnd.choice(WORDS) for _ in range(n))


def oracle(pages, mp, mb, md, lo, hi):
    out, viol, text = [], [], []
    for pn, page in enumerate(pages, 1):
        if pn > 1:
            text.append('')
        text.append('PAGE %d (%d %s)' % (pn, len(page), 'PANEL' if len(page) == 1 else 'PANELS'))
        d = s = 0
        if len(page) > mp:
            viol.append('page %d: more than %d panels' % (pn, mp))
        for qn, (desc, bal) in enumerate(page, 1):
            text += ['', 'PANEL %d' % qn, ' '.join(desc.split())]
            s += len(re.findall(r'\S+', desc))
            pw = 0
            for bn, (sp, ln) in enumerate(bal, 1):
                text.append(' '.join(sp.split()).upper() + ': ' + ' '.join(ln.split()))
                n = len(re.findall(r'\S+', ln))
                pw += n
                if n > mb:
                    viol.append('page %d panel %d balloon %d: more than %d words' % (pn, qn, bn, mb))
            if pw > md:
                viol.append('page %d panel %d: dialogue over %d words' % (pn, qn, md))
            d += pw
        sh = F(d, d + s)
        if sh < lo:
            viol.append('page %d: dialogue share below minimum' % pn)
        if sh > hi:
            viol.append('page %d: dialogue share above maximum' % pn)
        out.append((len(page), d, s, sh))
    return '\n'.join(text), out, viol


def test_random_vs_oracle():
    rnd = random.Random(11)
    for _ in range(300):
        pages = []
        for _ in range(rnd.randint(1, 4)):
            pg = []
            for _ in range(rnd.randint(1, 6)):
                bal = [(rnd.choice(['ann', 'Bo', 'cy d']), phrase(rnd, rnd.randint(1, 9))) for _ in range(rnd.randint(0, 3))]
                pg.append((phrase(rnd, rnd.randint(1, 12)) + '  ', bal))
            pages.append(pg)
        mp, mb, md = rnd.randint(1, 7), rnd.randint(1, 9), rnd.randint(1, 20)
        lo = F(rnd.randint(0, 5), 10)
        hi = lo + F(rnd.randint(0, 5), 10)
        r = chk(pages, mp, mb, md, lo, hi)
        t, st, v = oracle(pages, mp, mb, md, lo, hi)
        assert r['text'] == t
        assert r['violations'] == v
        assert r['balanced'] == (not v)
        assert [(p['panels'], p['dialogue_words'], p['description_words'], p['dialogue_share']) for p in r['pages']] == st


def test_hand_layout():
    r = chk([[('A man waits.', [('joe', 'Hello there')])]], 1, 5, 5, 0, 1)
    assert r['text'] == 'PAGE 1 (1 PANEL)\n\nPANEL 1\nA man waits.\nJOE: Hello there'
    assert r['pages'][0]['dialogue_share'] == F(2, 5) and r['balanced'] is True
    r = chk([[('x', []), ('y', [])], [('z', [])]], 2, 1, 1, 0, 1)
    assert r['text'] == 'PAGE 1 (2 PANELS)\n\nPANEL 1\nx\n\nPANEL 2\ny\n\nPAGE 2 (1 PANEL)\n\nPANEL 1\nz'


def test_limit_edges_exact():
    pg = [[('a b', [('s', 'w1 w2 w3')])]]
    assert chk(pg, 1, 3, 3, 0, 1)['violations'] == []
    assert chk(pg, 1, 2, 3, 0, 1)['violations'] == ['page 1 panel 1 balloon 1: more than 2 words']
    assert chk(pg, 1, 3, 2, 0, 1)['violations'] == ['page 1 panel 1: dialogue over 2 words']
    two = [[('a', []), ('b', [])]]
    assert chk(two, 2, 1, 1, 0, 1)['violations'] == []
    assert chk(two, 1, 1, 1, 0, 1)['violations'] == ['page 1: more than 1 panels']
    # share exactly at the bounds is allowed, one step outside is not
    pg = [[('a b', [('s', 'w1 w2 w3')])]]  # 3/5
    assert chk(pg, 1, 9, 9, F(3, 5), F(3, 5))['violations'] == []
    assert chk(pg, 1, 9, 9, F(3, 5) + F(1, 1000), 1)['violations'] == ['page 1: dialogue share below minimum']
    assert chk(pg, 1, 9, 9, 0, F(3, 5) - F(1, 1000))['violations'] == ['page 1: dialogue share above maximum']


def err(exc, msg, *a):
    with pytest.raises(exc) as e:
        chk(*a)
    assert str(e.value) == msg


P = [[('d', [('s', 'l')])]]
T, V = TypeError, ValueError


def test_pins_structure():
    err(T, 'pages must be a list or tuple', 'x', 1, 1, 1, 0, 1)
    err(V, 'page count must be between 1 and 24', [], 1, 1, 1, 0, 1)
    err(V, 'page count must be between 1 and 24', [[('d', [])]] * 25, 1, 1, 1, 0, 1)
    chk([[('d', [])]] * 24, 1, 1, 1, 0, 1)
    err(T, 'each page must be a list or tuple of panels', ['x'], 1, 1, 1, 0, 1)
    err(V, 'each page must have 1 to 9 panels', [[]], 1, 1, 1, 0, 1)
    err(V, 'each page must have 1 to 9 panels', [[('d', [])] * 10], 1, 1, 1, 0, 1)
    chk([[('d', [])] * 9], 9, 1, 1, 0, 1)
    err(T, 'each panel must be a (description, dialogue) pair', [['x']], 1, 1, 1, 0, 1)
    err(T, 'each panel must be a (description, dialogue) pair', [[('a', [], 3)]], 1, 1, 1, 0, 1)
    err(T, 'dialogue must be a list or tuple of (speaker, line) pairs', [[('a', 'b')]], 1, 1, 1, 0, 1)
    err(V, 'at most 6 balloons per panel', [[('a', [('s', 'l')] * 7)]], 1, 1, 1, 0, 1)
    chk([[('a', [('s', 'l')] * 6)]], 1, 1, 6, 0, 1)
    err(T, 'dialogue must be a list or tuple of (speaker, line) pairs', [[('a', ['s'])]], 1, 1, 1, 0, 1)
    err(T, 'dialogue must be a list or tuple of (speaker, line) pairs', [[('a', [('s', 'l', 'm')])]], 1, 1, 1, 0, 1)


def test_pins_text():
    err(T, 'description must be str', [[(1, [])]], 1, 1, 1, 0, 1)
    err(T, 'speaker must be str', [[('a', [(1, 'l')])]], 1, 1, 1, 0, 1)
    err(T, 'line must be str', [[('a', [('s', None)])]], 1, 1, 1, 0, 1)
    err(V, 'description must be 1 to 400 characters', [[('   ', [])]], 1, 1, 1, 0, 1)
    err(V, 'description must be 1 to 400 characters', [[('x' * 401, [])]], 1, 1, 1, 0, 1)
    chk([[('x' * 400, [])]], 1, 1, 1, 0, 1)
    err(V, 'speaker must be 1 to 30 characters', [[('a', [('x' * 31, 'l')])]], 1, 1, 1, 0, 1)
    chk([[('a', [('x' * 30, 'l')])]], 1, 1, 1, 0, 1)
    err(V, 'line must be 1 to 400 characters', [[('a', [('s', '')])]], 1, 1, 1, 0, 1)
    err(V, 'description must be printable ASCII', [[('a\tb', [])]], 1, 1, 1, 0, 1)
    err(V, 'line must be printable ASCII', [[('a', [('s', 'caf\u00e9')])]], 1, 1, 1, 0, 1)
    err(V, 'speaker must be printable ASCII', [[('a', [('s\n', 'l')])]], 1, 1, 1, 0, 1)


def test_pins_limits_and_shares():
    for i, name in enumerate(['max_panels_per_page', 'max_balloon_words', 'max_panel_dialogue_words']):
        for bad, exc, msg in [(True, T, name + ' must be a nonbool int'), (1.0, T, name + ' must be a nonbool int'),
                              (0, V, name + ' must be between 1 and 1000'), (1001, V, name + ' must be between 1 and 1000')]:
            a = [1, 1, 1]
            a[i] = bad
            err(exc, msg, P, *a, 0, 1)
        chk(P, *([1000 if j == i else 1 for j in range(3)]), 0, 1)
    for pos in (0, 1):
        for bad in (True, 0.5, '0', None):
            a = [0, 1]
            a[pos] = bad
            err(T, 'shares must be nonbool int or Fraction', P, 1, 1, 1, *a)
        a = [0, 1]
        a[pos] = F(1, 2 ** 32)
        err(V, 'rational values must fit 32 bits', P, 1, 1, 1, *a)
        a[pos] = F(2 ** 32, 3) if pos else F(1, 2 ** 32 - 1)
    chk(P, 1, 1, 1, F(1, 2 ** 32 - 1), F(2 ** 32 - 2, 2 ** 32 - 1))
    err(V, 'shares must be in [0, 1]', P, 1, 1, 1, -1, 1)
    err(V, 'shares must be in [0, 1]', P, 1, 1, 1, 0, 2)
    err(V, 'shares must be in [0, 1]', P, 1, 1, 1, F(-1, 2), F(1, 2))
    err(V, 'min_share must not exceed max_share', P, 1, 1, 1, F(2, 3), F(1, 3))


def test_validation_before_counting_even_if_violating():
    # a script that violates every limit still reports bad types first
    err(T, 'speaker must be str', [[('a b c d', [(7, 'x y z w')])]], 1, 1, 1, 0, 0)
    err(V, 'min_share must not exceed max_share', [[('a b c d', [('s', 'x y z w')])]], 1, 1, 1, 1, 0)


def test_gap_closers():
    # empty-string dialogue is not a list of balloons
    err(T, 'dialogue must be a list or tuple of (speaker, line) pairs', [[('a', '')]], 1, 1, 1, 0, 1)
    err(T, 'dialogue must be a list or tuple of (speaker, line) pairs', [[('a', 'ab')]], 1, 1, 1, 0, 1)
    # numerator alone too wide: denominator 1 so only the numerator check can fire
    err(V, 'rational values must fit 32 bits', P, 1, 1, 1, 2 ** 32, 2 ** 32)
    err(V, 'rational values must fit 32 bits', P, 1, 1, 1, 0, 2 ** 32)
    chk(P, 1, 1, 1, 0, 1)
    # each side of both share bounds
    chk(P, 1, 1, 1, 0, 0)
    chk(P, 1, 1, 1, 1, 1)
    err(V, 'shares must be in [0, 1]', P, 1, 1, 1, 0, -1)
    err(V, 'shares must be in [0, 1]', P, 1, 1, 1, 2, 1)
    err(V, 'shares must be in [0, 1]', P, 1, 1, 1, -1, -1)
    # ASCII class edges
    chk([[('~ !', [('~', '~')])]], 1, 1, 1, 0, 1)
    for bad in ('\x1f', '\x7f'):
        err(V, 'description must be printable ASCII', [[('a' + bad, [])]], 1, 1, 1, 0, 1)
        err(V, 'line must be printable ASCII', [[('a', [('s', 'a' + bad)])]], 1, 1, 1, 0, 1)


def test_whitespace_normalised_in_speakers_and_lines():
    r = chk([[('a   b', [('X   Y', 'hello    there')])]], 1, 5, 5, 0, 1)
    assert r['text'] == 'PAGE 1 (1 PANEL)\n\nPANEL 1\na b\nX Y: hello there'.replace('X Y', 'X Y'.upper())
    assert r['pages'][0]['dialogue_words'] == 2 and r['pages'][0]['description_words'] == 2
    r = chk([[('d', [('  lo  ', '  hi   yo  ')])]], 1, 5, 5, 0, 1)
    assert r['text'].splitlines()[-1] == 'LO: hi yo'
