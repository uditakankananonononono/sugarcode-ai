import itertools
import pytest
from sugarcode.extra_doc.property_testing603 import check_sort_properties as run


def test_each_property_independent_and_empty_duplicates():
    rows=[('good',[2,1,1],[1,1,2]),('empty',[],[]),('order',[1,2],[2,1]),
          ('mult',[1,1],[1,2]),('length',[1],[1,1])]
    assert run(rows)=={'cases':[('empty',[]),('good',[]),('length',['length','multiplicity']),('mult',['multiplicity']),('order',['order'])],'failed_cases':3}


def test_exhaustive_tiny_sort_property_oracle():
    for n in range(5):
        for source in itertools.product((-1,0,1),repeat=n):
            correct=sorted(source)
            assert run([('case',list(source),correct)])['failed_cases']==0
            assert run([('case',list(source),correct+[2])])['cases'][0][1]==['length','multiplicity']


@pytest.mark.parametrize('bad',[None,(),True,{}])
def test_outer_type(bad):
    with pytest.raises(TypeError,match='^exact case list required$'):run(bad)


@pytest.mark.parametrize('n',[0,33])
def test_case_cap(n):
    with pytest.raises(ValueError,match='^case count must be 1..32$'):run([None]*n)


@pytest.mark.parametrize('n',[0,2,4])
def test_arity(n):
    with pytest.raises(ValueError,match='^case arity must be three$'):run([(None,)*n])


@pytest.mark.parametrize('bad',[None,True,1,1.0,b'a',[],{}])
def test_identifier_type(bad):
    with pytest.raises(TypeError,match='^exact case identifier string required$'):run([(bad,[],[])])


@pytest.mark.parametrize('slot',[1,2])
@pytest.mark.parametrize('bad',[None,(),True,{},'x'])
def test_list_slot_types(slot,bad):
    row=['case',[],[]];row[slot]=bad
    with pytest.raises(TypeError,match='^exact integer list required$'):run([tuple(row)])


@pytest.mark.parametrize('slot',[1,2])
@pytest.mark.parametrize('bad',[None,True,1.0,'1',[],{}])
def test_list_element_type(slot,bad):
    row=['case',[],[]];row[slot]=[bad]
    with pytest.raises(TypeError,match='^exact nonbool integer required$'):run([tuple(row)])


@pytest.mark.parametrize('slot',[1,2])
def test_list_cap_before_elements(slot):
    row=['case',[],[]];row[slot]=[None]*17
    with pytest.raises(ValueError,match='^integer list cap must be at most16$'):run([tuple(row)])


@pytest.mark.parametrize('slot',[1,2])
@pytest.mark.parametrize('bad',[-1001,1001])
def test_element_cap(slot,bad):
    row=['case',[],[]];row[slot]=[bad]
    with pytest.raises(ValueError,match='^integer outside declared range$'):run([tuple(row)])


def test_duplicates_identifiers_endpoints_and_row_caps():
    with pytest.raises(ValueError,match='^duplicate case$'):run([('a',[],[]),('a',[1],[1])])
    assert run([('a'*24,[-1000,1000],[-1000,1000])])['failed_cases']==0
    assert run([('c_'+str(i),list(range(16)),list(range(16))) for i in range(32)])['failed_cases']==0
    for case in ('','A','a b','a'*25):
        with pytest.raises(ValueError,match='^bounded lowercase case identifier required$'):run([(case,[],[])])


@pytest.mark.parametrize('row',[['case',[],[]],None,True,{},'case',1,set()])
def test_exact_tuple_case_boundary(row):
    with pytest.raises(TypeError,match='^exact tuple case required$'):
        run([row])
