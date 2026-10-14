import itertools
import pytest
from sugarcode.extra_doc.mpc591 import sum_shared_values as run


def test_each_party_column_and_modular_reconstruction_oracle():
    for m in (2,7,1000003):
        for n in range(2,9):
            rows=[tuple((j+i)%m for i in range(n)) for j in range(5)]
            expected=[sum(x[i] for x in rows)%m for i in range(n)]
            assert run(m,rows)=={'party_totals':expected,'reconstructed_sum':sum(sum(x) for x in rows)%m,'parties':n,'inputs':5}


@pytest.mark.parametrize('bad',[None,True,1.0,'2',[],{}])
def test_modulus_type(bad):
    with pytest.raises(TypeError,match='^exact nonbool integer required$'):run(bad,[(0,0)])


@pytest.mark.parametrize('bad',[1,1000004])
def test_modulus_cap(bad):
    with pytest.raises(ValueError,match='^integer outside declared range$'):run(bad,[None])


@pytest.mark.parametrize('bad',[None,(),{},True])
def test_outer_type(bad):
    with pytest.raises(TypeError,match='^exact list required$'):run(7,bad)


@pytest.mark.parametrize('n',[0,33])
def test_outer_cap(n):
    with pytest.raises(ValueError,match='^row count must be 1..32$'):run(7,[None]*n)


@pytest.mark.parametrize('bad',[None,[],{},True])
def test_row_type(bad):
    with pytest.raises(TypeError,match='^exact tuple row required$'):run(7,[bad])


@pytest.mark.parametrize('n',[0,1,9])
def test_row_arity(n):
    with pytest.raises(ValueError,match='^share row arity must be 2..8$'):run(7,[(None,)*n])


def test_unequal_arities_before_slots():
    with pytest.raises(ValueError,match='^share row arities must match$'):run(7,[(0,0),(None,)*3])


@pytest.mark.parametrize('slot',range(8))
@pytest.mark.parametrize('bad',[None,True,1.0,'1',[],{}])
def test_each_slot_type(slot,bad):
    row=[0]*8;row[slot]=bad
    with pytest.raises(TypeError,match='^exact nonbool integer required$'):run(7,[tuple(row)])


@pytest.mark.parametrize('slot',range(8))
@pytest.mark.parametrize('bad',[-1,7])
def test_each_slot_cap(slot,bad):
    row=[0]*8;row[slot]=bad
    with pytest.raises(ValueError,match='^integer outside declared range$'):run(7,[tuple(row)])


def test_row_endpoint_permutation_and_no_wrap_loss():
    rows=[(6,6),(1,2)];assert run(7,rows)==run(7,list(reversed(rows)))
    assert run(7,rows)['reconstructed_sum']==1
    assert run(7,[(6,0)]*32)['party_totals']==[3,0]
