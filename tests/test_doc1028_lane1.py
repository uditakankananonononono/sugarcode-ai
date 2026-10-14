from fractions import Fraction
import random
import pytest
from sugarcode.extra_doc.imputation1028 import fill


def test_transposed_independent_column_oracle():
    rng=random.Random(1028)
    for _ in range(100):
        table=[[rng.choice((None,-2,0,3)) for _ in range(5)] for _ in range(8)];before=repr(table)
        columns=[];expected_fill=[]
        for j,col in enumerate(zip(*table)):
            values=[Fraction(x) for x in col if x is not None];mean=sum(values)/len(values) if values else None
            result=[]
            for i,x in enumerate(col):
                value=Fraction(x) if x is not None else mean
                if x is None and mean is not None:expected_fill.append((i,j))
                result.append(None if value is None else (value.numerator,value.denominator))
            columns.append(result)
        got=fill(table)
        assert got['table']==[list(row) for row in zip(*columns)] and got['filled']==sorted(expected_fill)
        assert got['claim']=='PARTIAL' and got['missingness_validated'] is False and repr(table)==before

class L(list):pass
class I(int):pass
@pytest.mark.parametrize('bad,message',[
 (L([[1]]),'table must be an exact list with 1..50 rows'),
 ([], 'table must be an exact list with 1..50 rows'),
 ([L([1])],'rows must be exact lists with 1..20 cells'),
 ([[]],'rows must be exact lists with 1..20 cells'),
 ([[1],[1,2]],'rows must have equal width'),
 *[([[x]],'cells must be None or integers in -1000..1000') for x in (True,I(0),-1001,1001,'')],
])
def test_invalid(bad,message):
    with pytest.raises(ValueError) as exc:fill(bad)
    assert str(exc.value)==message


def test_all_missing_zeros_maxima():
    assert fill([[None,0],[None,None]])['table']==[[None,(0,1)],[None,(0,1)]]
    assert fill([[-1000]*20]*50)['filled']==[]
    assert fill([[1000]])['table']==[[(1000,1)]]
