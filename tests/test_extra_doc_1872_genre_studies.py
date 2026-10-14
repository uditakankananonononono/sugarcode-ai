import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import genre_studies as mod

SRC = pathlib.Path(mod.__file__).read_text()
ROOT = pathlib.Path(mod.__file__).parent

NAMES = ('alpha', 'beta', 'Üser-9!', 'Zoë_2', 'Ω-1', 'q?7', 'B', 'x.y,z')
SM = 'row 1: shelf must be a string of 1 to 16 characters'
BM = 'row 1: book must be a string of 1 to 16 characters'
CM = 'row 1: code must be a nonbool integer between 1 and 99'


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
    code = compile(mutated, 'mutant', 'exec')
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


def test_scope_and_package_rules():
    assert mod.SCOPE.startswith('PARTIAL')
    assert len(mod.NOT_CLAIMED) >= 4 and 'NOT_CLAIMED' in mod.__doc__
    assert not (ROOT / '__init__.py').exists()


def test_disclaimer_text_exact():
    section = ' '.join(mod.__doc__.split('NOT_CLAIMED:', 1)[1].split())
    assert section == ('real librarianship, numerology, collection '
                       'value, genre boundaries, production readiness.')
    assert mod.SCOPE == 'PARTIAL: shelf classification over supplied codes'
    assert mod.NOT_CLAIMED == ('real librarianship', 'numerology',
                               'collection value', 'genre boundaries',
                               'production readiness')


def _expected(rows):
    books = {}
    totals = {}
    for shelf, book, code in rows:
        if shelf not in books:
            books[shelf] = 0
        books[shelf] += 1
        if shelf not in totals:
            totals[shelf] = 0
        totals[shelf] += code
    roots = {}
    for shelf in totals:
        root = totals[shelf] % 9
        roots[shelf] = root if root else 9
    prime = sorted(s for s in roots if roots[s] in (2, 3, 5, 7))
    perfect = sorted(s for s in roots if roots[s] == 9)
    holders = {}
    for shelf in roots:
        if roots[shelf] not in holders:
            holders[roots[shelf]] = 0
        holders[roots[shelf]] += 1
    dominant = None
    for root in holders:
        if (dominant is None or holders[root] > holders[dominant]
                or (holders[root] == holders[dominant]
                    and root < dominant)):
            dominant = root
    return {'total': len(rows), 'books': books, 'roots': roots,
            'prime': prime, 'perfect': perfect, 'dominant': dominant}


def _core(m):
    # fixed pins, oracle seeded with row number 1872
    assert m.classify_shelves([('s1', 'b1', 10), ('s1', 'b2', 8),
                               ('s2', 'b1', 9), ('s3', 'b1', 2),
                               ('s3', 'b2', 4)]) == {
        'total': 5, 'books': {'s1': 2, 's2': 1, 's3': 2},
        'roots': {'s1': 9, 's2': 9, 's3': 6},
        'prime': [], 'perfect': ['s1', 's2'], 'dominant': 9}
    # one book: its code is the root unless it is 9
    assert m.classify_shelves([('a', 'b', 4)]) == {
        'total': 1, 'books': {'a': 1}, 'roots': {'a': 4},
        'prime': [], 'perfect': [], 'dominant': 4}
    # a total of 9 has root 9, not 0
    r = m.classify_shelves([('a', 'x', 9)])
    assert r['roots'] == {'a': 9} and r['perfect'] == ['a']
    # a total of 18 has root 9
    r = m.classify_shelves([('a', 'x', 10), ('a', 'y', 8)])
    assert r['roots'] == {'a': 9}
    # a total of 10 has root 1
    r = m.classify_shelves([('a', 'x', 10)])
    assert r['roots'] == {'a': 1} and r['prime'] == []
    # prime roots are 2, 3, 5 and 7
    r = m.classify_shelves([('a', 'x', 2), ('b', 'y', 3),
                            ('c', 'z', 5), ('d', 'w', 7),
                            ('e', 'v', 4)])
    assert r['prime'] == ['a', 'b', 'c', 'd'] and r['perfect'] == []
    # the dominant tie goes to the smaller root
    r = m.classify_shelves([('a', 'x', 5), ('b', 'y', 2)])
    assert r['dominant'] == 2
    # a strictly more common root replaces the dominant
    r = m.classify_shelves([('a', 'x', 2), ('b', 'y', 2), ('c', 'z', 7)])
    assert r['dominant'] == 2
    # codes pile up before the root is taken
    r = m.classify_shelves([('a', 'x', 50), ('a', 'y', 50)])
    assert r['roots'] == {'a': 1}
    # dicts keep first-touch order
    r = m.classify_shelves([('b', 'x', 1), ('a', 'y', 2)])
    assert r['books'] == {'b': 1, 'a': 1}
    # non-ASCII shelves follow the same rule
    r = m.classify_shelves([('Üser-9!', 'Ω-1', 18), ('q?7', 'B', 7)])
    assert r == {'total': 2, 'books': {'Üser-9!': 1, 'q?7': 1},
                 'roots': {'Üser-9!': 9, 'q?7': 7}, 'prime': ['q?7'],
                 'perfect': ['Üser-9!'], 'dominant': 7}
    rng = random.Random(1872)
    for _ in range(300):
        rows = [(rng.choice(NAMES), rng.choice(NAMES), rng.randint(1, 99))
                for _ in range(rng.randint(1, 60))]
        assert m.classify_shelves(rows) == _expected(rows)
    return True


def _late(m):
    _raises(TypeError, 'rows must be a list or tuple', m.classify_shelves, 'ab')
    _raises(TypeError, 'rows must be a list or tuple', m.classify_shelves, 123)
    _raises(ValueError, 'rows must contain between 1 and 60 entries',
            m.classify_shelves, [])
    _raises(ValueError, 'rows must contain between 1 and 60 entries',
            m.classify_shelves, [('a', 'b', 1)] * 61)
    _raises(TypeError, 'row 2: expected a (shelf, book, code) triple',
            m.classify_shelves, [('a', 'b', 1), 'bad'])
    _raises(ValueError, 'row 2: expected 3 fields, got 2',
            m.classify_shelves, [('a', 'b', 1), ('a', 'b')])
    _raises(ValueError, 'row 2: expected 3 fields, got 4',
            m.classify_shelves, [('a', 'b', 1), ('a', 'b', 1, 1)])
    _raises(ValueError, SM, m.classify_shelves, [(1, 'b', 1)])
    _raises(ValueError, SM, m.classify_shelves, [('', 'b', 1)])
    _raises(ValueError, SM, m.classify_shelves, [('x' * 17, 'b', 1)])
    _raises(ValueError, BM, m.classify_shelves, [('a', 1, 1)])
    _raises(ValueError, BM, m.classify_shelves, [('a', '', 1)])
    _raises(ValueError, BM, m.classify_shelves, [('a', 'x' * 17, 1)])
    _raises(ValueError, CM, m.classify_shelves, [('a', 'b', '1')])
    _raises(ValueError, CM, m.classify_shelves, [('a', 'b', 0)])
    _raises(ValueError, CM, m.classify_shelves, [('a', 'b', 100)])
    _raises(ValueError, CM, m.classify_shelves, [('a', 'b', True)])
    # first bad row pins
    _raises(ValueError, 'row 3: shelf must be a string of 1 to 16 characters',
            m.classify_shelves, [('a', 'b', 1), ('c', 'd', 1), ('', 'e', 1)])
    _raises(ValueError, 'row 2: code must be a nonbool integer between 1 and 99',
            m.classify_shelves, [('a', 'b', 1), ('c', 'd', 0)])
    # shelf is validated before book, book before code
    _raises(ValueError, SM, m.classify_shelves, [('x' * 17, '', 0)])
    _raises(ValueError, BM, m.classify_shelves, [('a', '', 0)])
    # validation order: bad container before contents
    _raises(TypeError, 'rows must be a list or tuple', m.classify_shelves, {'e': 1})
    # tuple rows accepted exactly like lists
    assert m.classify_shelves((('a', 'b', 1),)) == m.classify_shelves([('a', 'b', 1)])
    # mixed list/tuple row containers, both orders
    mixed = m.classify_shelves([('a', 'x', 2), ['b', 'y', 1], ('a', 'y', 3)])
    assert mixed == m.classify_shelves([['a', 'x', 2], ('b', 'y', 1), ['a', 'y', 3]])
    # boundary acceptance pins
    assert m.classify_shelves([('a', 'b', 1)] * 60)['total'] == 60
    assert m.classify_shelves([('a', 'b', 99)])['roots'] == {'a': 9}
    # pre-seed pin: fresh accumulators only
    assert m.classify_shelves([('a', 'x', 11), ('b', 'y', 9), ('a', 'z', 7)]) == {
        'total': 3, 'books': {'a': 2, 'b': 1},
        'roots': {'a': 9, 'b': 9}, 'prime': [], 'perfect': ['a', 'b'],
        'dominant': 9}
    return True


class L(list):
    pass


class T(tuple):
    pass


class S(str):
    pass


class I(int):
    pass


def _sym(m):
    P = 'rows must be a list or tuple'
    for K in (L, T):
        _raises(TypeError, P, m.classify_shelves, K([('a', 'b', 1)]))
        _raises(TypeError,
                'row 1: expected a (shelf, book, code) triple',
                m.classify_shelves, [K(('a', 'b', 1))])
    _raises(ValueError, SM, m.classify_shelves, [(S('a'), 'b', 1)])
    _raises(ValueError, BM, m.classify_shelves, [('a', S('b'), 1)])
    _raises(ValueError, CM, m.classify_shelves, [('a', 'b', I(1))])
    return True


def battery(m):
    _core(m)
    _late(m)
    _sym(m)
    return True


MUTANTS = [
    ('type(rows) not in (list, tuple)', 'not isinstance(rows, (list, tuple))'),
    ('not 1 <= len(rows) <= 60', 'not 1 <= len(rows) <= 61'),
    ('not 1 <= len(rows) <= 60', 'not 0 <= len(rows) <= 60'),
    ('type(row) not in (list, tuple)', 'not isinstance(row, (list, tuple))'),
    ('len(row) != 3', 'len(row) != 2'),
    ('type(shelf) is not str', 'not isinstance(shelf, str)'),
    ('type(book) is not str', 'not isinstance(book, str)'),
    ('type(code) is not int', 'not isinstance(code, int)'),
    ('not 1 <= len(shelf) <= 16', 'not 1 <= len(shelf) <= 17'),
    ('not 1 <= len(book) <= 16', 'not 1 <= len(book) <= 17'),
    ('not 1 <= code <= 99', 'not 1 <= code <= 100'),
    ('        books[shelf] += 1', '        books[shelf] += 0'),
    ('        totals[shelf] += code', '        totals[shelf] += 1'),
    ('        root = totals[shelf] % 9', '        root = totals[shelf] % 10'),
    ('        roots[shelf] = root if root else 9',
     '        roots[shelf] = root'),
    ("if roots[s] in (2, 3, 5, 7)", "if roots[s] in (2, 3, 5)"),
    ("perfect = sorted(s for s in roots if roots[s] == 9)",
     "perfect = sorted(s for s in roots if roots[s] == 8)"),
    ('if (dominant is None or holders[root] > holders[dominant]',
     'if (dominant is None or holders[root] < holders[dominant]'),
    ("'prime': prime", "'prime': perfect"),
    ("'total': len(rows)", "'total': len(books)"),
    ('        shelf, book, code = row',
     '        book, shelf, code = row'),
    ('for i, row in enumerate(rows, 1):', 'for i, row in enumerate(rows):'),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)


def test_battery_on_real_module():
    assert battery(mod) is True
