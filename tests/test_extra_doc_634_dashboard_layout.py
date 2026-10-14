import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import dashboard_layout as mod

SRC = pathlib.Path(mod.__file__).read_text()
ROOT = pathlib.Path(mod.__file__).parent


def _load(src):
    m = types.ModuleType('mutant')
    exec(compile(src, 'mutant', 'exec'), m.__dict__)
    return m


def _load_code(code):
    m = types.ModuleType('mutant')
    exec(code, m.__dict__)
    return m


def _raises(exc, message, fn, *args):
    with pytest.raises(exc) as info:
        fn(*args)
    assert str(info.value) == message


def _survives(battery, old, new):
    doc_end = SRC.index('"""', 3) + 3
    assert SRC.find(old) > doc_end, 'mutation target must be code, not the docstring'
    mutated = SRC.replace(old, new, 1)
    assert mutated != SRC
    code = compile(mutated, 'mutant', 'exec')  # a syntax error is not a kill
    def _timeout(*_):
        raise TimeoutError('mutant did not terminate')
    previous = signal.signal(signal.SIGALRM, _timeout)
    signal.alarm(5)
    try:
        battery(_load_code(code))
    except (Exception, pytest.fail.Exception):
        return False
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, previous)
    return True


class I(int):
    pass


class L(list):
    pass


class T(tuple):
    pass


class S(str):
    pass


class LyingI(int):
    def __ge__(self, o): return True
    def __le__(self, o): return True
    def __gt__(self, o): return True
    def __lt__(self, o): return False
    def __ne__(self, o): return False
    def __eq__(self, o): return True
    __hash__ = int.__hash__


class LyingS(str):
    def __eq__(self, o): return True
    def __ne__(self, o): return False
    def __hash__(self): return hash('web')


def test_scope_and_package_rules():
    assert mod.SCOPE == 'PARTIAL: left-to-right panel placement on a fixed grid, nothing rendered'
    assert len(mod.NOT_CLAIMED) >= 4 and 'rendering' in mod.NOT_CLAIMED and 'NOT_CLAIMED' in mod.__doc__
    assert not (ROOT / '__init__.py').exists()


def _oracle(panels, cols):
    """Independent: walk a cursor cell by cell in row-major order and drop each panel where its span fits."""
    r, c = 0, 0
    placed, grid = [], {}
    for title, w in panels:
        if c + w > cols:
            r, c = r + 1, 0
        for x in range(c, c + w):
            assert (r, x) not in grid
            grid[(r, x)] = title
        placed.append((title, r, c))
        c += w
    nrows = (max(p[1] for p in placed) + 1) if placed else 0
    rows = [[t for t, rr, _ in placed if rr == i] for i in range(nrows)]
    fill = [sum(1 for (rr, _x) in grid if rr == i) for i in range(nrows)]
    return {'rows': rows, 'placements': placed, 'row_count': nrows, 'fill': fill}


def _core(m):
    ps = [('cpu', 4), ('mem', 4), ('disk', 4), ('net', 6), ('err', 6), ('big', 12), ('s', 1)]
    assert m.layout_panels(ps) == {'rows': [['cpu', 'mem', 'disk'], ['net', 'err'], ['big'], ['s']],
        'placements': [('cpu', 0, 0), ('mem', 0, 4), ('disk', 0, 8), ('net', 1, 0), ('err', 1, 6), ('big', 2, 0), ('s', 3, 0)],
        'row_count': 4, 'fill': [12, 12, 12, 1]}
    assert m.layout_panels(ps, 12) == m.layout_panels(tuple(ps))
    assert m.layout_panels([]) == {'rows': [], 'placements': [], 'row_count': 0, 'fill': []}
    assert m.layout_panels([('a', 12)]) == {'rows': [['a']], 'placements': [('a', 0, 0)], 'row_count': 1, 'fill': [12]}
    # exactly full vs one over
    assert m.layout_panels([('a', 6), ('b', 6)])['rows'] == [['a', 'b']]
    assert m.layout_panels([('a', 6), ('b', 7)])['rows'] == [['a'], ['b']]
    assert m.layout_panels([('a', 6), ('b', 5), ('c', 1)])['fill'] == [12]
    assert m.layout_panels([('a', 6), ('b', 5), ('c', 2)])['fill'] == [11, 2]
    # earlier gaps are not filled by later small panels
    assert m.layout_panels([('a', 8), ('b', 8), ('c', 2)], 12)['rows'] == [['a'], ['b', 'c']]
    assert m.layout_panels([['a', 1], ('b', 1)], 1) == {'rows': [['a'], ['b']], 'placements': [('a', 0, 0), ('b', 1, 0)], 'row_count': 2, 'fill': [1, 1]}
    assert m.layout_panels([('a', 24), ('b', 24)], 24)['row_count'] == 2
    assert m.layout_panels([('a', 12), ('b', 12)], 24)['rows'] == [['a', 'b']]
    assert m.layout_panels([('t' * 24, 1)])['rows'] == [['t' * 24]]
    # default columns 12: widths 5, 5, 3 split after the second panel, widths 5, 5, 2 do not
    assert m.layout_panels([('a', 5), ('b', 5), ('c', 3)])['rows'] == [['a', 'b'], ['c']]
    assert m.layout_panels([('a', 5), ('b', 5), ('c', 2)])['rows'] == [['a', 'b', 'c']]
    assert m.layout_panels([('p%d' % i, 1) for i in range(30)])['fill'] == [12, 12, 6]
    assert m.layout_panels([('a', 12), ('b', 12)], 12)['row_count'] == 2
    rng = random.Random(634)
    for _ in range(500):
        cols = rng.randint(1, 24)
        ps = [('p%d' % k, rng.randint(1, cols)) for k in range(rng.randint(0, 15))]
        assert m.layout_panels(ps, cols) == _oracle(ps, cols), (ps, cols)


def _late(m):
    PN = 'panels must be a list or tuple'
    CL = 'columns must be a nonbool integer between 1 and 24'
    EP = 'each panel must be a (title, width) pair'
    TT = 'panel titles must be strings of 1 to 24 characters'
    WD = 'width must be a nonbool integer between 1 and 24'
    WX = 'width must not exceed columns'
    good = ('a', 1)
    for bad in ('ab', None, 5, {}, L([good]), T([good]), L(), T()):
        _raises(TypeError, PN, m.layout_panels, bad)
    _raises(TypeError, PN, m.layout_panels, L([good] * 31))
    _raises(ValueError, 'panels must contain at most 30 entries', m.layout_panels, [('p%d' % i, 1) for i in range(31)])
    assert m.layout_panels([('p%d' % i, 1) for i in range(30)])['row_count'] == 3
    for bad in (0, 25, True, False, 1.0, '1', None, I(12), LyingI(12), LyingI(10 ** 30), I(10 ** 30)):
        _raises(ValueError, CL, m.layout_panels, [good], bad)
    for K in (L, T):
        for bad in (K(good), K(('a',))):
            _raises(ValueError, EP, m.layout_panels, [bad])
            _raises(ValueError, EP, m.layout_panels, [good, bad])
    for bad in ('ab', None, 5, ('a',), ('a', 1, 1), ()):
        _raises(ValueError, EP, m.layout_panels, [bad])
        _raises(ValueError, EP, m.layout_panels, [good, bad])
    for bad in ('', 'x' * 25, None, 5, S('b'), LyingS('b'), b'b'):
        _raises(ValueError, TT, m.layout_panels, [(bad, 1)])
        _raises(ValueError, TT, m.layout_panels, [good, (bad, 1)])
    _raises(ValueError, 'duplicate panel title', m.layout_panels, [good, good])
    _raises(ValueError, 'duplicate panel title', m.layout_panels, [good, ('b', 1), ('a', 1)])
    for bad in (0, 25, -1, True, False, 1.0, '1', None, I(1), LyingI(1), LyingI(10 ** 30), I(10 ** 30)):
        _raises(ValueError, WD, m.layout_panels, [('b', bad)], 24)
        _raises(ValueError, WD, m.layout_panels, [good, ('b', bad)], 24)
    _raises(ValueError, WX, m.layout_panels, [('b', 13)])
    _raises(ValueError, WX, m.layout_panels, [good, ('b', 13)])
    _raises(ValueError, WX, m.layout_panels, [('b', 2)], 1)
    assert m.layout_panels([('b', 12)])['fill'] == [12] and m.layout_panels([('b', 24)], 24)['fill'] == [24]
    # order: panels, size, columns, then per panel: shape, title, duplicate, width, width vs columns
    _raises(TypeError, PN, m.layout_panels, L([1]), I(1))
    _raises(ValueError, CL, m.layout_panels, [1], I(1))
    _raises(ValueError, EP, m.layout_panels, [1], 5)
    _raises(ValueError, TT, m.layout_panels, [(S('a'), I(1))])
    _raises(ValueError, 'duplicate panel title', m.layout_panels, [good, ('a', I(1))])          # duplicate before the width check
    _raises(ValueError, WD, m.layout_panels, [('a', I(1))])
    _raises(ValueError, WD, m.layout_panels, [('a', 99)], 1)                                     # range before the columns check


class I(int):
    pass


class L(list):
    pass


class T(tuple):
    pass


class S(str):
    pass


class LyingS(str):
    def __eq__(self, o): return True
    def __ne__(self, o): return False
    def __hash__(self): return hash('a')


class LyingI(int):
    def __ge__(self, o): return True
    def __le__(self, o): return True
    def __gt__(self, o): return True
    def __lt__(self, o): return False
    def __eq__(self, o): return True
    def __ne__(self, o): return False
    __hash__ = int.__hash__


def battery(m):
    _core(m)
    _late(m)


def test_battery_on_real_module():
    battery(mod)


def test_result_is_fresh_and_panels_unchanged():
    ps = [('a', 3)]
    r = mod.layout_panels(ps)
    r['rows'][0].append('zzz')
    r['fill'].append(99)
    assert ps == [('a', 3)]
    assert mod.layout_panels(ps)['rows'] == [['a']]


MUTANTS = [
    ("type(panels) not in (list, tuple)", "not isinstance(panels, (list, tuple))"),
    ("len(panels) > MAX_PANELS", "len(panels) >= MAX_PANELS"),
    ("MAX_PANELS = 30", "MAX_PANELS = 31"),
    ("type(v) is not int or not lo <= v <= hi", "isinstance(v, bool) or not isinstance(v, int) or not lo <= v <= hi"),
    ("type(v) is not int or not lo <= v <= hi", "not isinstance(v, int) or not lo <= v <= hi"),
    ("not lo <= v <= hi", "not lo < v <= hi"),
    ("not lo <= v <= hi", "not lo <= v < hi"),
    ("_int(columns, 1, 24", "_int(columns, 0, 24"),
    ("_int(columns, 1, 24", "_int(columns, 1, 25"),
    ("columns=12", "columns=13"),
    ("columns=12", "columns=11"),
    ("type(p) not in (list, tuple) or len(p) != 2", "not isinstance(p, (list, tuple)) or len(p) != 2"),
    ("or len(p) != 2", "or len(p) > 2"),
    ("or len(p) != 2", "or len(p) < 2"),
    ("type(title) is not str", "not isinstance(title, str)"),
    ("not 1 <= len(title) <= 24", "not 0 <= len(title) <= 24"),
    ("not 1 <= len(title) <= 24", "not 1 <= len(title) <= 25"),
    ("not 1 <= len(title) <= 24", "not 1 <= len(title) < 24"),
    ("if title in titles:", "if False:"),
    ("_int(width, 1, 24", "_int(width, 0, 24"),
    ("_int(width, 1, 24", "_int(width, 1, 25"),
    ("if width > columns:", "if width >= columns:"),
    ("if width > columns:", "if False:"),
    ("fill[-1] + width > columns", "fill[-1] + width >= columns"),
    ("fill[-1] + width > columns", "fill[-1] + width > columns + 1"),
    ("if not rows or", "if"),
    ("placements.append((title, len(rows) - 1, fill[-1]))", "placements.append((title, len(rows), fill[-1]))"),
    ("placements.append((title, len(rows) - 1, fill[-1]))", "placements.append((title, len(rows) - 1, fill[-1] + 1))"),
    ("fill[-1] += width", "fill[-1] += 1"),
    ("'row_count': len(rows)", "'row_count': len(rows) + 1"),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)
