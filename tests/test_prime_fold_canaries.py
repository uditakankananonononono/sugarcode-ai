import pytest
from sugarcode.modules.prime_design.core import secondary_structure

def test_pegrna_secondary_structure_uses_real_thermodynamic_fold():
    from sugarcode.modules.rna_nussinov import fold_energy
    seq='GGGAAACCC'
    expected=fold_energy(seq)
    result=secondary_structure(seq)
    assert result['dot_bracket']==expected['dot_bracket']=='(((...)))'
    assert result['mfe_kcal_mol']==pytest.approx(expected['mfe_kcal_mol'],abs=.01)
    assert result['paired_fraction']==pytest.approx(6/9)
    assert result['longest_stem']==3
    assert 'ViennaRNA' in result['method']

def test_self_complementarity_cannot_pair_a_base_to_itself():
    result=secondary_structure('GCGCGCGC')
    assert all(j-i>3 for i,j in result['pairs'])
    assert len({n for pair in result['pairs'] for n in pair})==2*len(result['pairs'])
    assert result['status']=='RNA secondary-structure model; penalty is uncalibrated, not editing efficiency'

@pytest.mark.parametrize('seq',['', 'ACNNGT', 'ACXXGT'])
def test_fold_requires_actual_unambiguous_sequence(seq):
    with pytest.raises(ValueError): secondary_structure(seq)
