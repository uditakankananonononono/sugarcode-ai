import numpy as np
import pytest
from sugarcode.modules.alpha_fold_ui import hardened as m


def test_nonadjacent_pair_energy_closed_form_and_defaults():
    # Only nonadjacent pair0,2 contributes; distance=sigma=>LJ0; .05*q0*q2/r.
    r=m.safe_physical_energy([[0,0,0],[1,0,0],[3.8,0,0]],charges=[1,0,-1])
    assert r['lennard_jones']==pytest.approx(0,abs=1e-12)
    assert r['electrostatic']==pytest.approx(-.05/3.8)
    assert r['total']==pytest.approx(-.05/3.8)
    r=m.safe_physical_energy([[0,0,0],[1,0,0],[7.6,0,0]])
    assert r['lennard_jones']==pytest.approx(4*.1*((.5)**12-(.5)**6))


def test_graph_default8_and_rigid_translation_endpoints():
    r=m.safe_residue_graph([[0,0,0],[7.5,0,0],[8.5,0,0]])
    assert r['edges']==[{'source':0,'target':1,'distance_A':7.5},{'source':1,'target':2,'distance_A':1}]
    x=m.safe_rigid_transform([[1,2,3]],np.eye(3),[1000000,0,0])
    assert np.asarray(x)==pytest.approx(np.array([[1000001,2,3]]))
    with pytest.raises(ValueError):m.safe_rigid_transform([[0,0,0]],np.eye(3),[1000001,0,0])


def test_recursive_tree_all_container_types():
    assert m._tree_ok({'x':[(np.array([1,2]),3)]})
    assert not m._tree_ok({'x':[(np.array([1,float('nan')]),3)]})
    assert not m._tree_ok([{'x':float('inf')}])


def test_numeric_cap_and_coordinate_caps():
    assert m._num('x',10**9,-10**9,10**9)==10**9
    with pytest.raises(ValueError,match='magnitude'):m._num('x',10**9+1,-10**9-1,10**9+1)
    assert m._coords(np.zeros((400,3))).shape==(400,3)
    with pytest.raises(ValueError):m._coords(np.zeros((401,3)))
    assert m._coords([[1000000,0,0]])[0,0]==1000000
    with pytest.raises(ValueError):m._coords([[1000001,0,0]])
    assert m._charges([1000],1).tolist()==[1000]
    with pytest.raises(ValueError):m._charges([1001],1)


def test_refinement_defaults_and_all_admitted_caps_without_backend(monkeypatch):
    seen=[]
    def refine(c,q,steps,lr,restrain,bl,kb):
        seen.append((len(c),steps,lr,restrain,bl,kb));return {'coordinates':c.tolist()}
    monkeypatch.setattr(m.core,'refine_coordinates',refine)
    m.safe_refine_coordinates(np.zeros((2,3)))
    assert seen[-1]==(2,20,.002,True,3.8,10)
    m.safe_refine_coordinates(np.zeros((60,3)),steps=500,learning_rate=.1,bond_length=.5,k_bond=10000)
    assert seen[-1]==(60,500,.1,True,.5,10000)
    m.safe_refine_coordinates(np.zeros((2,3)),steps=1,learning_rate=0,bond_length=20,k_bond=0)
    assert seen[-1]==(2,1,0,True,20,0)
    for kw in [{'steps':501},{'learning_rate':.1001},{'bond_length':20.001},{'k_bond':10001}]:
        with pytest.raises(ValueError):m.safe_refine_coordinates(np.zeros((2,3)),**kw)


def test_energy_graph_validation_upper_and_lower_endpoints(monkeypatch):
    monkeypatch.setattr(m.core,'physical_energy',lambda c,q,s,e:{'sigma':s,'epsilon':e})
    assert m.safe_physical_energy([[0,0,0]],sigma=.001,epsilon=0)=={'sigma':.001,'epsilon':0}
    assert m.safe_physical_energy([[0,0,0]],sigma=100,epsilon=1000000)=={'sigma':100,'epsilon':1000000}
    with pytest.raises(ValueError):m.safe_physical_energy([[0,0,0]],sigma=100.001)
    with pytest.raises(ValueError):m.safe_physical_energy([[0,0,0]],epsilon=1000001)
    monkeypatch.setattr(m.core,'residue_graph',lambda c,k:k)
    assert m.safe_residue_graph([[0,0,0]],cutoff=10000)==10000
    assert m.safe_residue_graph([[0,0,0]],cutoff=0)==0
    with pytest.raises(ValueError):m.safe_residue_graph([[0,0,0]],cutoff=10001)

def test_mutation_sequence_cap_and_cleaned_index(monkeypatch):
    monkeypatch.setattr(m.core,'mutation_stability',lambda s,p,b:(len(s),p,b))
    assert m.safe_mutation_stability('A'*100000,99999,'G')==(100000,99999,'G')
    with pytest.raises(ValueError):m.safe_mutation_stability('A'*100001,0,'G')
    assert m.safe_mutation_stability('A!C',1,'G')==(3,1,'G')
    with pytest.raises(ValueError):m.safe_mutation_stability('A!C',2,'G')


def test_refinement_output_caps_and_finite_arrays(monkeypatch):
    monkeypatch.setattr(m.core,'refine_coordinates',lambda *a:{'coordinates':[[1000000,0,0],[0,0,0]]})
    assert m.safe_refine_coordinates([[0,0,0],[1,0,0]])['coordinates'][0][0]==1000000
    monkeypatch.setattr(m.core,'refine_coordinates',lambda *a:{'coordinates':[[1000001,0,0],[0,0,0]]})
    with pytest.raises(ValueError):m.safe_refine_coordinates([[0,0,0],[1,0,0]])


def test_rotation_both_orthogonality_and_determinant_required():
    with pytest.raises(ValueError):m.safe_rigid_transform([[0,0,0]],np.diag([-1,1,1]),[0,0,0])
    with pytest.raises(ValueError):m.safe_rigid_transform([[0,0,0]],np.diag([2,.5,1]),[0,0,0])

def test_rotation_small_scaling_and_small_reflection_deviation():
    # Scale1.01 retains determinant1.01 but fails both1e-8 checks.
    with pytest.raises(ValueError):m.safe_rigid_transform([[0,0,0]],np.diag([1.01,1,1]),[0,0,0])
    # det1 shear: orthogonality is the only failing check.
    with pytest.raises(ValueError):m.safe_rigid_transform([[0,0,0]],[[1,.01,0],[0,1,0],[0,0,1]],[0,0,0])
    # Each row norm-squared differs8e-9 (passes1e-8 orthogonality),
    # determinant differs about1.2e-8 (fails1e-8 determinant).
    r=np.eye(3)*np.sqrt(1+8e-9)
    assert np.allclose(r@r.T,np.eye(3),rtol=0,atol=1e-8)
    assert not np.isclose(np.linalg.det(r),1,rtol=0,atol=1e-8)
    with pytest.raises(ValueError):m.safe_rigid_transform([[0,0,0]],r,[0,0,0])

def test_refinement61_cap_stops_before_backend(monkeypatch):
    def forbidden(*a,**k):raise AssertionError('oversize reached backend')
    monkeypatch.setattr(m.core,'refine_coordinates',forbidden)
    with pytest.raises(ValueError,match='60 residues'):m.safe_refine_coordinates(np.zeros((61,3)))

def test_public_zero_lower_bounds_and_just_negative(monkeypatch):
    monkeypatch.setattr(m.core,'physical_energy',lambda c,q,s,e:{'epsilon':e,'sigma':s})
    assert m.safe_physical_energy([[0,0,0]],epsilon=0)['epsilon']==0
    with pytest.raises(ValueError):m.safe_physical_energy([[0,0,0]],epsilon=-1e-12)
    assert m.safe_physical_energy([[0,0,0]],sigma=.001)['sigma']==.001
    with pytest.raises(ValueError):m.safe_physical_energy([[0,0,0]],sigma=.000999999999)
    monkeypatch.setattr(m.core,'residue_graph',lambda c,k:k)
    assert m.safe_residue_graph([[0,0,0]],cutoff=0)==0
    with pytest.raises(ValueError):m.safe_residue_graph([[0,0,0]],cutoff=-1e-12)
    monkeypatch.setattr(m.core,'refine_coordinates',lambda c,q,n,lr,rb,bl,kb:{'coordinates':c.tolist(),'args':(n,lr,bl,kb)})
    r=m.safe_refine_coordinates([[0,0,0],[1,0,0]],steps=1,learning_rate=0,bond_length=.5,k_bond=0)
    assert r['args']==(1,0,.5,0)
    for kw in [{'steps':0},{'learning_rate':-1e-12},{'bond_length':.4995},{'k_bond':-1e-12}]:
        with pytest.raises(ValueError):m.safe_refine_coordinates([[0,0,0],[1,0,0]],**kw)

@pytest.mark.parametrize('difference,valid',[(.9e-8,True),(1.1e-8,False)])
def test_orthogonality_tolerance_both_sides(difference,valid):
    # det exactly1; reciprocal diagonal scaling changes row-norm squares
    # by difference and -difference/(1+difference), isolating orthogonality.
    scale=np.sqrt(1+difference);r=np.diag([scale,1/scale,1])
    if valid:assert np.asarray(m.safe_rigid_transform([[0,0,0]],r,[0,0,0])).tolist()==[[0,0,0]]
    else:
        with pytest.raises(ValueError):m.safe_rigid_transform([[0,0,0]],r,[0,0,0])

@pytest.mark.parametrize('difference,valid',[(.9e-8,True),(1.1e-8,False)])
def test_determinant_tolerance_both_sides(difference,valid):
    # Uniform scale cubed=1+difference; row-norm discrepancy about2d/3
    # stays below1e-8, so determinant alone rejects1.1e-8.
    r=np.eye(3)*(1+difference)**(1/3)
    assert np.allclose(r@r.T,np.eye(3),rtol=0,atol=1e-8)
    if valid:assert np.asarray(m.safe_rigid_transform([[0,0,0]],r,[0,0,0])).tolist()==[[0,0,0]]
    else:
        with pytest.raises(ValueError):m.safe_rigid_transform([[0,0,0]],r,[0,0,0])


def test_public_charge_magnitude1000_vs1001(monkeypatch):
    monkeypatch.setattr(m.core,'physical_energy',lambda c,q,s,e:{'charges':q.tolist()})
    assert m.safe_physical_energy([[0,0,0]],charges=[1000])['charges']==[1000]
    with pytest.raises(ValueError):m.safe_physical_energy([[0,0,0]],charges=[1001])

@pytest.mark.parametrize('sequence',[None,[],5,''])
def test_mutation_input_guard_stage(sequence):
    with pytest.raises(ValueError,match='sequence: non-empty'):m.safe_mutation_stability(sequence,0,'A')


def test_mutation_zero_and_empty_cleaned_index(monkeypatch):
    monkeypatch.setattr(m.core,'mutation_stability',lambda s,p,b:p)
    assert m.safe_mutation_stability('AC',0,'G')==0
    with pytest.raises(ValueError,match='position'):m.safe_mutation_stability('!!!',0,'G')
    with pytest.raises(ValueError,match='position'):m.safe_mutation_stability('AC',2,'G')
    with pytest.raises(ValueError,match='mutant'):m.safe_mutation_stability('AC',0,'GG')

@pytest.mark.parametrize('r,t',[(np.zeros((2,3)),[0,0,0]),(np.eye(3),[0,0]),(np.diag([float('nan'),1,1]),[0,0,0])])
def test_rotation_shape_and_finite_guard_stage(r,t):
    with pytest.raises(ValueError,match='rotation must be finite'):m.safe_rigid_transform([[0,0,0]],r,t)


def test_tree_string_metadata_and_nested_nan_refinement(monkeypatch):
    assert m._tree_ok({'metadata':'ok','flag':None})
    monkeypatch.setattr(m.core,'refine_coordinates',lambda *a:{'coordinates':[[0,0,0],[1,0,0]],'energy':float('nan')})
    with pytest.raises(ValueError,match='non-finite'):m.safe_refine_coordinates([[0,0,0],[1,0,0]])

@pytest.mark.parametrize('d,valid',[(.9995e-8,True),(1.0005e-8,False)])
def test_rotation_precision_orthogonality(d,valid):
    scale=np.sqrt(1+d);r=np.diag([scale,1/scale,1])
    if valid:m.safe_rigid_transform([[0,0,0]],r,[0,0,0])
    else:
        with pytest.raises(ValueError):m.safe_rigid_transform([[0,0,0]],r,[0,0,0])

@pytest.mark.parametrize('d,valid',[(.9995e-8,True),(1.0005e-8,False)])
def test_rotation_precision_determinant(d,valid):
    r=np.eye(3)*(1+d)**(1/3)
    assert np.allclose(r@r.T,np.eye(3),rtol=0,atol=1e-8)
    if valid:m.safe_rigid_transform([[0,0,0]],r,[0,0,0])
    else:
        with pytest.raises(ValueError):m.safe_rigid_transform([[0,0,0]],r,[0,0,0])


def test_charge_precision1000point5_refusal():
    with pytest.raises(ValueError):m._charges([1000.5],1)
