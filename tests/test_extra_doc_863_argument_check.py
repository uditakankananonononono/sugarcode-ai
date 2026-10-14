import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import argument_check as mod

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
    assert mod.SCOPE == 'PARTIAL: forward-chains supplied if-then rules over supplied facts, no argument is judged'
    assert len(mod.NOT_CLAIMED) == 5 and 'informal fallacies' in mod.NOT_CLAIMED and 'truth of premises' in mod.NOT_CLAIMED
    assert 'NOT_CLAIMED' in mod.__doc__
    assert 'Critical Thinking - Evaluates arguments' in mod.__doc__
    assert not (ROOT / '__init__.py').exists()


def _oracle(fs, rs, c):
    """Independent: sweep all rules repeatedly until a full sweep adds nothing."""
    have = list(fs)
    grew = True
    while grew:
        grew = False
        for a, b in rs:
            if a in have and b not in have:
                have.append(b)
                grew = True
    return {'derived': sorted(have), 'steps': len(have) - len(fs), 'valid': c in have,
            'unsupported': sorted(a for a, b in rs if b == c and a not in have)}


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


def _core(m):
    f = m.argument_check
    assert f(['p'], [('p', 'q')], 'q') == {'derived': ['p', 'q'], 'steps': 1, 'valid': True, 'unsupported': []}
    assert f(['p'], [('p', 'q')], 'p') == {'derived': ['p', 'q'], 'steps': 1, 'valid': True, 'unsupported': []}
    # affirming the consequent: q is a fact, the rule p -> q does not give p back
    assert f(['q'], [('p', 'q')], 'p') == {'derived': ['q'], 'steps': 0, 'valid': False, 'unsupported': []}
    # a rule that concludes the conclusion with an unmet if_part is reported
    assert f(['q'], [('p', 'r')], 'r') == {'derived': ['q'], 'steps': 0, 'valid': False, 'unsupported': ['p']}
    assert f(['a'], [('x', 'r'), ('b', 'r'), ('a', 'b')], 'r') == {'derived': ['a', 'b', 'r'], 'steps': 2, 'valid': True, 'unsupported': ['x']}
    # a chain in reverse listing order still closes
    assert f(['a'], [('c', 'd'), ('b', 'c'), ('a', 'b')], 'd') == {'derived': ['a', 'b', 'c', 'd'], 'steps': 3, 'valid': True, 'unsupported': []}
    # branching and joins
    r = f(['a', 'z'], [('a', 'b'), ('a', 'c'), ('b', 'd'), ('c', 'd'), ('d', 'e')], 'e')
    assert r == {'derived': ['a', 'b', 'c', 'd', 'e', 'z'], 'steps': 4, 'valid': True, 'unsupported': []}
    # the rules only fire forward, and a cycle terminates
    assert f(['a'], [('a', 'b'), ('b', 'a')], 'b') == {'derived': ['a', 'b'], 'steps': 1, 'valid': True, 'unsupported': []}
    assert f(['b'], [('a', 'b')], 'a')['valid'] is False
    assert f(['a'], [('a', 'b')], 'z') == {'derived': ['a', 'b'], 'steps': 1, 'valid': False, 'unsupported': []}
    assert f(['a', 'b'], [('a', 'b')], 'b') == {'derived': ['a', 'b'], 'steps': 0, 'valid': True, 'unsupported': []}
    assert f(('a',), (['a', 'b'], ('b', 'c')), 'c')['valid'] is True
    assert f(['A'], [('a', 'b')], 'b')['valid'] is False
    assert f(['A~ z'], [('A~ z', 'x' * 12)], 'x' * 12)['valid'] is True
    assert f(list('abcd'), [('a', 'e'), ('e', 'f'), ('f', 'g'), ('g', 'h'), ('h', 'i'), ('i', 'j')], 'j')['steps'] == 6
    rng = random.Random(863)
    pool = 'abcdefgh'
    for _ in range(1500):
        fs = rng.sample(pool, rng.randint(1, 4))
        pairs = [(a, b) for a in pool for b in pool if a != b]
        rs = rng.sample(pairs, rng.randint(1, 6))
        rs = [rng.choice((list, tuple))(p) for p in rs]
        c = rng.choice(pool)
        assert f(fs, rs, c) == _oracle(fs, rs, c), (fs, rs, c)


def _late(m):
    f = m.argument_check
    FT = 'facts must be a list or tuple'
    FS = 'facts must contain 1 to 4 entries'
    FE = 'each fact must be a printable ASCII string of 1 to 12 characters'
    FD = 'facts must be distinct'
    RT = 'rules must be a list or tuple'
    RS = 'rules must contain 1 to 6 entries'
    RE = 'each rule must be an (if_part, then_part) tuple'
    IF = 'each if_part must be a printable ASCII string of 1 to 12 characters'
    TH = 'each then_part must be a printable ASCII string of 1 to 12 characters'
    SA = 'a rule must have different if_part and then_part'
    RD = 'rules must be distinct'
    CO = 'conclusion must be a printable ASCII string of 1 to 12 characters'
    ok = [('a', 'b')]
    names = ('', 'x' * 13, None, 5, True, S('a'), LyingS('a'), b'a', ['a'], '\u00e9', 'caf\u00e9', 'a\u00e9', '\u4e2d', '\u0661',
             '\n', 'a\n', '\ta', 'a\x00', '\x7f', 'a\r', '\x1b[0m', 'a\x0b')
    for bad in ('ab', None, 5, {}, L(['a']), T(['a']), L(), T()):
        _raises(TypeError, FT, f, bad, ok, 'a')
    _raises(ValueError, FS, f, [], ok, 'a')
    _raises(ValueError, FS, f, list('abcde'), ok, 'a')
    f(list('abcd'), ok, 'a')
    for bad in names:
        _raises(ValueError, FE, f, [bad], ok, 'a')
        _raises(ValueError, FE, f, ['a', bad], ok, 'a')
    f([' '], ok, 'a')
    _raises(ValueError, FD, f, ['a', 'a'], ok, 'a')
    for bad in ('ab', None, 5, {}, L(ok), T(ok), L(), T()):
        _raises(TypeError, RT, f, ['a'], bad, 'a')
    _raises(ValueError, RS, f, ['a'], [], 'a')
    _raises(ValueError, RS, f, ['a'], [('a', chr(98 + i)) for i in range(7)], 'a')
    f(['a'], [('a', chr(98 + i)) for i in range(6)], 'a')
    for bad in ('ab', None, 5, ('a',), ('a', 'b', 'c'), (), {'a': 1}, L(['a', 'b']), T(('a', 'b'))):
        _raises(ValueError, RE, f, ['a'], [bad], 'a')
        _raises(ValueError, RE, f, ['a'], [('a', 'b'), bad], 'a')
    for bad in names:
        _raises(ValueError, IF, f, ['a'], [(bad, 'b')], 'a')
        _raises(ValueError, IF, f, ['a'], [('a', 'b'), (bad, 'c')], 'a')
        _raises(ValueError, TH, f, ['a'], [('a', bad)], 'a')
        _raises(ValueError, TH, f, ['a'], [('a', 'b'), ('a', bad)], 'a')
        _raises(ValueError, CO, f, ['a'], ok, bad)
    _raises(ValueError, SA, f, ['a'], [('a', 'a')], 'a')
    _raises(ValueError, SA, f, ['a'], [('a', 'b'), ('c', 'c')], 'a')
    _raises(ValueError, RD, f, ['a'], [('a', 'b'), ('a', 'b')], 'a')
    f(['a'], [('a', 'b'), ('b', 'a')], 'a')
    f(['a'], [('a', 'b'), ('a', 'c')], 'a')
    f(['a'], ok, ' ')
    _raises(TypeError, FT, f, None, None, None)
    _raises(ValueError, FS, f, [], None, None)
    _raises(ValueError, FE, f, [1, 1], None, None)
    _raises(ValueError, FD, f, ['a', 'a'], None, None)
    _raises(TypeError, RT, f, ['a'], None, None)
    _raises(ValueError, RS, f, ['a'], [], None)
    _raises(ValueError, RE, f, ['a'], [1], None)
    _raises(ValueError, IF, f, ['a'], [(1, 1)], None)
    _raises(ValueError, TH, f, ['a'], [('a', 1)], None)
    _raises(ValueError, SA, f, ['a'], [('a', 'a'), ('a', 'a')], None)
    _raises(ValueError, RD, f, ['a'], [('a', 'b'), ('a', 'b')], None)
    _raises(ValueError, CO, f, ['a'], ok, None)


def battery(m):
    _core(m)
    _late(m)


def test_battery_on_real_module():
    battery(mod)


LB = "type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12"
MUTANTS = [
    (LB, "isinstance(x, str) and x.isascii() and x.isprintable() and 1 <= len(x) <= 12"),
    (LB, "type(x) is str and x.isprintable() and 1 <= len(x) <= 12"),
    (LB, "type(x) is str and x.isascii() and 1 <= len(x) <= 12"),
    (LB, "type(x) is str and x.isascii() and x.isalnum() and 1 <= len(x) <= 12"),
    (LB, "type(x) is str and x.isascii() and x.isprintable() and 0 <= len(x) <= 12"),
    (LB, "type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) < 12"),
    (LB, "type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 13"),
    ("type(facts) not in (list, tuple)", "not isinstance(facts, (list, tuple))"),
    ("not 1 <= len(facts) <= 4", "not 0 <= len(facts) <= 4"),
    ("not 1 <= len(facts) <= 4", "not 1 <= len(facts) < 4"),
    ("not 1 <= len(facts) <= 4", "not 1 <= len(facts) <= 5"),
    ("if len(set(facts)) != len(facts):", "if False:"),
    ("type(rules) not in (list, tuple)", "not isinstance(rules, (list, tuple))"),
    ("not 1 <= len(rules) <= 6", "not 0 <= len(rules) <= 6"),
    ("not 1 <= len(rules) <= 6", "not 1 <= len(rules) < 6"),
    ("not 1 <= len(rules) <= 6", "not 1 <= len(rules) <= 7"),
    ("type(r) not in (list, tuple) or len(r) != 2", "not isinstance(r, (list, tuple)) or len(r) != 2"),
    ("type(r) not in (list, tuple) or len(r) != 2", "type(r) not in (list, tuple) or len(r) > 2"),
    ("type(r) not in (list, tuple) or len(r) != 2", "type(r) not in (list, tuple) or len(r) < 2"),
    ("        if a == b:\n            raise", "        if False:\n            raise"),
    ("if len(set(pairs)) != len(pairs):", "if False:"),
    ("holds = set(facts)", "holds = set(facts[:1])"),
    ("queue = list(facts)", "queue = list(facts[:1])"),
    ("if a == now and b not in holds:", "if a != now and b not in holds:"),
    ("if a == now and b not in holds:", "if b == now and a not in holds:"),
    ("queue.append(b)", "pass"),
    ("'derived': sorted(holds)", "'derived': list(holds)"),
    ("'derived': sorted(holds)", "'derived': sorted(facts)"),
    ("'steps': len(holds) - len(facts)", "'steps': len(holds)"),
    ("'valid': conclusion in holds", "'valid': conclusion in facts"),
    ("'unsupported': sorted(a for a, b in pairs if b == conclusion and a not in holds)", "'unsupported': [a for a, b in pairs if b == conclusion and a not in holds]"),
    ("'unsupported': sorted(a for a, b in pairs if b == conclusion and a not in holds)", "'unsupported': sorted(a for a, b in pairs if b == conclusion)"),
    ("'unsupported': sorted(a for a, b in pairs if b == conclusion and a not in holds)", "'unsupported': sorted(a for a, b in pairs if b == conclusion and a not in facts)"),
    ("'unsupported': sorted(a for a, b in pairs if b == conclusion and a not in holds)", "'unsupported': sorted(b for a, b in pairs if a == conclusion and b not in holds)"),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)
