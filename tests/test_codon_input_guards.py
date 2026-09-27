import pytest
from sugarcode.bio.codon import optimize_sequence
from sugarcode.bio.sequence import translate


@pytest.mark.parametrize('protein', ['MA?K', 'MA K', 'MXX', 'M*', ''])
def test_no_silent_protein_residue_drop(protein):
    with pytest.raises(ValueError, match='20 standard amino acids'):
        optimize_sequence(protein)


@pytest.mark.parametrize('bounds', [(-0.1, .5), (.6, .4), (0, 1.1)])
def test_invalid_gc_bounds_rejected(bounds):
    with pytest.raises(ValueError, match='GC bounds'):
        optimize_sequence('MAK', gc_min=bounds[0], gc_max=bounds[1])


def test_unavoidable_motif_fails_instead_of_claiming_avoidance():
    with pytest.raises(ValueError, match='forbidden motif cannot be removed'):
        optimize_sequence('MAK', avoid_motifs=['ATG'])
    with pytest.raises(ValueError, match='avoid motifs'):
        optimize_sequence('MAK', avoid_motifs=['ATN'])
    clean = optimize_sequence('MAK', avoid_motifs=['GCGGCG'])
    assert translate(clean) == 'MAK'
