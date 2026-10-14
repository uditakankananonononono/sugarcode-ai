import random
import pytest
from sugarcode.extra_doc.poststructural1752 import compare_readings
class L(list):pass
class T(tuple):pass
class S(str):pass
BAD=(None,True,1,S('a'),'','\t','\u00a0','\u3000','\u2003','\u0085','x'*81)


def test_independent_term_reading_matrix_oracle():
    rng=random.Random(1752)
    for _ in range(100):
        rows=[(str(i),[(t,rng.choice('xyz')) for t in 'abcd' if rng.randrange(2)]) for i in range(8)]
        matrix={n:dict(aa) for n,aa in rows};disagreements=[];missing=[]
        for t in 'abcd':
            present=[(n,d[t]) for n,d in matrix.items() if t in d];absent=[n for n,d in matrix.items() if t not in d]
            if not present:continue
            if any(m!=present[0][1] for n,m in present):disagreements.append((t,present))
            if absent:missing.append((t,absent))
        assert compare_readings(rows)=={'disagreements':disagreements,'missing':missing,'claim':'PARTIAL','interpretation_validated':False}

@pytest.mark.parametrize('rows,message',[
 *[(x,'readings must be an exact list with 2..20 entries') for x in (None,L([('a',[]),('b',[])]),(('a',[]),('b',[])),[('a',[])],[(str(i),[]) for i in range(21)])],
 *[([x,('b',[])],'reading must be an id assignments tuple') for x in (['a',[]],T(('a',[])),('a',),('a',[],1))],
 *[([(x,[]),('b',[])],'reading IDs must be unique valid labels') for x in BAD],
 ([('a',[]),('a',[])],'reading IDs must be unique valid labels'),
 *[([('a',x),('b',[])],'assignments must be an exact list with 0..100 entries') for x in (None,L(),(),[(str(i),'m') for i in range(101)])],
 *[([('a',[x]),('b',[])],'assignment must be a term meaning tuple') for x in (['t','m'],T(('t','m')),('t',),('t','m',1))],
 *[([('a',[(x,'m')]),('b',[])],'assignment labels must be valid with unique terms') for x in BAD],
 *[([('a',[('t',x)]),('b',[])],'assignment labels must be valid with unique terms') for x in BAD],
 ([('a',[('t','m'),('t','n')]),('b',[])],'assignment labels must be valid with unique terms'),
])
def test_invalid(rows,message):
    with pytest.raises(ValueError) as exc:compare_readings(rows)
    assert str(exc.value)==message


def test_caps_empty_identical_and_zero_width():
    pairs=[('x'*80,'y'*80)]+[(str(i),'m') for i in range(99)]
    assert compare_readings([(str(i),pairs[:]) for i in range(20)])['missing']==[]
    assert compare_readings([('x'*80,[('\u200b','m')]),('b',[('\u200b','m')])])['disagreements']==[]
    assert compare_readings([('a',[]),('b',[])])['missing']==[]
