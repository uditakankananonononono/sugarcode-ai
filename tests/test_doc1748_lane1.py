import random
import pytest
from sugarcode.extra_doc.phenomenology1748 import summarize
class L(list):pass
class T(tuple):pass
class S(str):pass
BAD=(None,True,1,S('a'),'','\t','\u00a0','\u3000','\u2003','\u0085','x'*81)


def test_independent_descriptor_frequency_oracle():
    rng=random.Random(1748)
    for _ in range(100):
        rows=[(str(i),rng.sample(list('abcd'),rng.randrange(5))) for i in range(10)]
        frequency={c:sum(c in ds for n,ds in rows) for c in 'abcd'}
        memberships=[(c,sorted(n for n,ds in rows if ds.count(c))) for c in 'abcd' if frequency[c]]
        assert summarize(rows)=={'descriptor_participants':memberships,'universal':[c for c in 'abcd' if frequency[c]==10],'claim':'PARTIAL','experience_validated':False}

@pytest.mark.parametrize('rows,message',[
 *[(x,'descriptions must be an exact list with 1..100 entries') for x in (None,L([('a',[])]),(('a',[]),),[],[(str(i),[]) for i in range(101)])],
 *[([x],'description must be a participant descriptors tuple') for x in (['a',[]],T(('a',[])),('a',),('a',[],1))],
 *[([(x,[])],'participant IDs must be unique valid labels') for x in BAD],
 ([('a',[]),('a',[])],'participant IDs must be unique valid labels'),
 *[([('a',x)],'descriptors must be an exact list of 0..20 unique valid labels') for x in (None,L(),('a',),['a','a'],list(map(str,range(21))),*[[x] for x in BAD])],
])
def test_invalid(rows,message):
    with pytest.raises(ValueError) as exc:summarize(rows)
    assert str(exc.value)==message


def test_caps_universal_empty_and_zero_width():
    codes=['x'*80]+list(map(str,range(19)));got=summarize([(str(i),codes[:]) for i in range(100)])
    assert got['universal']==sorted(codes) and all(len(ns)==100 for c,ns in got['descriptor_participants'])
    assert summarize([('x'*80,['\u200b']),('b',[])])['universal']==[]
