import random
import copy
import pytest
from sugarcode.extra_doc.ethnicity1776 import count_labels
class L(list):pass
class T(tuple):pass
class S(str):pass
BAD=(None,True,1,S('a'),'','\t','\u00a0','\u3000','\u2003','\u0085','x'*81)


def test_independent_label_histogram_oracle():
    rng=random.Random(1776)
    for _ in range(100):
        rows=[(str(i),rng.sample(list('abcd'),rng.randrange(5))) for i in range(20)];freq={}
        for n,ls in rows:
            for x in ls:freq[x]=freq.get(x,0)+1
        assert count_labels(rows)=={'frequencies':sorted(freq.items()),'unlabelled':[n for n,ls in rows if sum(1 for x in ls)==0],'multiple':[n for n,ls in rows if sum(1 for x in ls)>1],'claim':'PARTIAL','ethnicity_inferred':False}

@pytest.mark.parametrize('rows,message',[
 *[(x,'records must be an exact list with 1..100 entries') for x in (None,L([('a',[])]),(('a',[]),),[],[(str(i),[]) for i in range(101)])],
 *[([x],'record must be an id labels tuple') for x in (['a',[]],T(('a',[])),('a',),('a',[],1))],
 *[([(x,[])],'record IDs must be unique valid labels') for x in BAD],
 ([('a',[]),('a',[])],'record IDs must be unique valid labels'),
 *[([('a',x)],'labels must be an exact list of 0..20 unique valid labels') for x in (None,L(),('a',),['a','a'],list(map(str,range(21))),*[[x] for x in BAD])],
])
def test_invalid(rows,message):
    with pytest.raises(ValueError) as exc:count_labels(rows)
    assert str(exc.value)==message


def test_caps_single_empty_and_output_ownership():
    labels=['x'*80,'\u200b']+list(map(str,range(18)));rows=[(str(i),labels[:]) for i in range(100)];before=copy.deepcopy(rows);out=count_labels(rows)
    assert out['frequencies']==[(x,100) for x in sorted(labels)]
    for x in out.values():
        if type(x) is list:x.clear()
    assert rows==before
    assert count_labels([('x'*80,[])])['unlabelled']==['x'*80]
