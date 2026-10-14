import random
import pytest
from sugarcode.extra_doc.comparative1736 import compare


def test_independent_feature_frequency_oracle():
    rng=random.Random(1736)
    for _ in range(100):
        rows=[(str(i),rng.sample(list('abcdef'),rng.randrange(7))) for i in range(8)];all_features=sorted({f for n,fs in rows for f in fs});got=compare(rows)
        common=[f for f in all_features if sum(f in fs for n,fs in rows)==len(rows)]
        unique=[(n,sorted(f for f in fs if sum(f in others for name,others in rows)==1)) for n,fs in rows]
        assert got['common']==common and got['unique']==unique and got['claim']=='PARTIAL' and got['research_validated'] is False

class L(list):pass
class T(tuple):pass
class S(str):pass
@pytest.mark.parametrize('rows,message',[
 (L([('a',[]),('b',[])]),'cases must be an exact list with 2..50 entries'),
 ([('a',[])],'cases must be an exact list with 2..50 entries'),
 ([(str(i),[]) for i in range(51)],'cases must be an exact list with 2..50 entries'),
 ([T(('a',[])),('b',[])],'case must be an id features tuple'),
 ([('a',[],1),('b',[])],'case must be an id features tuple'),
 *[([(x,[]),('b',[])],'case IDs must be unique valid labels') for x in (S('a'),'\t','\u00a0','\u3000','\u2003','\u0085','x'*81)],
 *[([('a',x),('b',[])],'features must be an exact list of 0..20 unique valid labels') for x in (L(),list(map(str,range(21))),[S('a')],['a','a'])],
])
def test_invalid(rows,message):
    with pytest.raises(ValueError) as exc:compare(rows)
    assert str(exc.value)==message


def test_caps_identical_empty_labels():
    fs=list(map(str,range(20)));assert compare([(str(i),fs[:]) for i in range(50)])['common']==sorted(fs)
    assert compare([('x'*80,[]),('\u200b',[])])['common']==[]
