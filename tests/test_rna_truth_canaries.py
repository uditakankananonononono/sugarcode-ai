"""Behavior canaries for the Oct 7 overclaim pass. No fabricated model outputs."""
import math
import pytest
from sugarcode.modules.rna_decoder import core as r

RNA = 'GGACTAAAACGTTTTGATCAGACT'

def test_untrained_motif_scores_are_not_probabilities():
    sites = r.predict_m6a(RNA, threshold=0)
    assert sites and all('m6a_probability' not in x for x in sites)
    assert all(x['trained'] is False and 'heuristic_score' in x for x in sites)

def test_no_fabricated_mrna_effect_sizes():
    effects = r.optimize_mrna(RNA)['predicted_effect']
    assert effects['translation_efficiency'] is None
    assert effects['half_life'] is None

def test_nanopore_deviation_not_modification_probability():
    result = r.nanopore_modification([3.], [0.])
    assert 'modification_probability' not in result
    assert result['z_scores'] == pytest.approx([15.])

@pytest.mark.parametrize('signal,expected,sd', [([], [], .2), ([1,2], [1], .2), ([math.nan], [1], .2), ([1],[1],0)])
def test_nanopore_rejects_invalid_inputs(signal, expected, sd):
    with pytest.raises(ValueError):
        r.nanopore_modification(signal, expected, sd)

def test_structure_is_actual_pairing_not_palindrome_or_fake_energy():
    result = r.structure_ensemble('GGGAAACCC', window=9)
    assert result['method'] == 'ViennaRNA Turner 2004 partition-function ensemble'
    w = result['windows'][0]
    assert w['pairs'] and w['dot_bracket'] == '(((...)))'
    assert w['mfe_kcal_mol'] < 0 and 'folding_dg_proxy' not in w
    assert 0 < w['pair_probabilities'][0]['probability'] <= 1

def test_empty_structure_does_not_divide_by_zero():
    assert r.structure_ensemble('')['windows'] == []

def test_kinetics_zero_rates_is_constant_not_division_by_zero():
    assert r.modification_kinetics(initial=.3, writer=0, eraser=0)['occupancy'] == pytest.approx([.3]*121)

@pytest.mark.parametrize('kwargs', [{'initial':2}, {'writer':-1}, {'hours':-1}])
def test_kinetics_rejects_nonphysical_inputs(kwargs):
    with pytest.raises(ValueError):
        r.modification_kinetics(**kwargs)

def test_functional_impact_does_not_fabricate_effects_from_motif_counts():
    impact = r.functional_impact(RNA, {'psi':[1,2], 'm6A':[3]})
    assert impact['translation_efficiency_relative'] is None
    assert impact['immune_activation_relative'] is None
    assert impact['stability_relative'] is None

def test_no_gc_derived_encapsulation_prediction():
    assert r.design_rna(RNA)['delivery']['encapsulation_proxy'] is None

def test_cds_bounds_are_validated():
    with pytest.raises(ValueError):
        r.predict_m6a(RNA, cds_start=20, cds_end=3)


def test_structure_reports_cross_window_pairs_in_full_sequence_mode():
    result = r.structure_ensemble('GGGAAACCC', window=None)
    assert result['windows'][0]['pairs'] == [[0,8], [1,7], [2,6]]

@pytest.mark.parametrize('seq,window', [('ACX',20), ('ACGU',0), ('ACGU',-1)])
def test_structure_rejects_bad_sequence_and_window(seq, window):
    with pytest.raises(ValueError):
        r.structure_ensemble(seq, window=window)
