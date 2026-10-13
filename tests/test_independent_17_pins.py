import pytest
from sugarcode.modules.deepsplice import hardened as h

@pytest.mark.parametrize('args,message',[(('v',1e10,0,1),'magnitude exceeds cap'),(('v',float('nan'),0,1),'must be finite')])
def test_numeric_guard_stage(args,message):
    with pytest.raises(ValueError,match=message):h._num(*args)

def test_fixed_sequence_length():
    with pytest.raises(ValueError,match='must be 60 nt'):h._seq('x','A',60)

def test_variant_output_refusal(monkeypatch):
    monkeypatch.setattr(h.core,'variant_at',lambda *a:{'x':float('nan')})
    with pytest.raises(ValueError,match='non-finite output refused'):h.safe_variant_at('A',0,'C')

def test_variant_valid_output_accepted(monkeypatch):
    monkeypatch.setattr(h.core,'variant_at',lambda *a:{'x':1})
    assert h.safe_variant_at('A',0,'C')=={'x':1}

def test_exon_output_refusal(monkeypatch):
    monkeypatch.setattr(h,'_stable_logistic',lambda *a:float('nan'))
    with pytest.raises(ValueError,match='output out of range refused'):h.safe_exon_inclusion(0,0,{'exon_definition_support':0})

def test_isoform_output_refusal(monkeypatch):
    monkeypatch.setattr(h.core,'isoform_distribution',lambda *a:{'isoforms':{'a':2}})
    with pytest.raises(ValueError,match='probability distribution'):h.safe_isoform_distribution(.5)

def test_candidate_cap():
    with pytest.raises(ValueError,match='candidates: list'):h.safe_active_learning([{}]*100001)

def test_strategy_cap():
    with pytest.raises(ValueError,match='strategies: list'):h.safe_intervention_simulation(.5,.5,[{}]*100001)
