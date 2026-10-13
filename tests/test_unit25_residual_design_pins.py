import pytest
from sugarcode.modules.protein_painter import core as m

@pytest.mark.parametrize('description,application',[('bind','therapeutic binder'),('structural','biomaterial')])
def test_selected_template_application(description,application):
    assert m.design_protein(description,length=1,candidates=1)['applications']==application

def test_candidate_rounding_alternate_count_and_site_number(monkeypatch):
    monkeypatch.setattr(m,'_design_sequence',lambda p,a,r:('A'*len(p),[0],True))
    monkeypatch.setattr(m,'chou_fasman',lambda s:['H']+['E']*(len(s)-1))
    monkeypatch.setattr(m,'_stability',lambda *a:{'folding_dg_estimate':-4})
    r=m.design_protein('enzyme',length=7,candidates=5)
    assert r['best']['fold_match']==.143
    assert r['best']['design_score']==.2857
    assert r['best']['active_site_residues']==['A1'] and len(r['alternates'])==3
