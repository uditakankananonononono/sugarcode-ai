import itertools,pytest
from sugarcode.extra_doc.abstract_feedback2021 import feedback
class Number(int):pass

def oracle(initial,target,gain,steps):
    states=tuple(target+(initial-target)*((1-gain)**i) for i in range(steps+1))
    return {'abstract_feedback_validated':False,'not_claimed':('physical_control','stability','convergence','safety'),'states':states,'pre_update_errors':tuple(target-v for v in states[:-1]),'final_error':target-states[-1],'final_exact':states[-1]==target}

@pytest.mark.parametrize('args',list(itertools.product((-100,-1,0,1,100),(-100,0,100),(0,1,2),(1,2,20))))
def test_closed_form(args):assert feedback(*args)==oracle(*args)

def test_full_singleton():
    assert feedback(0,1,1,1)=={'abstract_feedback_validated':False,'not_claimed':('physical_control','stability','convergence','safety'),'states':(0,1),'pre_update_errors':(1,),'final_error':0,'final_exact':True}

def test_refusals():
    for j,(name,lo,hi) in enumerate((('initial',-100,100),('target',-100,100),('gain',0,2),('steps',1,20))):
        for bad in (lo-1,hi+1,True,False,Number(1),None,1.0,'é',{}, {'extra':0},[1]):
            args=[0,0,0,1];args[j]=bad
            with pytest.raises(ValueError) as e:feedback(*args)
            assert str(e.value)==f'{name}: integer {lo} to {hi} required'

def test_fresh_output():
    a=feedback(0,1,1,1);a['states']=('caller',)
    assert feedback(0,1,1,1)==oracle(0,1,1,1)
