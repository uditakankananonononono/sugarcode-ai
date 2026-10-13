import pytest
import numpy as np
from sugarcode.modules.alpha_fold_ui import hardened as h

@pytest.mark.parametrize('args,message',[(('v','1',0,1),'must be int or float'),(('v',1e10,0,1),'magnitude exceeds cap'),(('v',float('nan'),0,1),'must be finite')])
def test_numeric_guard_stage(args,message):
    with pytest.raises(ValueError,match=message):h._num(*args)

def test_sequence_cap():
    with pytest.raises(ValueError,match='sequence: non-empty str'):h.safe_mutation_stability('A'*100001,0,'C')

def test_translation_cap():
    with pytest.raises(ValueError,match='translation:'):h.safe_rigid_transform([[0,0,0]],np.eye(3),[1e7,0,0])

def test_energy_output_refusal(monkeypatch):
    monkeypatch.setattr(h.core,'physical_energy',lambda *a:{'x':float('nan')})
    with pytest.raises(ValueError,match='non-finite output refused'):h.safe_physical_energy([[0,0,0]])

def test_refinement_size_cap():
    with pytest.raises(ValueError,match='refinement limited'):h.safe_refine_coordinates([[0,0,0]]*61)

def test_refinement_output_refusal(monkeypatch):
    monkeypatch.setattr(h.core,'refine_coordinates',lambda *a:{'coordinates':[[1e7,0,0]]})
    with pytest.raises(ValueError,match='exploded output refused'):h.safe_refine_coordinates([[0,0,0],[1,0,0]])

def test_int_helper_invalid_range():
    with pytest.raises(ValueError,match='must be in'):h._int('v',-1,0,1)

def test_int_helper_valid_range():assert h._int('v',1,0,1)==1

def test_coords_helper_invalid_shape():
    with pytest.raises(ValueError,match='shape'):h._coords([[0,0]])

def test_coords_helper_valid_shape():assert h._coords([[0,0,0]]).shape==(1,3)
