"""Closed-form and boundary checks for held protein mechanics."""
import math
import pytest
from sugarcode.modules.protein_painter import core as m

def test_unknown_host_named_refusal():
    with pytest.raises(KeyError,match='unknown host'):m.codon_optimize('MA','missing')

def test_empty_active_residues_do_not_place_sites():
    import random
    seq,sites,complete=m._design_sequence('CCCCC','',random.Random(0))
    assert sites==[] and complete is True and len(seq)==5


def test_unavailable_coils_leave_active_site_incomplete():
    import random
    s,pos,complete=m._design_sequence('HHHH','HDE',random.Random(0))
    assert pos==[] and complete is False and len(s)==4

def test_geometry_and_kinetics_analytical():
    r=m.active_site_geometry('DW',[0,1],substrate_charge=1)
    assert r=={'positions':[0,1],'residues':['D','W'],'net_charge':-1,'hydrophobic_fraction':.5,'aromatic_contacts':1,'transition_state_complementarity':.75}
    k=m.enzyme_kinetics('DW',[0,1],substrate_charge=1,temperature_c=72)
    assert k['kcat_s']==pytest.approx(10**1.25/math.e)
    assert k['km_m']==pytest.approx(.001/.95)
    assert k['catalytic_efficiency_m_inv_s']==pytest.approx(10**1.25/math.e*.95/.001)

def test_compatibility_thresholds_and_binding_analytical():
    assert m.cellular_compatibility('M'+'A'*9)['signal_peptide_proxy'] is True
    assert m.cellular_compatibility('M'+'A'*8)['signal_peptide_proxy'] is False
    r=m.binding_interface('DW',[0,1],ligand_charge=1,ligand_hydrophobic=.5)
    score=.45+.35*.75*math.exp(-2)+.2
    assert r['binding_score']==pytest.approx(score)
    assert r['kd_relative']==pytest.approx(math.exp(-6*score))

def test_active_site_nearest_coil_order_and_shortage():
    import random
    _,sites,complete=m._design_sequence('CCHHHHCC','HDE',random.Random(4))
    assert sites==[1,6,7] and complete is True
    seq,sites,complete=m._design_sequence('HHCHH','HDE',random.Random(4))
    assert sites==[2] and seq[2]=='H' and complete is False

def test_expression_burden_and_diversity_analytical():
    r=m.expression_construct('AC')
    assert r['coding_dna']=='GCGTGC' and r['gc_fraction']==5/6
    assert r['codon_diversity']==1
    assert r['expression_burden']==pytest.approx(.002+.3/3+.1)
    assert m.expression_construct('A'*1000)['expression_burden']==1

def test_mutational_sensitivity_closed_form():
    rows=m.mutational_scan('AGPA',[0])['positions']
    assert [r['functional_sensitivity'] for r in rows]==pytest.approx([.625,.375,.375,.225])
    assert [r['suggested_class'] for r in rows]==['conservative','diversifying','diversifying','diversifying']
    assert m.mutational_scan('AGPA',[0])['high_sensitivity']==[0]

def test_epitope_window_count_and_empty_scan():
    r=m.immunogenicity_scan('WWAA',window=3)
    assert r['epitopes']==[{'start':0,'peptide':'WWA','risk':2/3},{'start':1,'peptide':'WAA','risk':1/3}]
    assert r['max_risk']==2/3 and r['burden']==1
    assert m.immunogenicity_scan('AAAA',window=3)=={'epitopes':[],'max_risk':0,'burden':0}

def test_stability_weighted_score_and_rounding(monkeypatch):
    monkeypatch.setattr(m,'hydrophobicity_profile',lambda *a:[1,1.01,0,2])
    r=m._stability('AAAA',['H','H','E','C'])
    assert r=={'helix_fraction':.5,'strand_fraction':.25,'hydrophobic_core_fraction':.5,'folding_dg_estimate':-3.4,'stability_class':'moderate'}

def test_candidate_defaults_and_ranking_independent_stubs(monkeypatch):
    calls=[]
    def sequence(pattern,active,rng):calls.append(pattern);return 'A'*len(pattern),[],False
    monkeypatch.setattr(m,'_design_sequence',sequence)
    monkeypatch.setattr(m,'chou_fasman',lambda s:['H']*len(s))
    monkeypatch.setattr(m,'_stability',lambda *a:{'folding_dg_estimate':-4})
    r=m.design_protein('enzyme',length=2)
    assert len(calls)==8 and calls==['HH']*8
    assert r['best']['fold_match']==1 and r['best']['design_score']==.8
    assert len(r['alternates'])==3 and r['verification']['fold_verified'] is True
    assert r['applications']=='industrial biocatalyst'
    calls.clear();r=m.design_protein('enzyme',length=1,candidates=1)
    assert len(calls)==1 and r['target_pattern']=='H'
    calls.clear();r=m.design_protein('enzyme',length=10,candidates=1)
    assert r['best']['fold_match']==.5 and r['verification']['fold_verified'] is False

def test_histidine_charge_and_default_binding():
    assert m.active_site_geometry('H',[0])['net_charge']==.1
    g=m.binding_interface('DA',[0,1])
    score=.45+.35*.75/math.e
    assert g['binding_score']==pytest.approx(score)
    assert m.enzyme_kinetics('DW',[0,1])['kcat_s']==pytest.approx(10**(-1+3*.75/math.e))

def test_default_epitope_and_signal_prefix_limits():
    r=m.immunogenicity_scan('W'*10)
    assert len(r['epitopes'])==2 and all(len(x['peptide'])==9 for x in r['epitopes'])
    assert m.cellular_compatibility('M'+'G'*15+'A'*9)['signal_peptide_proxy'] is True
    assert m.cellular_compatibility('M'+'G'*16+'A'*9)['signal_peptide_proxy'] is False
    assert m.cellular_compatibility('M'+'G'*23+'A'*9)['signal_peptide_proxy'] is False
    r=m.cellular_compatibility('CCCCKEN',compartment='ER')
    assert r['disulfide_capacity']==2 and r['degron_count']==1 and r['folding_risk']==.15
