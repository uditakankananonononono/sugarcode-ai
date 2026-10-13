import pytest
from sugarcode.modules.alpha_fold_ui import hardened as h


def test_refinement_cap_before_backend(monkeypatch):
    monkeypatch.setattr(h.core,'refine_coordinates',lambda *a:(_ for _ in ()).throw(AssertionError('backend reached')))
    with pytest.raises(ValueError,match='refinement limited'):h.safe_refine_coordinates([[0,0,0]]*61)


def test_small_refinement_allowed(monkeypatch):
    monkeypatch.setattr(h.core,'refine_coordinates',lambda *a:{'coordinates':[[0,0,0],[1,0,0]]})
    assert len(h.safe_refine_coordinates([[0,0,0],[1,0,0]])['coordinates'])==2
