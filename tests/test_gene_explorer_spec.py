import math
import pytest
from sugarcode.modules.gene_explorer import *
SEQ='ATG'+'GCT'*30+'TAA'+'CCC'*10

def test_legacy_central_dogma_and_report():
 r=explore(SEQ,'demo'); assert r['mrna']['sequence'].startswith('AUG') and r['protein']['sequence']=='M'+'A'*30 and len(r['animation_script'])==5 and 'Longest ORF' in central_dogma_report(SEQ,'demo')

def test_information_graph_directionality():
 g=information_graph(SEQ,['i1'],['v1'],['P']); assert len(g['nodes'])==6 and {'transcription','translation','splicing','perturbs','interacts'}=={e['relation'] for e in g['edges']}

def test_transcript_processing_splices_introns():
 r=transcript_processing(['ATG','GCT'],['AAAA']); assert r['pre_mrna_length']==10 and r['mature_mrna']=='AUGGCU' and r['export_probability']>.9

def test_isoform_expression_normalized():
 r=isoform_expression({'a':2,'b':1},{'b':2}); assert sum(r['fractions'].values())==pytest.approx(1) and r['fractions']['a']==r['fractions']['b']

def test_variant_cascade_propagates():
 r=variant_cascade(SEQ,4,'T',.9,True,.3); assert r['ddg_kcal_mol']>0 and r['expression_ratio']<1 and r['phenotype_effect']>0

def test_conformational_populations_normalized():
 r=conformational_states('MAAAA',2); assert sum(r['populations'].values())==pytest.approx(1)

def test_pathway_dynamic_and_drug_sensitive():
 a=pathway_simulation(drug=0); b=pathway_simulation(drug=.8); assert len(a['time_h'])==121 and a['signal'][-1]>b['signal'][-1]

def test_variant_posterior_attributions_interval():
 r=probabilistic_variant(.9,3,.6,.5,.8); assert sum(r['attributions'].values())==pytest.approx(1) and r['conformal_interval'][0]<=r['pathogenic_probability']<=r['conformal_interval'][1]

def test_diagnostics_honest_finite():
 d=central_dogma_diagnostics(SEQ); assert len(d)==13 and all(math.isfinite(v) for v in d.values())

def test_diagnostics_change_with_sequence():
 a=central_dogma_diagnostics(SEQ); b=central_dogma_diagnostics('ATG'+'AAA'*10+'TAA'); assert sum(a[k]!=b[k] for k in a)>=7

def test_digital_explorer_complete_honest():
 r=digital_gene_explorer(SEQ,'demo',[{'position':4,'alt':'T'}],{'drug':.2}); assert r['trace'] and r['information_graph'] and r['transcript_processing'] and r['conformational_states'] and r['variant_cascades'] and r['pathway'] and r['diagnostics']
 assert 'no trained model and not clinically validated' in r['model_status']

def test_invalid_isoform_rejected():
 with pytest.raises(ValueError): isoform_expression({'a':0})
