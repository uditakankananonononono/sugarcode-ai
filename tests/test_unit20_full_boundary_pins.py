"""Closed-form and boundary checks for held codon mechanics."""
import math
import numpy as np
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

def test_custom_trna_average_and_dwell(monkeypatch):
    monkeypatch.setattr(m.codonlib,'relative_adaptiveness',lambda table:{'ATG':.125,'GCT':.5})
    assert m._trna_strain('ATGGCT',{})==pytest.approx((-math.log(.125)-math.log(.5))/2)
    r=m.tasep_simulate('ATGGCTAAA',steps=0)
    assert r['dwell_times_s']==[.8,.2,2]
    assert r['output_rate_per_s']==0 and r['mean_density']==0
    assert r['density_profile']==[0,0,0] and r['jam_sites']==[]
    r=m.tasep_simulate('ATGGCT',steps=10,ribosome_init_rate=0)
    assert r['sim_time_s']==0 and r['proteins_completed']==0

def test_design_default_arguments_are_forwarded(monkeypatch):
    calls={}
    def flow(dna,table=None,ribosome_init_rate=2,steps=4000):
        calls['steps']=steps;return {}
    def load(dna,host_flux_mmol_gdw_h=10,copies=100,atp_per_aa=4):
        calls['copies']=copies;return {}
    def evo(dna,trials=200,seed=7):
        calls['seed']=seed;return {}
    monkeypatch.setattr(m,'tasep_simulate',flow);monkeypatch.setattr(m,'metabolic_load',load);monkeypatch.setattr(m,'evolutionary_robustness',evo)
    monkeypatch.setattr(m,'_design_diagnostics',lambda *a:{'jam_site_count':0,'host_flux_diversion':0,'initiation_accessibility':1})
    m.design_expression_construct('MA')
    assert calls=={'steps':2000,'copies':100,'seed':7}

@pytest.mark.parametrize('lo,hi',[(.5,.5),(.5,1),(0,.5)])
def test_gc_equal_and_upper_end_refusal(lo,hi):
    with pytest.raises(ValueError,match='GC bounds'):m._validate_design('MA','ecoli_k12',lo,hi,1)

def test_context_attention_two_codons_closed_form():
    # ATG is (1/3,1/3,1/3,0), CCC is (0,0,0,1).
    vectors=[np.array([1/3,1/3,1/3,0,0,1]),np.array([0,0,0,1,math.sin(.1),math.cos(.1)])]
    dot=np.array([[float(x@y)/math.sqrt(6) for y in vectors] for x in vectors])
    expected=[[1/(1+math.exp(row[1]-row[0])),1/(1+math.exp(row[0]-row[1]))] for row in dot]
    assert np.array(m.sequence_attention('ATGCCC')['attention'])==pytest.approx(np.array(expected))

def test_gc_folding_pair_energy_closed_form():
    r=m.folding_accessibility('GCGCGC',window=6)
    assert r['local_delta_g_kcal_mol']==pytest.approx([-2.1,-3.1,-2.1,-3.6,-2.1,-3.1])
    assert r['accessibility']==pytest.approx([1/(1+math.exp(-e)) for e in r['local_delta_g_kcal_mol']])

def test_tasep_four_events_exact_single_site(monkeypatch):
    class Rng:
        choices=iter([0,1,0,1])
        def exponential(self,scale):return scale
        def choice(self,n,p):return next(self.choices)
    monkeypatch.setattr(m.np.random,'default_rng',lambda seed:Rng())
    monkeypatch.setattr(m.codonlib,'relative_adaptiveness',lambda table:{'ATG':.5})
    r=m.tasep_simulate('ATG',ribosome_init_rate=2,steps=4)
    # initiation .5s, exit .2s, repeated; burn-in excludes step0.
    assert r['sim_time_s']==1.4 and r['proteins_completed']==2
    assert r['density_profile']==[.333] and r['mean_density']==.3333
    assert r['output_rate_per_s']==1.4286

def test_mutation_landscape_three_defined_events(monkeypatch):
    class Rng:
        positions=iter([2,0,0]);bases=iter(['C','T','C'])
        def integers(self,n):return next(self.positions)
        def choice(self,choices):
            x=next(self.bases);assert x in choices;return x
    monkeypatch.setattr(m.np.random,'default_rng',lambda seed:Rng())
    # GAA -> GAC nonsynonymous; GAA -> TAA stop; GAA -> CAA nonsynonymous.
    r=m.evolutionary_robustness('GAA',trials=3)
    assert r['synonymous_fraction']==0 and r['stop_gain_fraction']==1/3
    assert r['mean_mutation_effect']==pytest.approx(-1.6/3)
    assert r['homopolymer_risk']==0 and r['trials']==3 and r['seed']==7

def test_synthetic_construct_diagnostics_closed_form(monkeypatch):
    dna='ATGGCTGAGACCGCGCGCGAATTCGGATCC'
    codons=[dna[i:i+3] for i in range(0,len(dna),3)]
    monkeypatch.setattr(m.codonlib,'relative_adaptiveness',lambda table:{c:v for c,v in zip(codons,[.1,.2,.8,.9,1,.3,.4,.5,.6,.7])})
    monkeypatch.setattr(m.codonlib,'cai',lambda *a:.75)
    flow={'dwell_times_s':[1,2,3,4,5,6,7,8,9,10],'density_profile':[.6,.7,.8,0,0,0,0,0,0,0],'output_rate_per_s':2,'mean_density':.21,'jam_sites':[2]}
    load={'atp_molecules_per_cell_per_cycle':800,'estimated_host_flux_diversion':.25}
    fold={'accessibility':[.1,.2,.3]*10,'initiation_accessibility':.2}
    evo={'synonymous_fraction':.5,'stop_gain_fraction':.1,'mean_mutation_effect':-.4,'homopolymer_risk':2}
    attention={'context_score':[.1,.2,.3,.4,.5,.6,.7,.8,.9,1]}
    r=m._design_diagnostics(dna,flow,load,fold,evo,attention,{},2)
    assert len(r)==51
    assert r['rare_codon_fraction']==.1 and r['optimal_codon_fraction']==.2
    assert r['codon_diversity']==10 and r['codon_entropy']==pytest.approx(-math.log(.1+1e-12))
    assert r['CpG_fraction']==dna.count('CG')/30
    assert r['restriction_BsaI_count']==1 and r['restriction_EcoRI_count']==1 and r['restriction_BamHI_count']==1
    assert r['repeat_GC_count']==1
    assert r['mean_dwell_s']==5.5 and r['max_dwell_s']==10
    assert r['dwell_CV']==pytest.approx(math.sqrt(8.25)/5.5)
    assert r['queue_fraction']==.2 and r['ribosome_peak_density']==.8
    assert r['structured_fraction']==1/3 and r['minimum_mRNA_accessibility']==.1
    assert r['attention_peak']==1 and r['attention_mean']==pytest.approx(.55)
    assert r['translation_time_s']==55 and r['proteins_per_hour']==7200 and r['ATP_per_protein']==40
    assert r['resource_efficiency']==1.6 and r['design_score']==pytest.approx(.06)
    assert r['bottleneck_codon_index']==9 and r['bottleneck_codon']=='TCC'
    assert r['synthesis_complexity_score']==pytest.approx(2.2)
    assert r['start_codon_valid'] is True and r['internal_stop_count']==0

def test_exact_burden_boundary_and_display_digits():
    # copies=3, ATP/aa=2; 3 aa => 18 molecules. Choosing the binary64
    # denominator one adjacent step above/below the division boundary tests it.
    cost=18*1.66e-9
    flux=cost/.05
    while cost/flux<.05:flux=math.nextafter(flux,0)
    while cost/flux>.05:flux=math.nextafter(flux,math.inf)
    assert cost/flux==.05
    r=m.metabolic_load('ATG'*3,copies=3,atp_per_aa=2,host_flux_mmol_gdw_h=flux)
    assert r['burden_class']=='high' and repr(r['estimated_host_flux_diversion'])=='0.05'
    r=m.metabolic_load('ATG'*3,copies=3,atp_per_aa=2,host_flux_mmol_gdw_h=cost/.0499)
    assert r['burden_class']=='moderate' and repr(r['estimated_host_flux_diversion'])=='0.0499'
    assert r['fba_constraint_row']['stoichiometry']=={'ATP':-6,'AA_POOL':-3}
    assert repr(r['fba_constraint_row']['upper_bound'])=='3e-08'
    r=m.metabolic_load('ATG'*101,copies=3,atp_per_aa=2,host_flux_mmol_gdw_h=.01)
    assert repr(r['estimated_host_flux_diversion'])=='0.000101'
    assert repr(r['fba_constraint_row']['upper_bound'])=='1.006e-06'

def test_partial_codon_sbml_and_odd_folding_window():
    import xml.etree.ElementTree as ET
    root=ET.fromstring(m._sbml_export('ATGGC',2))
    ns={'s':'http://www.sbml.org/sbml/level3/version2/core'}
    p={x.attrib['id']:x.attrib['value'] for x in root.findall('.//s:parameter',ns)}
    assert p['k_translate']=='0.033333' and p['construct_nt']=='5'
    refs=root.find(".//s:reaction[@id='translation']/s:listOfReactants",ns)
    assert {x.attrib['species']:x.attrib['stoichiometry'] for x in refs}=={'SYNTH_mRNA':'1','ATP':'4','AA_POOL':'1'}
    for window in [2,3]:
        r=m.folding_accessibility('AGCTAG',window=window)
        assert r['local_delta_g_kcal_mol']==pytest.approx([0,-1.05,-2.6,-1.05,-.5,-1.05])

def test_design_positive_copy_one():
    assert m._validate_design(' MA ','ecoli_k12',.4,.6,1)=='MA'

def test_declared_defaults_forward_or_report(monkeypatch):
    class Stop(Exception):pass
    seen={}
    class Rng:
        def exponential(self,scale):seen['scale']=scale;raise Stop
    monkeypatch.setattr(m.np.random,'default_rng',lambda seed:Rng())
    with pytest.raises(Stop):m.tasep_simulate('ATG')
    assert seen['scale']==.5
    monkeypatch.setattr(m.np.random,'default_rng',lambda seed:np.random.RandomState(seed))
    assert m.sequence_attention('ATG')['heads']==4

def test_two_site_tasep_four_events(monkeypatch):
    class Rng:
        choices=iter([0,1,2,0])
        def exponential(self,scale):return scale
        def choice(self,n,p):return next(self.choices)
    monkeypatch.setattr(m.np.random,'default_rng',lambda seed:Rng())
    monkeypatch.setattr(m.codonlib,'relative_adaptiveness',lambda table:{'ATG':.5,'GCT':.25})
    r=m.tasep_simulate('ATGGCT',ribosome_init_rate=2,steps=4)
    assert r['proteins_completed']==1
    assert r['sim_time_s']==1.42
    assert r['density_profile']==[.333,.333] and r['mean_density']==.3333


def test_synonymous_landscape_and_default_trial_count(monkeypatch):
    class Rng:
        def integers(self,n):return 2
        def choice(self,choices):return 'C'
    monkeypatch.setattr(m.np.random,'default_rng',lambda seed:Rng())
    r=m.evolutionary_robustness('GCT')
    assert r['trials']==200 and r['synonymous_fraction']==1 and r['mean_mutation_effect']==0

def test_optimize_closed_form_stubbed_cost_and_rounding(monkeypatch):
    monkeypatch.setattr(m.codonlib,'optimize_sequence',lambda *a:'ATGGCT')
    monkeypatch.setattr(m,'tasep_simulate',lambda *a,**kw:{})
    monkeypatch.setattr(m,'_trna_strain',lambda *a:.123456)
    monkeypatch.setattr(m,'gc_content',lambda dna:.543216)
    monkeypatch.setattr(m,'gc_windows',lambda dna,window:[(0,.543216)])
    values=iter([.812345,.792345,.654321])
    monkeypatch.setattr(m.codonlib,'cai',lambda *a:next(values))
    r=m.optimize('MA')
    assert r['cai_gc_repair_cost']==.02 and r['gc_repair_note'] is None
    assert r['cai_before']==.6543 and r['cai_after']==.7923 and r['chi_score']==.1235
    assert r['gc_content']==.5432 and r['gc_windows']==[{'start':0,'gc':.543}]


def test_strain_floor_and_nontrivial_dwell_rounding(monkeypatch):
    monkeypatch.setattr(m.codonlib,'relative_adaptiveness',lambda table:{'ATG':0,'GCT':.3})
    assert m._trna_strain('ATG',{})==pytest.approx(-math.log(1e-6))
    assert m.tasep_simulate('GCT',steps=0)['dwell_times_s']==[.3333]
