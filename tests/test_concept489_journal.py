import copy
import itertools as it
import pytest
from sugarcode.extra_doc import concept489_journal as m


def test_journal_oracles_exhaustive():
    # Expanded signed unit tokens, not production positive/negative sums.
    for n in range(5):
        for values in it.product(range(-2, 3), repeat=n):
            for accounts in it.product(range(2), repeat=n):
                lines = tuple((i, a, v) for i, (a, v) in enumerate(zip(accounts, values)))
                tokens = [(a, 1 if v > 0 else -1) for _, a, v in lines for _ in range(abs(v))]
                d = tokens.count((0, 1)) + tokens.count((1, 1))
                c = tokens.count((0, -1)) + tokens.count((1, -1))
                assert m.journal_balance(lines) == (d, c, d-c)
                expected = []
                for a in sorted(set(accounts)):
                    debit, credit = tokens.count((a, 1)), tokens.count((a, -1))
                    expected.append((a, debit, credit, debit-credit))
                assert m.journal_account_totals(lines) == tuple(expected)
                assert m.journal_reverse(lines) == tuple((i, a, -v) for i, a, v in lines)
                assert m.journal_reclassify(lines, 0, 1) == tuple((i, 1, v) for i, a, v in lines)
                # Solve completion by exhaustive possible delta, including zero.
                possible = [x for x in range(-8, 9) if d-c+x == 0]
                assert m.journal_suspense_completion(lines, 15) == ((15, possible[0]) if possible[0] else None)


def test_replay_trial_closing_reconcile_oracles():
    for values in it.product(range(-2, 3), repeat=3):
        balances = tuple(enumerate(values))
        d = tuple((a, b) for a, b in balances if b > 0)
        c = tuple((a, abs(b)) for a, b in balances if b < 0)
        assert m.journal_trial_balance(balances) == (d, c, sum(values))
        for nominal in ((), (0,), (1,), (0, 1)):
            delta = m.journal_close_nominal(balances, nominal, 2)
            expected = tuple((a, -values[a] if a in nominal else sum(values[i] for i in nominal)) for a in sorted(nominal+(2,)))
            assert delta == expected
            assert sum(v for _, v in delta) == 0
        for amount in range(-2, 3):
            lines = ((3, 0, amount), (8, 1, -amount))
            state = list(values)
            for _ in range(abs(amount)):
                state[0] += 1 if amount > 0 else -1
                state[1] -= 1 if amount > 0 else -1
            target = tuple(enumerate(state))
            assert m.journal_post(balances, lines) == target
            assert m.journal_running_balances(balances, (lines, m.journal_reverse(lines))) == (balances, target, balances)
            assert m.journal_reconcile(balances, target) == tuple((a, state[a]-values[a]) for a in range(3) if state[a] != values[a])
    for before in it.product(range(-1, 2), repeat=2):
        for after in it.product(range(-1, 2), repeat=2):
            if sum(before) != sum(after):
                continue
            assert m.journal_reconcile(tuple(enumerate(before)), tuple(enumerate(after))) == tuple((a, after[a]-before[a]) for a in range(2) if after[a] != before[a])


def refuse(fn, args, code):
    saved = copy.deepcopy(args)
    with pytest.raises(ValueError) as error:
        fn(*args)
    assert str(error.value) == 'J489:' + code
    assert args == saved


def test_all_journal_refusals_and_order():
    class I(int): pass
    class T(tuple): pass
    calls = [(m.journal_balance, ()), (m.journal_account_totals, ()), (m.journal_post, (((0, 0),),)), (m.journal_reverse, ()), (m.journal_reclassify, ()), (m.journal_suspense_completion, ())]
    for fn, prefix in calls:
        suffix = (0, 1) if fn is m.journal_reclassify else ((0,) if fn is m.journal_suspense_completion else ())
        for bad, code in [(None, 'type:lines'), ([], 'type:lines'), (T(()), 'type:lines'), ((None,)*33, 'length:lines'), ((None,), 'shape:lines'), (((0, 0),), 'shape:lines'), ((T((0, 0, 0)),), 'shape:lines'), (((True, 0, 0),), 'type:lines:entry'), (((0, 0, I(0)),), 'type:lines:entry'), (((0, 0, float('inf')),), 'type:lines:entry'), (((-1, 0, 0),), 'bound:lines:entry'), (((32, 0, 0),), 'bound:lines:entry'), (((0, -1, 0),), 'bound:lines:entry'), (((0, 16, 0),), 'bound:lines:entry'), (((0, 0, -1001),), 'bound:lines:entry'), (((0, 0, 1001),), 'bound:lines:entry'), (((0, 0, 0), (0, 1, 0)), 'duplicate:lines'), (((-1, 0, 0), (1, True, 0)), 'type:lines:entry')]:
            refuse(fn, prefix+(bad,)+suffix, code)
    for fn, scalar_args, label in ((m.journal_reclassify, (0, 1), 'source'), (m.journal_suspense_completion, (0,), 'suspense')):
        for bad in (True, I(0), 0.0, None):
            refuse(fn, ((), bad)+scalar_args[1:], 'type:'+label)
        for bad in (-1, 16):
            refuse(fn, ((), bad)+scalar_args[1:], 'bound:'+label)
    for bad in (True, I(1), 1.0):
        refuse(m.journal_reclassify, ((), 0, bad), 'type:target')
    for bad in (-1, 16):
        refuse(m.journal_reclassify, ((), 0, bad), 'bound:target')
    refuse(m.journal_reclassify, ((), 0, 0), 'same:account')
    refuse(m.journal_post, (((0, 0),), ((0, 1, 1),)), 'unknown:account')
    refuse(m.journal_post, (((0, 0),), ((0, 0, 1),)), 'unbalanced:lines')


def test_balance_validation_all_routes():
    class I(int): pass
    class T(tuple): pass
    for bad, code in [(None,'type:'),([], 'type:'),(T(()),'type:'),((None,)*17,'length:'),((None,),'shape:'),(((0,),),'shape:'),((T((0,0)),),'shape:'),(((True,0),),'typeentry:'),(((0,I(0)),),'typeentry:'),(((-1,0),),'boundentry:'),(((16,0),),'boundentry:'),(((0,-32001),),'boundentry:'),(((0,32001),),'boundentry:'),(((0,0),(0,0)),'duplicate:'),(((-1,0),(1,True)),'typeentry:')]:
        for fn, build, label in ((m.journal_trial_balance,lambda b:(b,),'balances'),(m.journal_post,lambda b:(b,()),'balances'),(m.journal_close_nominal,lambda b:(b,(),0),'balances'),(m.journal_running_balances,lambda b:(b,()),'balances'),(m.journal_reconcile,lambda b:(b,()),'current'),(m.journal_reconcile,lambda b:((),b),'target')):
            expected = code.replace('typeentry:', 'type:').replace('boundentry:', 'bound:')+label
            if 'entry' in code: expected += ':entry'
            refuse(fn,build(bad),expected)


def test_special_validation_and_precedence():
    b=((0,0),(1,0))
    for bad,code in [(None,'type:nominal'),((None,)*16,'length:nominal'),((True,),'type:nominal:entry'),((-1,),'bound:nominal:entry'),((16,),'bound:nominal:entry'),((0,0),'duplicate:nominal')]:
        refuse(m.journal_close_nominal,(b,bad,1),code)
    refuse(m.journal_close_nominal,(b,(),True),'type:equity')
    refuse(m.journal_close_nominal,(b,(),16),'bound:equity')
    refuse(m.journal_close_nominal,(b,(),-1),'bound:equity')
    refuse(m.journal_close_nominal,(b,(2,),1),'unknown:account')
    refuse(m.journal_close_nominal,(b,(),2),'unknown:account')
    refuse(m.journal_close_nominal,(b,(1,),1),'equity:nominal')
    refuse(m.journal_running_balances,(b,None),'type:journals')
    refuse(m.journal_running_balances,(b,(None,)*9),'length:journals')
    refuse(m.journal_running_balances,(b,(((0,0,1),),None)),'type:lines')
    refuse(m.journal_running_balances,(b,(((0,2,1),),)),'unknown:account')
    refuse(m.journal_running_balances,(b,(((0,0,1),),)),'unbalanced:lines')
    refuse(m.journal_reconcile,(b,((2,1),)),'mismatch:accounts')
    refuse(m.journal_reconcile,(b,((0,1),(1,0))),'mismatch:total')
    refuse(m.journal_close_nominal,(None,None,True),'type:balances')
    refuse(m.journal_reclassify,(((32,0,0),),True,True),'bound:lines:entry')


def test_caps_purity_scope_and_output_types():
    lines=tuple((i,15,1000 if i%2 else -1000) for i in range(32))
    balances=tuple((a,32000 if a%2 else -32000) for a in range(16))
    assert m.journal_balance(lines)==(16000,16000,0)
    assert m.journal_account_totals(lines)==((15,16000,16000,0),)
    assert m.journal_post(balances,lines)==balances
    assert len(m.journal_running_balances(balances,(lines,)*8))==9
    assert len(m.journal_close_nominal(balances,tuple(range(15)),15))==16
    assert m.journal_suspense_completion(tuple((i,0,1000) for i in range(32)),15)==(15,-32000)
    assert m.journal_reconcile(((0,-32000),(1,32000)),((0,32000),(1,-32000)))==((0,64000),(1,-64000))
    assert m.journal_post(((0,32000),(1,-32000)),tuple((i,i%2,1000 if i%2==0 else -1000) for i in range(32)))==((0,48000),(1,-48000))
    args=(balances,lines);saved=copy.deepcopy(args);m.journal_post(*args);assert args==saved
    assert m.SCOPE=='PARTIAL bounded caller-supplied double-entry conservation and replay fixtures'
    assert m.NOT_CLAIMED==('AGI-like intelligence','accounting correctness','financial advice','currency compatibility','production readiness')
    assert m.CLAIMS=={'agi_like_intelligence':False,'production_ready':False,'accounting_correctness':False}
    assert all(type(v) is bool and v is False for v in m.CLAIMS.values())


def test_additional_scalar_endpoints_found_by_constant_mutants():
    assert m.journal_reclassify(((0, 15, 1),), 15, 0) == ((0, 0, 1),)
    assert m.journal_reclassify(((0, 0, -1),), 0, 15) == ((0, 15, -1),)
    assert m.journal_close_nominal(((0, 3), (15, -3)), (15,), 0) == ((0, -3), (15, 3))
    refuse(m.journal_close_nominal, (((0, 0), (15, 0)), (0,), 0), 'equity:nominal')
    assert m.journal_close_nominal(((0, 0),), (), 0) == ((0, 0),)
    assert m.journal_suspense_completion((), 0) is None
