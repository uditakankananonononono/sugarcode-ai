import itertools
import pytest
from sugarcode.extra_doc.formal_verification599 import verify_reachability as run


def test_cycles_disconnected_bad_and_shortest_lexicographic_witness():
    edges=[('a','c'),('a','b'),('b','d'),('c','e'),('d','a'),('z','z')]
    for order in (edges,list(reversed(edges))):
        assert run('a',order,['d','e','z'])=={'safe_in_model':False,'reachable':['a','b','c','d','e'],'counterexample':['a','b','d']}
    assert run('a',edges,['z'])['safe_in_model'] is True
    assert run('a',edges,['a'])['counterexample']==['a']
    assert run('a',edges,[])['safe_in_model'] is True


def test_independent_fixed_point_oracle_all_small_graphs():
    possibilities=list(itertools.product('abc',repeat=2))
    for mask in range(1,512):
        edges=[pair for i,pair in enumerate(possibilities) if mask>>i&1]
        reachable={'a'}
        for _ in range(3):reachable|={dst for src,dst in edges if src in reachable}
        result=run('a',edges,['c'])
        assert result['reachable']==sorted(reachable)
        assert result['safe_in_model']==('c' not in reachable)
        if result['counterexample'] is not None:
            path=result['counterexample'];assert path[0]=='a' and path[-1]=='c'
            assert all(pair in edges for pair in zip(path,path[1:]))


@pytest.mark.parametrize('bad',[None,True,1,1.0,b'a',[],{}])
def test_start_type(bad):
    with pytest.raises(TypeError,match='^exact string label required$'):run(bad,[('a','b')],[])


@pytest.mark.parametrize('which',[0,1])
@pytest.mark.parametrize('bad',[None,(),True,{}])
def test_outer_types(which,bad):
    args=[[('a','b')],[]];args[which]=bad
    with pytest.raises(TypeError,match='^exact transition and bad-state lists required$'):run('a',*args)


@pytest.mark.parametrize('edges,bad', [([],[]),([None]*65,[]),([('a','b')],[None]*33)])
def test_outer_caps_precede_scan(edges,bad):
    with pytest.raises(ValueError,match='^transition or bad-state count outside cap$'):run('a',edges,bad)


@pytest.mark.parametrize('row',[(),(None,),(None,)*3])
def test_arity(row):
    with pytest.raises(ValueError,match='^transition arity must be two$'):run('a',[row],[])


@pytest.mark.parametrize('slot',range(2))
@pytest.mark.parametrize('bad',[None,True,1,1.0,b'a',[],{}])
def test_transition_slots(slot,bad):
    row=['a','b'];row[slot]=bad
    with pytest.raises(TypeError,match='^exact string label required$'):run('a',[tuple(row)],[])


@pytest.mark.parametrize('bad',[None,True,1,1.0,b'a',[],{}])
def test_bad_state_types(bad):
    with pytest.raises(TypeError,match='^exact string label required$'):run('a',[('a','b')],[bad])


def test_duplicate_and_state_caps():
    with pytest.raises(ValueError,match='^duplicate transition or bad state$'):run('a',[('a','b')]*2,[])
    with pytest.raises(ValueError,match='^duplicate transition or bad state$'):run('a',[('a','b')],['b','b'])
    edges=[('s_'+str(i),'s_'+str(i+1)) for i in range(31)]
    assert len(run('s_0',edges,[])['reachable'])==32
    with pytest.raises(ValueError,match='^state count must be at most32$'):run('s_0',edges+[('s_31','s_32')],[])


def test_bad_state_order_does_not_replace_lexicographic_witness_tie():
    edges=[('a','c'),('a','b'),('b','d'),('c','e')]
    for bad in (['e','d'],['d','e']):
        assert run('a',edges,bad)['counterexample']==['a','b','d']
