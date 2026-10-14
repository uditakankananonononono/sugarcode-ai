import itertools
from fractions import Fraction as F
import pytest
from sugarcode.extra_doc.dynamic_analysis601 import run_checked as run


def test_exact_trace_all_opcodes_and_assertion():
    rows=[('add',3),('sub',1),('mul',5),('div',2),('assert_eq',10)]
    assert run(2,rows)=={'trace':[(0,'add','2','5'),(1,'sub','5','4'),(2,'mul','4','20'),(3,'div','20','10'),(4,'assert_eq','10','10')],'value_fraction':'10','fault':None,'completed':True}


def test_each_runtime_fault_and_first_failure_stops():
    assert run(1,[('div',0),('add',10)])=={'trace':[],'value_fraction':'1','fault':(0,'division_by_zero'),'completed':False}
    assert run(1,[('add',1),('assert_eq',3),('div',0)])=={'trace':[(0,'add','1','2')],'value_fraction':'2','fault':(1,'assertion_failed'),'completed':False}
    assert run(0,[('div',2)])['value_fraction']=='0'
    assert run(1,[('div',3)])['value_fraction']=='1/3'


def test_independent_arithmetic_one_step_oracle():
    for initial,operand in itertools.product((-9,0,7),(-3,1,5)):
        want={'add':F(initial)+operand,'sub':F(initial)-operand,'mul':F(initial)*operand,'div':F(initial,operand)}
        for op,result in want.items():assert run(initial,[(op,operand)])['value_fraction']==str(result)


@pytest.mark.parametrize('bad',[None,True,1.0,'1',[],{}])
def test_initial_type(bad):
    with pytest.raises(TypeError,match='^exact nonbool integer required$'):run(bad,[('add',1)])


@pytest.mark.parametrize('bad',[-1000001,1000001,10**1000])
def test_initial_cap(bad):
    with pytest.raises(ValueError,match='^integer outside declared range$'):run(bad,[None])


@pytest.mark.parametrize('bad',[None,(),{},True])
def test_outer_type(bad):
    with pytest.raises(TypeError,match='^exact instruction list required$'):run(0,bad)


@pytest.mark.parametrize('n',[0,33])
def test_count(n):
    with pytest.raises(ValueError,match='^instruction count must be 1..32$'):run(0,[None]*n)


@pytest.mark.parametrize('bad',[None,[],{},True])
def test_row_type(bad):
    with pytest.raises(TypeError,match='^exact tuple instruction required$'):run(0,[bad])


@pytest.mark.parametrize('n',[0,1,3])
def test_arity(n):
    with pytest.raises(ValueError,match='^instruction arity must be two$'):run(0,[(None,)*n])


@pytest.mark.parametrize('bad',[None,True,1,1.0,[],b'add'])
def test_opcode_type(bad):
    with pytest.raises(TypeError,match='^exact opcode string required$'):run(0,[(bad,1)])


@pytest.mark.parametrize('bad',['','ADD','exec','add '*100])
def test_opcode_enum(bad):
    with pytest.raises(ValueError,match='^unknown opcode$'):run(0,[(bad,1)])


@pytest.mark.parametrize('bad',[None,True,1.0,'1',[],{}])
def test_operand_type(bad):
    with pytest.raises(TypeError,match='^exact nonbool integer required$'):run(0,[('add',bad)])


@pytest.mark.parametrize('bad',[-1000001,1000001])
def test_operand_cap(bad):
    with pytest.raises(ValueError,match='^integer outside declared range$'):run(0,[('add',bad)])


def test_validation_precedes_fault_and_endpoints():
    with pytest.raises(ValueError,match='^unknown opcode$'):run(0,[('div',0),('bad',1)])
    assert run(1000000,[('sub',1000000)])['value_fraction']=='0'
    assert run(-1000000,[('add',-1000000)])['value_fraction']=='-2000000'
    assert run(0,[('add',1)]*32)['value_fraction']=='32'


def test_state_cap_rollback_both_numerator_and_denominator():
    high=run(1,[('mul',1000000)]*32)
    low=run(1,[('div',1000000)]*32)
    assert high['fault']==(12,'state_cap') and high['value_fraction']==str(1000000**12)
    assert low['fault']==(12,'state_cap') and low['value_fraction']==str(F(1,1000000**12))
