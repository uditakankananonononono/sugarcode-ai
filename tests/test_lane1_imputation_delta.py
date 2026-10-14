import pytest
from sugarcode.extra_doc.imputation1028 import fill
from sugarcode.extra_doc.multiple_imputation1029 import pool


def test_imputation_caps_shape_and_all_missing():
    assert len(fill([[0]]*50)['table'])==50
    assert len(fill([[0]*20])['table'][0])==20
    assert fill([[None]])['filled']==[] and fill([[None]])['table']==[[None]]
    for table,message in [([[0]]*51,'table must be an exact list with 1..50 rows'),
                          ([[0]*21],'rows must be exact lists with 1..20 cells'),
                          ([[1,2],[1]],'rows must have equal width')]:
        with pytest.raises(ValueError) as exc:fill(table)
        assert str(exc.value)==message


def test_pool_cap_and_longer_variances():
    assert pool([0]*20,[0]*20)['mean']==(0,1)
    with pytest.raises(ValueError) as exc:pool([0]*21,[0]*21)
    assert str(exc.value)=='estimates must be an exact list with 2..20 entries'
    with pytest.raises(ValueError) as exc:pool([1,2],[1,2,3])
    assert str(exc.value)=='variances must be an exact list matching estimate count'
