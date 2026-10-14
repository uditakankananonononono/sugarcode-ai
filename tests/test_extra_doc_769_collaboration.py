import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import collaboration as mod

SRC = pathlib.Path(mod.__file__).read_text()
ROOT = pathlib.Path(mod.__file__).parent


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
    pass


class LyingS(str):
    def __eq__(self, o): return True
    def __ne__(self, o): return False
    def __hash__(self): return hash('a')


def test_scope_and_package_rules():
    assert mod.SCOPE == 'PARTIAL: piece crediting over supplied rows, no real collaboration'
    assert len(mod.NOT_CLAIMED) >= 4 and 'editing' in mod.NOT_CLAIMED and 'NOT_CLAIMED' in mod.__doc__
    assert not (ROOT / '__init__.py').exists()
    assert (mod.MAX_ROWS, mod.MAX_NAME) == (100, 8)


def _oracle(rows):
    """Independent: contributor lists per piece via nested loops."""
    names = []
    for piece, contributor in rows:
        if piece not in names:
            names.append(piece)
    pieces = []
    for piece in sorted(names):
        who = []
        for piece2, contributor in rows:
            if piece2 == piece and contributor not in who:
                who.append(contributor)
        pieces.append((piece, sorted(who)))
    solo = 0
    joint = 0
    for piece, who in pieces:
        if len(who) == 1:
            solo += 1
        elif len(who) >= 2:
            joint += 1
    return {'pieces': pieces, 'solo': solo, 'joint': joint, 'total': len(rows)}


def _core(m):
    assert m.credit([('song', 'amy'), ('song', 'bo'), ('poem', 'cy'),
                     ('song', 'amy')]) == {
        'pieces': [('poem', ['cy']), ('song', ['amy', 'bo'])],
        'solo': 1, 'joint': 1, 'total': 4}
    assert m.credit([]) == {'pieces': [], 'solo': 0, 'joint': 0, 'total': 0}
    # a repeated (piece, contributor) pair credits once
    assert m.credit([('song', 'amy'), ('song', 'amy')])['pieces'] == [('song', ['amy'])]
    # pieces sort by name
    assert m.credit([('zz', 'a'), ('aa', 'b')])['pieces'] == [('aa', ['b']), ('zz', ['a'])]
    # contributors sort within a piece
    assert m.credit([('song', 'zz'), ('song', 'aa')])['pieces'] == [('song', ['aa', 'zz'])]
    # three contributors is still one joint piece
    assert m.credit([('s', 'a'), ('s', 'b'), ('s', 'c')])['joint'] == 1
    # a contributor on two pieces counts on both
    assert m.credit([('x', 'a'), ('y', 'a')])['pieces'] == [('x', ['a']), ('y', ['a'])]
    # solo and joint partition the pieces
    assert m.credit([('x', 'a'), ('y', 'a'), ('y', 'b')]) == {
        'pieces': [('x', ['a']), ('y', ['a', 'b'])], 'solo': 1, 'joint': 1, 'total': 3}
    # tuples accepted at every level
    assert m.credit((('s', 'a'),))['total'] == 1
    rng = random.Random(769)
    for _ in range(400):
        rows = [(rng.choice(['p1', 'p2', 'p3']), rng.choice(['a', 'b', 'cy']))
                for _ in range(rng.randint(0, 10))]
        assert m.credit(rows) == _oracle(rows)


def _late(m):
    CRD = 'credits must be a list or tuple'
    CAP = 'credits must contain at most 100 rows'
    ROW = 'each credit must be a (piece, contributor) row'
    PCE = 'piece must be a string of 1 to 8 characters'
    CON = 'contributor must be a string of 1 to 8 characters'
    good = [('s', 'a')]
    for bad in ('ab', None, 5, {}, L(good), T(good), L(), T()):
        _raises(TypeError, CRD, m.credit, bad)
    _raises(TypeError, CRD, m.credit, L(good * 101))            # subclass refused before the cap
    _raises(ValueError, CAP, m.credit, good * 101)
    assert m.credit(good * 100)['total'] == 100
    for bad in ('sa', 5, None, ('s',), ('s', 'a', 'x'), ()):
        _raises(ValueError, ROW, m.credit, [bad])
        _raises(ValueError, ROW, m.credit, [('s', 'a'), bad])
    for K in (L, T):
        _raises(ValueError, ROW, m.credit, [K(('s', 'a'))])
    for bad in ('', 'x' * 9, None, 5, b's', S('s'), LyingS('s'), I(1)):
        _raises(ValueError, PCE, m.credit, [(bad, 'a')])
        _raises(ValueError, PCE, m.credit, [('s', 'a'), (bad, 'b')])
    for bad in ('', 'x' * 9, None, 5, b'a', S('a'), LyingS('a'), I(1)):
        _raises(ValueError, CON, m.credit, [('s', bad)])
        _raises(ValueError, CON, m.credit, [('s', 'a'), ('t', bad)])
    assert m.credit([('x' * 8, 'y' * 8)])['total'] == 1
    assert m.credit([('x', 'y')])['total'] == 1                  # single-character names accepted
    # order: container, cap, rows (shape, piece, contributor)
    _raises(TypeError, CRD, m.credit, L(good))
    _raises(ValueError, CAP, m.credit, [('s', 1, 2)] * 101)
    _raises(ValueError, ROW, m.credit, [('s', 'a', 'x')])
    _raises(ValueError, PCE, m.credit, [(S('s'), 'a')])
    _raises(ValueError, CON, m.credit, [('s', S('a'))])
    # the first bad row reports first
    _raises(ValueError, PCE, m.credit, [(5, 6), ('s', 'a', 'x')])


def battery(m):
    _core(m)
    _late(m)


def test_battery_on_real_module():
    battery(mod)


def test_result_is_fresh_and_inputs_unchanged():
    rows = [('s', 'a'), ('s', 'b')]
    r = mod.credit(rows)
    r['pieces'].append(('bogus', ['x']))
    assert rows == [('s', 'a'), ('s', 'b')]
    assert mod.credit(rows)['joint'] == 1


MUTANTS = [
    ("    if type(rows_in) not in (list, tuple):", "    if not isinstance(rows_in, (list, tuple)):"),
    ("    if len(rows_in) > MAX_ROWS:", "    if len(rows_in) >= MAX_ROWS:"),
    ("MAX_ROWS = 100", "MAX_ROWS = 101"),
    ("        if type(row) not in (list, tuple) or len(row) != 2:",
     "        if not isinstance(row, (list, tuple)) or len(row) != 2:"),
    ("or len(row) != 2", "or len(row) > 2"),
    ("        if type(piece) is not str or not 1 <= len(piece) <= MAX_NAME:",
     "        if not isinstance(piece, str) or not 1 <= len(piece) <= MAX_NAME:"),
    ("not 1 <= len(piece) <= MAX_NAME", "not 1 <= len(piece) < MAX_NAME"),
    ("MAX_NAME = 8", "MAX_NAME = 9"),
    ("        if type(contributor) is not str or not 1 <= len(contributor) <= MAX_NAME:",
     "        if not isinstance(contributor, str) or not 1 <= len(contributor) <= MAX_NAME:"),
    ("    by_piece = {}", "    by_piece = {'zz': set(['a'])}"),
    ("        by_piece.setdefault(piece, set()).add(contributor)",
     "        by_piece.setdefault(piece, set()).add(piece)"),
    ("        by_piece.setdefault(piece, set()).add(contributor)",
     "        by_piece.setdefault(contributor, set()).add(piece)"),
    ("    pieces = sorted((piece, sorted(who)) for piece, who in by_piece.items())",
     "    pieces = sorted((piece, sorted(who, reverse=True)) for piece, who in by_piece.items())"),
    ("    pieces = sorted((piece, sorted(who)) for piece, who in by_piece.items())",
     "    pieces = sorted(((piece, sorted(who)) for piece, who in by_piece.items()), reverse=True)"),
    ("    solo = sum(1 for piece, who in pieces if len(who) == 1)",
     "    solo = sum(1 for piece, who in pieces if len(who) >= 1)"),
    ("    solo = sum(1 for piece, who in pieces if len(who) == 1)",
     "    solo = sum(1 for piece, who in pieces if len(who) == 2)"),
    ("    joint = sum(1 for piece, who in pieces if len(who) >= 2)",
     "    joint = sum(1 for piece, who in pieces if len(who) >= 3)"),
    ("    joint = sum(1 for piece, who in pieces if len(who) >= 2)",
     "    joint = sum(len(who) for piece, who in pieces if len(who) >= 2)"),
    ("    for piece, contributor in rows:\n        by_piece.setdefault(piece, set()).add(contributor)",
     "    for piece, contributor in rows[1:]:\n        by_piece.setdefault(piece, set()).add(contributor)"),
    ("    return {'pieces': pieces, 'solo': solo, 'joint': joint, 'total': len(rows)}",
     "    return {'pieces': pieces, 'solo': solo, 'joint': joint, 'total': len(rows) + 1}"),
    ("'credits must be a list or tuple'", "'credits must be a sequence'"),
    ("'credits must contain at most 100 rows'", "'credits must contain at most 99 rows'"),
    ("'each credit must be a (piece, contributor) row'", "'each credit must be a (piece, contributor) tuple'"),
    ("'piece must be a string of 1 to 8 characters'", "'piece must be a string of 1 to 7 characters'"),
    ("'contributor must be a string of 1 to 8 characters'", "'contributor must be a string of 1 to 7 characters'"),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)
