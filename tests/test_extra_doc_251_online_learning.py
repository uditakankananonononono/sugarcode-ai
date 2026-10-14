from fractions import Fraction as F
from itertools import product
import pytest
from sugarcode.extra_doc.online_learning import projected_online_gradient as solve


def test_prediction_before_loss_projection_and_regret_oracle():
    gs = [[2, -1], [-1, 3], [0, -2]]
    r = solve(gs, [-1, 0], [2, 2], [0, 1], F(1, 2))
    predictions = [[0, 1], [-1, F(3, 2)], [F(-1, 2), 0]]
    assert [row['prediction'] for row in r['trace']] == predictions
    assert r['final_point'] == [F(-1, 2), 1]
    losses = [sum(a*b for a,b in zip(g,x)) for g,x in zip(gs,predictions)]
    assert [row['loss'] for row in r['trace']] == losses
    vertex_losses = [sum(sum(a*b for a,b in zip(g,x)) for g in gs)
                     for x in product([-1,2],[0,2])]
    assert r['learner_loss'] == sum(losses) == F(9,2)
    assert r['comparator_loss'] == min(vertex_losses) == -1
    assert r['regret'] == F(11,2)
    # Diameter squared 13, gradient energy 19, eta=1/2.
    assert r['regret_bound'] == F(71,4)
    assert r['certificate_valid'] is True


def test_zero_gradient_comparator_tie_and_fixed_box():
    r=solve([[0],[0]],[-2],[3],[1])
    assert r['comparator']==[-2] and r['regret']==0 and r['final_point']==[1]
    r=solve([[2],[-3]],[4],[4],[4],2)
    assert r['regret']==0 and r['regret_bound']==13
    assert [t['round'] for t in r['trace']]==[1,2]


def test_widest_shape_and_scalar_admission():
    assert solve([[0]*8]*256,[0]*8,[2**31]*8,[0]*8)['regret']==0
    assert solve([[F(1,2**31)]],[0],[1],[0])['certificate_valid']

@pytest.mark.parametrize('args,error,message',[
 ((None,[0],[1],[0]),TypeError,'inputs must be lists or tuples'),
 (([[None]*9],[None]*9,[None]*9,[None]*9),ValueError,'dimension count must be between 1 and 8'),
 (([],[0],[1],[0]),ValueError,'round count must be between 1 and 256'),
 (([None]*257,[0],[1],[0]),ValueError,'round count must be between 1 and 256'),
 (([[0]],[0],[1,2],[0]),ValueError,'vector dimensions must agree'),
 (([[0,0]],[0],[1],[0]),ValueError,'gradient dimensions must agree'),
 (([[True]],[0],[1],[0]),TypeError,'values must be nonbool int or Fraction'),
 (([[1.0]],[0],[1],[0]),TypeError,'values must be nonbool int or Fraction'),
 (([[2**32]],[0],[1],[0]),ValueError,'rational values must fit 32 bits'),
 (([[F(1,2**32)]],[0],[1],[0]),ValueError,'rational values must fit 32 bits'),
 (([[0]],[0],[1],[0],0),ValueError,'step_size must be positive'),
 (([[0]],[1],[0],[0]),ValueError,'lower bounds must not exceed upper bounds'),
 (([[0]],[0],[1],[2]),ValueError,'initial point must be inside box'),
])
def test_errors(args,error,message):
    with pytest.raises(error) as exc:solve(*args)
    assert str(exc.value)==message


def test_exact_step_default_and_initial_validation():
    import inspect
    assert inspect.signature(solve).parameters['step_size'].default==1
    for upper,initial,error,message in [([1],[],ValueError,'vector dimensions must agree'),([], [0],ValueError,'vector dimensions must agree'),([1],None,TypeError,'inputs must be lists or tuples')]:
        with pytest.raises(error) as exc:solve([[0]],[0],upper,initial)
        assert str(exc.value)==message

@pytest.mark.parametrize('field',range(5))
def test_exact_boundary_all_numeric_fields(field):
    edge=2**32-1
    args=[[[0]], [0], [edge], [0], 1]
    if field==0:args[0]=[[edge]]
    elif field==1:args[1]=[edge];args[3]=[edge]
    elif field==2:pass
    elif field==3:args[3]=[edge]
    else:args[4]=edge
    assert solve(*args)['certificate_valid'] is True

@pytest.mark.parametrize('value',[F(2**32),F(1,2**32)])
def test_fraction_component_overflow_refused(value):
    with pytest.raises(ValueError) as exc:solve([[value]],[0],[1],[0])
    assert str(exc.value)=='rational values must fit 32 bits'
