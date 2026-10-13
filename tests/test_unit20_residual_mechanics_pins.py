import pytest
from sugarcode.modules.codon_opt import core as m

def test_zero_host_flux_uses_positive_floor():
    r=m.metabolic_load('ATG',copies=1,atp_per_aa=1,host_flux_mmol_gdw_h=0)
    assert r['estimated_host_flux_diversion']==1 and r['burden_class']=='high'

def test_zero_codon_adaptiveness_uses_positive_hop_floor(monkeypatch):
    monkeypatch.setattr(m.codonlib,'relative_adaptiveness',lambda t:{'ATG':0})
    assert m.tasep_simulate('ATG',steps=0)['dwell_times_s']==[2]
