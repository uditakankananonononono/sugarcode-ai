import math
import pytest
from sugarcode.modules.epi_edit import *
SEQ=('ATGC'*120)+'AGG'+('TGACTCA'*50)+'AGG'+('GC'*200)

def test_legacy_landscape_and_nonpermanent_design():
 l=chromatin_landscape(SEQ); r=design_epigenome_edit(SEQ,(400,500),'CRISPRi'); assert l['track'] and r['non_permanent'] and r['mode']=='CRISPRi'

def test_all_declared_histone_marks_have_assignment_paths():
 seq=('CG'*120)+('A'*240)+('TGACTCA'*40)+('GC'*120)
 landscape=chromatin_landscape(seq,(700,900))
 observed={mark for tile in landscape['track'] for mark in tile['marks']}
 assert {'H3K4me3','H3K27ac','H3K27me3','H3K9me3','H3K36me3'} <= observed


def test_effector_activation_and_repression():
 krab=effector_response('KRAB',.8); p300=effector_response('p300',.8); assert krab['relative_expression']<p300['relative_expression'] and krab['state']['methylation']>p300['state']['methylation']

def test_occupancy_is_graded_and_cooperative():
 assert effector_response('VP64',.9)['relative_expression']>effector_response('VP64',.1)['relative_expression']

def test_chromatin_graph_has_contact_edges():
 g=chromatin_graph(chromatin_landscape(SEQ)); assert g['nodes'] and g['edges']

def test_reader_writer_spreads_mark():
 g=chromatin_graph(chromatin_landscape(SEQ)); r=spread_epigenetic_state(g,{0:1},steps=4); assert len(r['trajectory'])==5 and r['spread_distance_tiles']>1

def test_competitive_occupancy_normalized():
 r=competitive_occupancy(1,1,2,1); assert sum(r.values())==pytest.approx(1) and r['endogenous_tf']>r['dcas']

def test_expression_trajectory_dynamic_and_reversible():
 r=expression_trajectory('KRAB',.8,hours=24); assert len(r['time_h'])==145 and r['relative_expression'][0]!=r['relative_expression'][-1] and r['reversible']

def test_cell_state_effect_is_context_specific():
 r=cell_state_effect('p300',.7,{'open':{'accessibility':.8},'closed':{'accessibility':.2}}); assert r['open']['state']['accessibility']>r['closed']['state']['accessibility']

def test_regulatory_offtarget_weights_function():
 h={'cfd_score':.5}; assert regulatory_offtarget(h,.8,essential=True)['regulatory_risk']>regulatory_offtarget(h,.2)['regulatory_risk']

def test_multiplex_spacing_and_occupancy():
 guides=[{'start':0,'composite':.9},{'start':10,'composite':.8},{'start':100,'composite':.7}]; r=multiplex_design(guides,min_spacing=50); assert r['count']==2 and r['selected'][0]['start']==0 and r['combined_occupancy']>.9

def test_diagnostics_honest_finite():
 d=epiedit_diagnostics(SEQ); assert len(d)==23 and all(math.isfinite(v) for v in d.values()) and not any(k.startswith('position_') for k in d)

def test_diagnostics_gene_body_mark_is_reachable():
 d=epiedit_diagnostics(SEQ); explicit=epiedit_diagnostics(SEQ,transcribed_span=(300,700)); assert d['mark_fraction.H3K36me3']>0 and explicit['mark_fraction.H3K36me3']>0

def test_diagnostics_change_with_effector():
 a=epiedit_diagnostics(SEQ,'KRAB',.8); b=epiedit_diagnostics(SEQ,'p300',.8); assert sum(a[k]!=b[k] for k in a)>=4

def test_compiler_complete_and_honest():
 r=compile_epigenome_edit(SEQ,(400,500),'CRISPRa',cell_states={'disease':{'accessibility':.8},'healthy':{'accessibility':.2}}); assert r['effector']=='p300' and r['expression_trajectory'] and r['domain_spread'] and r['cell_states'] and r['multiplex'] and r['validation'] and r['vector_architecture']['status']=='architecture only'
 assert 'no trained model and not clinically validated' in r['model_status']

def test_invalid_effector_rejected():
 with pytest.raises(ValueError): effector_response('MAGIC',.5)
