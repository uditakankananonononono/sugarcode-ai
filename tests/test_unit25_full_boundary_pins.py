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

def test_cellular_compatibility_closed_form_cases():
    r=m.cellular_compatibility('PESTKENDGNCCCC',compartment='cytosol')
    assert r['degron_count']==3 and r['disulfide_capacity']==0
    assert r['folding_risk']==pytest.approx(.75)
    for compartment in ['ER','secreted']:
        r=m.cellular_compatibility('PESTKENDGNCCCCC',compartment=compartment)
        assert r['disulfide_capacity']==2 and r['folding_risk']==pytest.approx(.45)
    assert m.cellular_compatibility('CC')['folding_risk']==0
    assert m.cellular_compatibility('CCC')['folding_risk']==.3
    assert m.cellular_compatibility('A'*19)['transmembrane_propensity']==1
    assert m.cellular_compatibility('G'+'A'*18+'G')['transmembrane_propensity']==18/19
    assert m.cellular_compatibility('A'*18)['transmembrane_propensity']==18/19

def test_epitope_exact_point33_cutoff():
    r=m.immunogenicity_scan('W'*33+'A'*67,window=100)
    assert r=={'epitopes':[{'start':0,'peptide':'W'*33+'A'*67,'risk':.33}],'max_risk':.33,'burden':.33}

def test_sensitivity_exact_half_and_six_tenths():
    # local HYDRO fractions 2/9 and1 for a G/P centre. Defaults i+-3
    # give seven residues, so construct .5 with active-site .4 + .45*(2/9)
    # is not attainable here. .6 is exactly .45 + .15 in binary64.
    r=m.mutational_scan('AAAPAAA')
    # P isn't HYDRO, local6/7: .45*6/7+.15.
    assert r['positions'][3]['functional_sensitivity']==pytest.approx(.45*6/7+.15)
    r=m.mutational_scan('G',active_positions=[0])
    assert r['positions'][0]['functional_sensitivity']==.55
    assert r['positions'][0]['suggested_class']=='conservative' and r['high_sensitivity']==[]
    r=m.mutational_scan('AAAAA')
    assert all(x['functional_sensitivity']==.45 for x in r['positions'])
    assert r['high_sensitivity']==[]
    r=m.mutational_scan('AAAAGGGGAAAA',[4])
    expected=[.45*sum(a=='A' for a in 'AAAAGGGGAAAA'[max(0,i-3):i+4])/len('AAAAGGGGAAAA'[max(0,i-3):i+4])+.4*(i==4)+.15*(a=='G') for i,a in enumerate('AAAAGGGGAAAA')]
    assert [x['functional_sensitivity'] for x in r['positions']]==pytest.approx(expected)

def test_stability_high_low_thresholds_and_fraction_precision(monkeypatch):
    monkeypatch.setattr(m,'hydrophobicity_profile',lambda *a:[0,2,2])
    assert m._stability('AAA',['H']*3)=={'helix_fraction':1,'strand_fraction':0,'hydrophobic_core_fraction':.667,'folding_dg_estimate':-4.8,'stability_class':'high'}
    monkeypatch.setattr(m,'hydrophobicity_profile',lambda *a:[0])
    assert m._stability('AAA',['C']*3)['stability_class']=='low'
    r=m._stability('AAA',['H','E','C'])
    assert r['helix_fraction']==.333 and r['strand_fraction']==.333 and r['folding_dg_estimate']==-1.87
    assert m._stability('AA',['H','H'])['stability_class']=='low' # exact score .4
    monkeypatch.setattr(m,'hydrophobicity_profile',lambda *a:[0,2])
    assert m._stability('AA',['H','H'])['stability_class']=='moderate' # exact score .55

def test_distinct_codon_triplet_diversity():
    r=m.expression_construct('ACDAC')
    assert r['coding_dna']=='GCGTGCGATGCGTGC'
    assert r['codon_diversity']==.6 and r['gc_fraction']==11/15
    assert r['expression_burden']==pytest.approx(.005+.3*(11/15-.5)+.2)

def test_tm_terminal_window_and_catalytic_temperature_width():
    assert m.cellular_compatibility('G'*5+'A'*19)['transmembrane_propensity']==1
    assert m.cellular_compatibility('A'*19+'G'*5)['transmembrane_propensity']==1
    r=m.enzyme_kinetics('DW',[0,1],temperature_c=54.5,substrate_charge=1)
    assert r['kcat_s']==pytest.approx(10**1.25*math.exp(-.25))

def test_active_coil_tie_both_sides():
    import random
    _,sites,complete=m._design_sequence('CCCHCCCC','HDE',random.Random(0))
    assert sites==[2,4,5] and complete is True

def test_binding_mismatched_hydrophobic_packing():
    r=m.binding_interface('DA',[0,1],ligand_hydrophobic=.9,ligand_charge=0)
    score=.45*.6+.35*.75/math.e
    assert r['packing_complementarity']==pytest.approx(.6)
    assert r['binding_score']==pytest.approx(score)

def test_stability_hydro_window_forwarded(monkeypatch):
    seen=[]
    monkeypatch.setattr(m,'hydrophobicity_profile',lambda s,w:seen.append(w) or [0])
    m._stability('AAA',['C']*3)
    assert seen==[7]

def test_tm_exact19_with_internal_gap_and_terminal_gap():
    for seq in ['A'*9+'G'+'A'*10,'G'+'A'*18+'G']:
        assert m.cellular_compatibility(seq)['transmembrane_propensity']==18/19
    assert m.cellular_compatibility('CC')['folding_risk']==0
    assert m.cellular_compatibility('CCC')['folding_risk']==.3

def test_single_residue_expression_and_cysteine_count():
    r=m.expression_construct('C')
    assert r['coding_dna']=='TGC' and r['codon_diversity']==1 and r['gc_fraction']==2/3
    assert r['expression_burden']==pytest.approx(.001+.3*(2/3-.5)+.1)
    r=m.expression_construct('CC')
    assert r['codon_diversity']==.5 and r['expression_burden']==pytest.approx(.002+.05+.2)
    assert m.expression_construct('W')['expression_burden']==pytest.approx(.051)

def test_stability_exact_core_edge_and_classes(monkeypatch):
    monkeypatch.setattr(m,'hydrophobicity_profile',lambda *a:[1,1.0000001,-1])
    r=m._stability('AAA',['H','E','C'])
    assert r['hydrophobic_core_fraction']==.333
    assert r['folding_dg_estimate']==-2.67 and r['stability_class']=='low'
    monkeypatch.setattr(m,'hydrophobicity_profile',lambda *a:[0])
    assert m._stability('AA',['H','H'])['stability_class']=='low'
    monkeypatch.setattr(m,'hydrophobicity_profile',lambda *a:[2,0])
    assert m._stability('AA',['H','H'])['stability_class']=='moderate'
    monkeypatch.setattr(m,'hydrophobicity_profile',lambda *a:[2])
    assert m._stability('AA',['H','H'])['stability_class']=='high'

def test_odd_length_mid_and_tie_site_residues():
    import random
    seq,sites,complete=m._design_sequence('CCHCC','HDE',random.Random(1))
    assert sites==[0,1,3] and [seq[i] for i in sites]==list('HDE') and complete
    # Empty active residues with coils is behaviorally identical if and -> or:
    # ordered[:0] is empty; no coils with nonempty active is also empty.

@pytest.mark.parametrize('host,dna',[('ecoli','GCGTGCGATGAATTTGGTCATATTAAACTGATGAACCCGCAACGTAGCACCGTTTGGTAT'),('yeast','GCTTGTGACGAGTTCGGACACATCAAGTTGATGAATCCACAGAGATCTACTGTCTGGTAC')])
def test_codon_table_all_amino_acids(host,dna):
    assert m.codon_optimize('ACDEFGHIKLMNPQRSTVWY',host)==dna
    assert m.codon_optimize(' c! ',host)==('TGC' if host=='ecoli' else 'TGT')

def test_single_residue_geometry_and_empty_sites():
    r=m.active_site_geometry('W',[0],substrate_charge=0)
    assert r['hydrophobic_fraction']==1 and r['aromatic_contacts']==1 and r['transition_state_complementarity']==1
    r=m.active_site_geometry('D',[],substrate_charge=0)
    assert r['hydrophobic_fraction']==0 and r['net_charge']==0 and r['transition_state_complementarity']==.5
    # mutational_scan clean_protein guarantees length>=1 and every local
    # slice includes its centre, so max(1,len(local)) -> len(local) equivalent.
    assert m.mutational_scan('A')['positions'][0]['functional_sensitivity']==.45
