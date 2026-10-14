import itertools
import pytest
from sugarcode.extra_doc.aggregate_design674 import audit


def test_exhaustive_partition_oracle():
    ids=['a','b','c','d'];rows=[list(c) for size in range(1,5) for c in itertools.combinations(ids,size)]
    for labels in itertools.product(('x','y','z'),repeat=4):
        owners=dict(zip(ids,labels));got=audit(owners,rows)
        groups=[sorted(dict.fromkeys(owners[x] for x in row)) for row in rows]
        assert got['aggregate_sets']==groups
        assert got['cross_boundary']==[i for i,row in enumerate(rows) if any(owners[x]!=owners[row[0]] for x in row)]
        assert got['claim']=='PARTIAL' and got['consistency_validated'] is False

class D(dict):pass
class L(list):pass
class S(str):pass

@pytest.mark.parametrize('owners,rows,message',[
 (D(a='x'),[],'owners must be an exact dict with 1..50 entries'),
 ({},[],'owners must be an exact dict with 1..50 entries'),
 *[({x:'y'},[],'IDs must be nonblank exact strings of 1..80 characters') for x in (S('a'),'\t','\u00a0','\u3000','\u2003','\u0085','x'*81)],
 ({'a':'x'},L(),'transactions must be an exact list with 0..100 entries'),
 ({'a':'x'},[L(['a'])],'transaction must be an exact list with 1..50 entities'),
 ({'a':'x'},[[]],'transaction must be an exact list with 1..50 entities'),
 ({'a':'x'},[['a','a']],'transaction entities must be distinct exact known IDs'),
 ({'a':'x'},[[S('a')]],'transaction entities must be distinct exact known IDs'),
])
def test_invalid(owners,rows,message):
    with pytest.raises(ValueError) as exc:audit(owners,rows)
    assert str(exc.value)==message


def test_maxima_and_zero_width():
    owners={str(i):'x'*80 for i in range(50)};rows=[list(owners)]*100
    assert audit(owners,rows)['cross_boundary']==[]
    assert audit({'\u200b':'\u200b'},[['\u200b']])['aggregate_sets']==[['\u200b']]
