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
