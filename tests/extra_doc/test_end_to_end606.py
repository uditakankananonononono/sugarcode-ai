import itertools
import pytest
from sugarcode.extra_doc.end_to_end606 import exercise_flow as run


def test_complete_flow_and_hand_trace():
    assert run([('a','add'),('b','add'),('c','pay'),('d','ship')])=={
        'state':'shipped','items':2,'trace':[('a','add','cart','cart',1),('b','add','cart','cart',2),('c','pay','cart','paid',2),('d','ship','paid','shipped',2)],
        'fault':None,'complete_simulated_flow':True}


def test_all_small_sequences_independent_transition_oracle():
    for n in range(1,6):
        for seq in itertools.product(('add','pay','ship'),repeat=n):
            state=0;items=0;bad=None
            for i,op in enumerate(seq):
                if state==0 and op=='add':items+=1
                elif state==0 and op=='pay' and items:state=1
                elif state==1 and op=='ship':state=2
                else:bad=('e_'+str(i),'invalid_transition');break
            result=run([('e_'+str(i),op) for i,op in enumerate(seq)])
            assert result['state']==('cart','paid','shipped')[state]
            assert result['items']==items and result['fault']==bad
            assert result['complete_simulated_flow']==(state==2 and bad is None)


@pytest.mark.parametrize('bad',[None,(),True,{}])
def test_outer_type(bad):
    with pytest.raises(TypeError,match='^exact event list required$'):run(bad)


@pytest.mark.parametrize('n',[0,33])
def test_cap(n):
    with pytest.raises(ValueError,match='^event count must be 1..32$'):run([None]*n)


@pytest.mark.parametrize('bad',[None,[],True,{}])
def test_tuple_type(bad):
    with pytest.raises(TypeError,match='^exact tuple event required$'):run([bad])


@pytest.mark.parametrize('n',[0,1,3])
def test_arity(n):
    with pytest.raises(ValueError,match='^event arity must be two$'):run([(None,)*n])


@pytest.mark.parametrize('slot',range(2))
@pytest.mark.parametrize('bad',[None,True,1,1.0,b'a',[],{}])
def test_slot_types(slot,bad):
    row=['a','add'];row[slot]=bad
    msg='exact event identifier string required' if slot==0 else 'exact action string required'
    with pytest.raises(TypeError,match='^'+msg+'$'):run([tuple(row)])


@pytest.mark.parametrize('bad',['','A','a b','a'*25])
def test_id_caps(bad):
    with pytest.raises(ValueError,match='^bounded lowercase event identifier required$'):run([(bad,'add')])


@pytest.mark.parametrize('bad',['','ADD','unknown','add '*100])
def test_action_enum(bad):
    with pytest.raises(ValueError,match='^unknown flow action$'):run([('a',bad)])


def test_duplicate_validation_precedence_endpoints():
    with pytest.raises(ValueError,match='^duplicate event$'):run([('a','add'),('a','pay')])
    with pytest.raises(ValueError,match='^unknown flow action$'):run([('a','ship'),('b','wrong')])
    assert run([('a'*24,'add')])['items']==1
    assert run([('e_'+str(i),'add') for i in range(32)])['items']==32
