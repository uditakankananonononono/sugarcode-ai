from itertools import product
import pytest
from sugarcode.extra_doc.genre_blending import genre_blending


def oracle(genres,conflicts):
    feasible=[]
    for indices in product(*(range(len(x)) for x in genres)):
        words=tuple(genres[i][j][0] for i,j in enumerate(indices))
        if not any(set(pair)<=set(words) for pair in conflicts):
            score=sum(genres[i][j][1] for i,j in enumerate(indices))
            feasible.append((-score,indices,words))
    return min(feasible) if feasible else None


def test_generates_compatible_outline():
    genres=[[('mystery',5),('chase',2)],[('magic',4),('village',1)],[('romance',3),('solitude',0)]]
    conflicts=[('mystery','magic'),('chase','romance')]
    want=oracle(genres,conflicts);r=genre_blending(genres,conflicts)
    assert r['conventions']==list(want[2]) and r['indices']==list(want[1])
    assert r['outline']==[(i,w) for i,w in enumerate(want[2])]
    assert r['certificate']=={'score':-want[0],'conflicts':[],'all_genres_covered':True,'optimal':True}


def test_tie_and_infeasible():
    assert genre_blending([[('a',1),('b',1)],[('c',1)]],[])['indices']==[0,0]
    r=genre_blending([[('a',1)],[('b',1)]],[('a','b')])
    assert r['conventions'] is None and r['certificate']['conflicts']==[('a','b')]
    assert r['certificate']['all_genres_covered'] is False


def test_grid_oracle():
    for a,b,c,d in product(range(3),repeat=4):
        genres=[[('a',a),('b',b)],[('c',c),('d',d)]]
        for conflicts in [[],[('a','c')],[('b','d')],[('a','c'),('b','d')]]:
            want=oracle(genres,conflicts);r=genre_blending(genres,conflicts)
            assert r['conventions']==list(want[2]) and r['certificate']['score']==-want[0]


@pytest.mark.parametrize('genres',[None,(),[],[[('a',1)]],[[('a',1)]]*5,[[] ,[('b',1)]],[[('a',1)]*4,[('b',1)]],[[None],[('b',1)]],[[('',1)],[('b',1)]],[[('a'*21,1)],[('b',1)]],[[('a',True)],[('b',1)]],[[('a',1.)],[('b',1)]],[[('a',11)],[('b',1)]],[[('a',-1)],[('b',1)]]])
def test_genre_refusal(genres):
    with pytest.raises((TypeError,ValueError)):genre_blending(genres,[])


@pytest.mark.parametrize('conflicts',[None,(),[None],[('a',)],[('a','b','c')],[('a',True)],[('a','x')],[('a','a')],[('a','b')]*11])
def test_conflict_refusal(conflicts):
    with pytest.raises((TypeError,ValueError)):genre_blending([[('a',1)],[('b',1)]],conflicts)


def test_caps_preflight_and_duplicate_names():
    class Rows(list):
        def __iter__(self):raise AssertionError('oversized scanned')
    with pytest.raises(ValueError):genre_blending(Rows([None]*5),[])
    with pytest.raises(ValueError):genre_blending([[('a',1),('a',2)],[('b',1)]],[])
    r=genre_blending([[('x'*20,10),('b',0),('c',1)]]*4,[])
    assert r['certificate']['score']==40
