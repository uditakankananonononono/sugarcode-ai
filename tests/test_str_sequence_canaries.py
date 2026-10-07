import pytest
from sugarcode.modules.str_scope.core import find_strs, reconstruct_repeat_reads, expansion_call

def test_unknown_bases_are_not_homopolymer_alleles():
    assert find_strs('N'*40)==[]

@pytest.mark.parametrize('kwargs', [{'min_unit':0}, {'min_unit':4,'max_unit':2}, {'max_unit':0}, {'min_repeats':0}, {'min_repeats':True}])
def test_str_search_validates_integer_search_domain(kwargs):
    with pytest.raises(ValueError):
        find_strs('CAG'*20,**kwargs)

def test_empty_sequence_has_no_repeat_alleles():
    assert find_strs('')==[]

@pytest.mark.parametrize('sample,ref', [(-1,10),(1.5,10),(True,10),(10,-1)])
def test_expansion_counts_are_nonnegative_integers(sample,ref):
    with pytest.raises(ValueError):
        expansion_call(sample,ref,'CAG')

def test_disease_locus_cannot_be_called_on_wrong_motif():
    with pytest.raises(ValueError):
        expansion_call(45,20,'CGG',locus='HTT')

def test_generic_repeat_delta_is_not_pathogenic_classification():
    result=expansion_call(60,20,'AT')
    assert 'pathogenic' not in result['classification']
    assert result['instability_risk'] is None
    assert result['status']=='Generic repeat-count comparison only; no disease or instability model'

def test_single_molecule_requires_exact_motif_seed_not_every_one_mismatch_chunk():
    result = reconstruct_repeat_reads(['CAA'*20], 'CAG')
    assert result['reads'][0]['repeat_count']==0
    assert result['reads'][0]['purity']==0

def test_single_molecule_trims_mismatch_only_flanks():
    result=reconstruct_repeat_reads(['CAT'+'CAG'*8+'CAA'], 'CAG')
    assert result['reads'][0]['repeat_count']==8
    assert result['reads'][0]['start']==3
    assert result['reads'][0]['interruptions']==[]

def test_unknown_base_inside_tract_is_not_called_biological_interruption():
    result=reconstruct_repeat_reads(['CAG'*5+'CAN'+'CAG'*6], 'CAG')
    assert result['reads'][0]['repeat_count']==6
    assert result['reads'][0]['interruptions']==[]
