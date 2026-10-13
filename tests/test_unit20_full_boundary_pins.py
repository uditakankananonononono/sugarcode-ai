"""Closed-form and boundary checks for held codon mechanics."""
import math
import pytest
from sugarcode.modules.codon_opt import core as m

@pytest.mark.parametrize('args,fragment',[(('', 'ecoli_k12',.4,.6,1),'non-empty'),(('MA','missing',.4,.6,1),'unknown host'),(('MA','ecoli_k12',0,.6,1),'GC bounds'),(('MA','ecoli_k12',.4,.6,0),'positive integer')])
def test_design_refusal(args,fragment):
    with pytest.raises(ValueError,match=fragment):m._validate_design(*args)

def test_named_empty_refusals():
    for fn,args,fragment in [(m.optimize,('MA','missing'),'unknown host'),(m.tasep_simulate,('AA',),'empty coding'),(m.sequence_attention,('AA',),'complete codon'),(m.folding_accessibility,('AAAAA',),'6 nt')]:
        with pytest.raises(ValueError,match=fragment):fn(*args)
    assert len(m.folding_accessibility('AAAAAA')['accessibility'])==6

def test_burden_rounding_and_class_boundaries():
    dna='ATG'*10
    for fraction,cls in [(0.009,'low'),(.01,'moderate'),(.049,'moderate'),(.050001,'high'),(1.5,'high')]:
        flux=10*4*100*1.66e-9/fraction
        r=m.metabolic_load(dna,host_flux_mmol_gdw_h=flux)
        assert r['burden_class']==cls
        assert r['estimated_host_flux_diversion']==round(min(fraction,1),6)
    r=m.metabolic_load('ATG'*100000)
    assert r['estimated_host_flux_diversion']==.00664

def test_folding_long_initiation_mean():
    r=m.folding_accessibility('ATGCGCGCGCGC'*8)
    assert r['initiation_accessibility']==pytest.approx(sum(r['accessibility'][:30])/30)

def test_quality_flags_exact_thresholds(monkeypatch):
    for jam,burden,access,count in [(1,.05,.2,1),(0,.05001,.2,1),(0,.05,.19999,1),(0,.05,.2,0)]:
        monkeypatch.setattr(m,'_design_diagnostics',lambda *a:{'jam_site_count':jam,'host_flux_diversion':burden,'initiation_accessibility':access})
        r=m.design_expression_construct('MA',tasep_steps=3)
        assert len(r['quality_flags'])==count

def test_empty_and_unknown_trna_strain():
    assert m._trna_strain('AA',m.codonlib.ECOLI_K12)==0
    assert m._trna_strain('NNN',{})==pytest.approx(-math.log(1e-6))

def test_sbml_mass_action_parameters_and_translation_stoichiometry():
    import xml.etree.ElementTree as ET
    for strain,expected in [(-1,.1),(0,.1),(1,.05),(3,.025)]:
        xml=ET.fromstring(m._sbml_export('ATG'*7,strain))
        ns={'s':'http://www.sbml.org/sbml/level3/version2/core'}
        p={x.attrib['id']:float(x.attrib['value']) for x in xml.findall('.//s:parameter',ns)}
        assert p=={'k_transcribe':.05,'k_translate':expected,'k_mrna_decay':.01,'k_protein_decay':.005,'trna_strain_index':strain,'construct_nt':21}
        refs=xml.find(".//s:reaction[@id='translation']/s:listOfReactants",ns)
        assert {x.attrib['species']:float(x.attrib['stoichiometry']) for x in refs}=={'SYNTH_mRNA':1,'ATP':28,'AA_POOL':7}

def test_uniform_codons_attention_symmetry_and_folding():
    a=m.sequence_attention('ATG'*4,heads=3)
    for row in a['attention']:assert sum(row)==pytest.approx(1)
    single=m.sequence_attention('ATG',heads=1)
    assert single['attention']==[[1]] and single['context_score']==[1]
    f=m.folding_accessibility('AAAAAA',window=6)
    assert f['local_delta_g_kcal_mol']==[0]*6
    assert f['accessibility']==[.5]*6 and f['initiation_accessibility']==.5
