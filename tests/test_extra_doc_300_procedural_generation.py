import pytest
from sugarcode.extra_doc.procedural_generation import generate_maze as solve


def test_explicit_two_by_two_direction_order():
    r=solve(2,2)
    assert r['visit_order']==[(0,0),(1,0),(1,1),(0,1)]
    assert r['passages']==[((0,0),(1,0)),((1,0),(1,1)),((1,1),(0,1))]
    assert solve(2,2,[1,0,2,3])['visit_order']==[(0,0),(0,1),(1,1),(1,0)]
    assert r['difficulty_validated'] is False


def test_independent_union_find_tree_and_grid_invariants():
    for w,h in [(1,1),(1,16),(16,1),(7,5),(16,16)]:
        r=solve(w,h);cells={(x,y) for x in range(w) for y in range(h)};parent={c:c for c in cells}
        def root(c):
            while parent[c]!=c:c=parent[c]
            return c
        assert set(r['visit_order'])==cells and len(r['visit_order'])==w*h
        assert len(r['passages'])==w*h-1 and r['cell_count']==w*h
        for a,b in r['passages']:
            assert a in cells and b in cells and sum(abs(x-y) for x,y in zip(a,b))==1
            assert root(a)!=root(b)
            parent[root(a)]=root(b)
        assert len({root(c) for c in cells})==1

@pytest.mark.parametrize('args,message',[
 ((0,1),'dimensions must be nonbool integers between 1 and 16'),
 ((1,17),'dimensions must be nonbool integers between 1 and 16'),
 ((True,1),'dimensions must be nonbool integers between 1 and 16'),
 ((1,1,None),'directions must contain four direction codes'),
 ((1,1,[0,1,2]),'directions must contain four direction codes'),
 ((1,1,[True,1,2,3]),'directions must be a permutation of nonbool codes zero through three'),
 ((1,1,[0,0,2,3]),'directions must be a permutation of nonbool codes zero through three'),
 ((1,1,[0,1,2,4]),'directions must be a permutation of nonbool codes zero through three'),
])
def test_errors(args,message):
    with pytest.raises(ValueError) as exc:solve(*args)
    assert str(exc.value)==message


def test_reverse_direction_permutation_exercises_all_offsets():
    r=solve(3,3,[2,3,0,1])
    assert r['visit_order']==[(0,0),(1,0),(2,0),(2,1),(1,1),(0,1),(0,2),(1,2),(2,2)]


def test_northward_backfill_default_order():
    assert solve(3,4)['visit_order']==[(0,0),(1,0),(2,0),(2,1),(2,2),(2,3),(1,3),(0,3),(0,2),(1,2),(1,1),(0,1)]
