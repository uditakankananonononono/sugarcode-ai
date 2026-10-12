"""Bounded genomic integration regressions on supplied sequences and scalars."""
import numpy as np
import pytest
from sugarcode.modules.genomegpt import core as g


def test_short_identity_has_zero_cosine_change():
    assert g.delta_embedding('AAA','AAA')['cosine_change']==0
    assert g.delta_embedding('AAA','AAAA')['cosine_change']==1


def test_per_bin_tracks_condition_expression_without_track_mutation():
    tracks={'atac':[0.1,0.9],'h3k27ac':[0.2,0.8],'methylation':[0.9,0.1]}
    result=g.epigenetic_fusion('ATGC'*50,tracks,bin_size=100)
    assert [b['atac'] for b in result['bins']]==[.1,.9]
    low=g.expression_prediction('ATGC'*50,tracks={'atac':[0,0]},bin_size=100)
    high=g.expression_prediction('ATGC'*50,tracks={'atac':[1,1]},bin_size=100)
    assert high['log2_expression']>low['log2_expression']
    assert tracks['atac']==[.1,.9]


@pytest.mark.parametrize('tracks',[{'atac':[0.1]},{'atac':[0.1,float('nan')]},{'atac':True},{'atac':[0.1,1.1]},{'unknown':.5}])
def test_track_shape_value_and_unknown_key_rejection(tracks):
    with pytest.raises(ValueError):g.epigenetic_fusion('ATGC'*50,tracks,bin_size=100)


def test_cell_contrast_consumes_cell_specific_supplied_tracks():
    r=g.cell_state_contrast('ATGC'*50,cell_types=('a','b'),tracks_by_cell={'a':{'atac':0},'b':{'atac':1}},bin_size=100)
    assert r['highest']=='b' and r['range_log2']>0


def test_edit_result_includes_reference_edited_loops_contacts_insulation():
    motif='CCGCGAGGCGGCAG';rc=motif[::-1].translate(str.maketrans('ACGT','TGCA'))
    seq='AT'*1750+motif+'AT'*1000+rc+'AT'*1500
    r=g.simulate_edit(seq,3500,3501,'A',contact_bin_size=1000)
    change=r['chromatin_comparison']
    assert len(change['reference_loops'])==1 and len(change['edited_loops'])==0
    assert change['lost_loops'] and change['reference_insulation'] and change['edited_insulation']
    assert np.any(np.asarray(change['contact_delta'])!=0)
    assert change['comparison_status']=='same_length_common_bins'
    assert not change['biological_effect_established']


def test_indel_contact_coordinates_not_subtracted_as_if_aligned():
    r=g.simulate_edit('ATGC'*100,10,12,'',contact_bin_size=100)
    assert r['chromatin_comparison']['contact_delta'] is None
    assert r['chromatin_comparison']['comparison_status']=='length_change_not_coordinate_aligned'


def test_profile_constraints_accept_satisfying_edits_and_reject_impossible_ones():
    seq='ATGC'*5
    r=g.propose_expression_profile_edits(seq,{'hepatocyte':0},tolerances={'hepatocyte':1},preserve_cells={'neuron':1},max_candidates=3)
    assert r['edits'] and all(abs(x['per_cell_delta']['neuron'])<=1 for x in r['edits'])
    assert all(x['constraint_satisfied'] for x in r['edits']) and not r['biological_effect_established']
    assert g.propose_expression_profile_edits(seq,{'hepatocyte':100},tolerances={'hepatocyte':0},max_candidates=3)['edits']==[]


def test_profile_search_budget_and_nonfinite_target():
    with pytest.raises(ValueError):g.propose_expression_profile_edits('ATGC'*251,{'generic':0})
    with pytest.raises(ValueError):g.propose_expression_profile_edits('ATGC',{'generic':float('nan')})
    with pytest.raises(ValueError):g.propose_expression_profile_edits('ATGC',{'generic':0},tolerances={'wrong':1})
