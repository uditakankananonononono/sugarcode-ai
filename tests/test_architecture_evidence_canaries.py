import pytest
import numpy as np
from sugarcode.modules.liquid_biopsy.core import reconstruct_tumor_architecture as build
HAP=[[0,1],[1,0]]

def test_unrelated_variant_positions_are_not_rearrangement_evidence():
    result=build([{'id':'a','chrom':'1','position':1},{'id':'b','chrom':'2','position':2}],HAP)
    assert result['structural_rearrangements']==[]
    assert result['rearrangement_status']=='Missing: no supplied split-read or discordant-pair junction evidence'
    assert 'somatic_mutations' not in result
    assert len(result['supplied_variants'])==2

@pytest.mark.parametrize('coverage',[[1,-1],[1,np.nan],[0,0],[[1,2]]])
def test_coverage_cannot_generate_fake_cnv_from_invalid_inputs(coverage):
    with pytest.raises(ValueError): build([],HAP,coverage=coverage)

def test_matched_normal_controls_copy_ratio_instead_of_sample_median():
    result=build([],HAP,coverage=[200,200,100],normal_coverage=[100,100,100])
    assert [x['copy_ratio'] for x in result['copy_number_profile']]==[2,2,1]
    assert result['copy_number_status']=='Matched-normal depth ratios; no purity/ploidy or absolute copy-number inference'

def test_measured_junction_support_not_distance_is_required():
    junction={'left':{'chrom':'1','position':100},'right':{'chrom':'2','position':300},'split_reads':4,'discordant_pairs':3}
    result=build([],HAP,junction_evidence=[junction])
    assert len(result['structural_rearrangements'])==1
    assert result['structural_rearrangements'][0]['support_reads']==7
    assert result['structural_rearrangements'][0]['source']=='supplied junction evidence'
    assert junction=={'left':{'chrom':'1','position':100},'right':{'chrom':'2','position':300},'split_reads':4,'discordant_pairs':3}

@pytest.mark.parametrize('methylation',[[1.5],[-.1],[np.nan]])
def test_methylation_requires_finite_fractions(methylation):
    with pytest.raises(ValueError): build([],HAP,methylation=methylation)
