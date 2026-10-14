import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import cqrs as mod

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


def test_scope_and_package_rules():
    assert mod.SCOPE.startswith('PARTIAL')
    assert len(mod.NOT_CLAIMED) >= 4 and 'NOT_CLAIMED' in mod.__doc__
    assert not (ROOT / '__init__.py').exists()


def _oracle(cmds):
    accepted, events, rejected = [], [], []
    for i, (op, acct, amt) in enumerate(cmds):
        delta = amt if op == 'deposit' else -amt
        bal = sum(d for a, d in accepted if a == acct)
        if bal + delta < 0:
            rejected.append((i, 'insufficient funds'))
        else:
            accepted.append((acct, delta))
            events.append((len(events), acct, 'deposited' if delta > 0 else 'withdrawn', amt))
    view = {}
    for a, d in accepted:
        view.setdefault(a, 0)
    for a in view:
        view[a] = sum(d for x, d in accepted if x == a)
    return events, view, rejected


def _core(m):
    r = m.run_cqrs([('deposit', 'a', 5), ('withdraw', 'a', 5), ('withdraw', 'a', 1), ('deposit', 'b', 2)])
    assert r['read_model'] == {'a': 0, 'b': 2}
    assert r['rejected'] == [(2, 'insufficient funds')]
    assert [e['seq'] for e in r['events']] == [0, 1, 2] and r['command_count'] == 4
    assert m.run_cqrs([]) == {'events': [], 'read_model': {}, 'rejected': [], 'command_count': 0}
    rng = random.Random(649)
    for _ in range(200):
        cmds = [(rng.choice(['deposit', 'withdraw']), rng.choice('abc'), rng.randint(1, 30))
                for _ in range(rng.randint(0, 50))]
        r = m.run_cqrs(cmds)
        ev, view, rej = _oracle(cmds)
        assert [(e['seq'], e['account'], e['kind'], e['amount']) for e in r['events']] == ev
        assert r['read_model'] == view and r['rejected'] == rej
        assert all(v >= 0 for v in r['read_model'].values())
        assert m.project(r['events']) == r['read_model']
    assert m.run_cqrs([('withdraw', 'a', 1000000)])['rejected'] == [(0, 'insufficient funds')]
    assert m.run_cqrs([('deposit', 'a' * 16, 1000000)])['read_model'] == {'a' * 16: 1000000}
    assert len(m.run_cqrs([('deposit', 'a', 1)] * 50)['events']) == 50
    _raises(ValueError, 'commands must contain at most 50 entries', m.run_cqrs, [('deposit', 'a', 1)] * 51)
    _raises(TypeError, 'commands must be a list or tuple', m.run_cqrs, 'x')
    _raises(ValueError, 'each command must be an (operation, account, amount) triple', m.run_cqrs, [('deposit', 'a')])
    _raises(ValueError, 'each command must be an (operation, account, amount) triple', m.run_cqrs, ['abc'])
    _raises(ValueError, 'operation must be deposit or withdraw', m.run_cqrs, [('burn', 'a', 1)])
    _raises(ValueError, 'operation must be deposit or withdraw', m.run_cqrs, [(1, 'a', 1)])
    for bad in ('', 'a' * 17, 5):
        _raises(ValueError, 'account must be a string of 1 to 16 characters', m.run_cqrs, [('deposit', bad, 1)])
    for bad in (True, 0, 1000001, 1.0, '1'):
        _raises(ValueError, 'amount must be a nonbool integer between 1 and 1000000', m.run_cqrs, [('deposit', 'a', bad)])
    # caps fire before any later entry is inspected
    _raises(ValueError, 'commands must contain at most 50 entries', m.run_cqrs, [None] * 51)


def test_battery_on_real_module():
    battery(mod)


def test_literal_example():
    r = mod.run_cqrs([('deposit', 'x', 10), ('withdraw', 'x', 4), ('withdraw', 'x', 7)])
    assert r['events'] == [{'seq': 0, 'account': 'x', 'kind': 'deposited', 'amount': 10},
                           {'seq': 1, 'account': 'x', 'kind': 'withdrawn', 'amount': 4}]
    assert r['read_model'] == {'x': 6} and r['rejected'] == [(2, 'insufficient funds')]



class I(int):
    pass


class L(list):
    pass


class T(tuple):
    pass


class Dc(dict):
    pass


class S(str):
    pass


def _late(m):
    _raises(TypeError, 'commands must be a list or tuple', m.run_cqrs, L([('deposit', 'a', 1)]))
    _raises(ValueError, 'each command must be an (operation, account, amount) triple', m.run_cqrs, [('deposit', 'a', 1), T(('deposit', 'a', 1))])
    _raises(ValueError, 'operation must be deposit or withdraw', m.run_cqrs, [('deposit', 'a', 1), (S('deposit'), 'a', 1)])
    _raises(ValueError, 'account must be a string of 1 to 16 characters', m.run_cqrs, [('deposit', 'a', 1), ('deposit', S('a'), 1)])
    _raises(ValueError, 'amount must be a nonbool integer between 1 and 1000000', m.run_cqrs, [('deposit', 'a', 1), ('deposit', 'a', I(5))])
    ok = ('deposit', 'a', 1)
    _raises(ValueError, 'each command must be an (operation, account, amount) triple', m.run_cqrs, [ok, ('deposit', 'a')])
    _raises(ValueError, 'operation must be deposit or withdraw', m.run_cqrs, [ok, ('burn', 'a', 1)])
    _raises(ValueError, 'account must be a string of 1 to 16 characters', m.run_cqrs, [ok, ('deposit', '', 1)])
    _raises(ValueError, 'amount must be a nonbool integer between 1 and 1000000', m.run_cqrs, [ok, ('deposit', 'a', 0)])
    _raises(ValueError, 'amount must be a nonbool integer between 1 and 1000000', m.run_cqrs, [ok, ('deposit', 'a', True)])
    _raises(ValueError, 'amount must be a nonbool integer between 1 and 1000000', m.run_cqrs, [ok] * 49 + [('deposit', 'a', 1000001)])


def _sym(m):
    OUT = 'commands must be a list or tuple'
    ROW = 'each command must be an (operation, account, amount) triple'
    for K in (L, T):
        _raises(TypeError, OUT, m.run_cqrs, K([('deposit', 'a', 1)]))
        _raises(ValueError, ROW, m.run_cqrs, [K(('deposit', 'a', 1))])
        _raises(ValueError, ROW, m.run_cqrs, [('deposit', 'a', 1), K(('deposit', 'a', 1))])
        _raises(ValueError, ROW, m.run_cqrs, [K(('deposit', 'a', 1)), ('deposit', 'a', 1)])


def battery(m):
    _core(m)
    _late(m)
    _sym(m)

MUTANTS = [
    ('type(commands) not in (list, tuple)', 'not isinstance(commands, (list, tuple))'),
    ('amt > have', 'amt >= have'), ('amt > have', 'amt > have + 1'),
    ("have + amt if op == 'deposit' else have - amt", "have + amt if op == 'deposit' else have + amt"),
    ("have + amt if op == 'deposit' else have - amt", "have - amt if op == 'deposit' else have - amt"),
    ("else -1", "else 1"), ("sign = 1 if", "sign = -1 if"), ('(i, ', '(i + 1, '),
    ("'seq': len(events)", "'seq': len(events) + 1"), ('> MAX_COMMANDS', '> MAX_COMMANDS + 1'),
    ('1 <= amt <= 1000000', '1 <= amt <= 1000001'), ('1 <= amt <= 1000000', '0 <= amt <= 1000000'),
    ('not 1 <= len(acct) <= 16', 'not 1 <= len(acct) <= 17'), ('type(amt) is not int', 'isinstance(amt, bool) or not isinstance(amt, int)'),
    ("op not in ('deposit', 'withdraw')", "op not in ('deposit',)"), ('len(c) != 3', 'len(c) != 4'),
    ("'command_count': len(commands)", "'command_count': len(events)"),
    ('rejected.append', 'pass  #'),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)
