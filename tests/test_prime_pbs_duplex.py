"""Perfect RNA(PBS)/DNA hybrid checks, not prime-edit efficiency validation."""
import math
import pytest
from sugarcode.modules.prime_design import pbs_thermodynamics


def test_hand_summed_acgt_hybrid():
    # RNA AC, CG, GU, UA repeats: Sugimoto 1995 parameters (T denotes U).
    h = 1.9 + 3*(-5.9-16.3-7.8) + 2*(-7.8)
    s = -3.9 + 3*(-12.3-47.1-21.6) + 2*(-23.2)
    r = pbs_thermodynamics('ACGT'*3, salt_mM=1000)
    assert r['delta_h_kcal_mol'] == pytest.approx(h)
    assert r['delta_s_cal_mol_k'] == pytest.approx(s)
    assert r['delta_g_kcal_mol'] == pytest.approx(h-310.15*s/1000)
    assert r['tm_c'] == pytest.approx(1000*h/(s+1.987*math.log(12.5e-9))-273.15)


def test_order_and_rna_direction_matter():
    a = pbs_thermodynamics('AAAACCCCGGGGTTTT')
    b = pbs_thermodynamics('ACGT'*4)
    assert a['delta_g_kcal_mol'] != pytest.approx(b['delta_g_kcal_mol'])
    assert pbs_thermodynamics('A'*12)['delta_g_kcal_mol'] != pytest.approx(pbs_thermodynamics('T'*12)['delta_g_kcal_mol'])


def test_concentration_and_mass_action_half_bound_at_tm():
    low = pbs_thermodynamics('ACGT'*4, strand_concentration_nM=25)
    high = pbs_thermodynamics('ACGT'*4, strand_concentration_nM=2500)
    assert high['tm_c'] > low['tm_c']
    assert high['annealing_probability'] > low['annealing_probability']
    at_tm = pbs_thermodynamics('ACGT'*4, target_temperature_c=low['tm_c'])
    assert at_tm['annealing_probability'] == pytest.approx(.5)
    assert 'not editing efficiency' in low['status']


def test_salt_entropy_and_temperature_consistent():
    a = pbs_thermodynamics('ACGT'*3, salt_mM=50)
    b = pbs_thermodynamics('ACGT'*3, salt_mM=1000)
    assert a['delta_s_cal_mol_k']-b['delta_s_cal_mol_k'] == pytest.approx(.368*11*math.log(.05))
    assert a['tm_c'] < b['tm_c']
    assert a['delta_g_kcal_mol'] > b['delta_g_kcal_mol']
    hot = pbs_thermodynamics('ACGT'*3, target_temperature_c=95)
    assert hot['delta_g_kcal_mol'] > a['delta_g_kcal_mol']
    assert hot['annealing_probability'] < a['annealing_probability']


@pytest.mark.parametrize('seq', ['ACGTACGTN', 'ACGTACGT!', '', None, 'ACGUACGU'])
def test_invalid_sequence_not_silently_cleaned(seq):
    with pytest.raises(ValueError):
        pbs_thermodynamics(seq)


@pytest.mark.parametrize('kwargs', [
    {'salt_mM':float('nan')}, {'salt_mM':float('inf')}, {'salt_mM':0},
    {'salt_mM':True}, {'target_temperature_c':float('nan')},
    {'target_temperature_c':-273.15}, {'target_temperature_c':True},
    {'strand_concentration_nM':0}, {'strand_concentration_nM':float('inf')},
])
def test_invalid_conditions_rejected(kwargs):
    with pytest.raises(ValueError):
        pbs_thermodynamics('ACGT'*3, **kwargs)


def test_extreme_conditions_stable_and_whitespace_normalized():
    assert pbs_thermodynamics(' acgt acgt ') == pbs_thermodynamics('ACGTACGT')
    for temp in (-273.149, 1e6):
        r = pbs_thermodynamics('ACGT'*3, target_temperature_c=temp)
        assert 0 <= r['annealing_probability'] <= 1
        assert all(math.isfinite(r[k]) for k in ('tm_c', 'delta_g_kcal_mol'))
    for length in (7, 26):
        with pytest.raises(ValueError):
            pbs_thermodynamics('A'*length)
