"""Real-data/curation validation for micro_tx (module 105).

BUG 74: SCFA_YIELD credited butyrate to Bifidobacterium (.10), Akkermansia
(.15) and L. reuteri (.10) - none produce butyrate. Bifidobacterium makes
acetate + lactate and only feeds butyrate producers via cross-feeding
(PMID 38126785); butyrate production is restricted to specific clostridial
clusters (PMIDs 26925050, 19807780) - in this table F. prausnitzii and
Roseburia. Non-producer butyrate entries zeroed.

BUG 75: compartment migration used np.roll - a periodic boundary, so the
proximal compartment exchanged directly with the distal one as if the gut
were a ring. Replaced with a zero-padded chain Laplacian (endpoints have one
neighbour); mass conservation is identical (column sums 0).
"""
import numpy as np
import pytest
from sugarcode.modules.micro_tx import core as mt

NON_PRODUCERS = ["Bifidobacterium_adolescentis", "Akkermansia_muciniphila", "Lactobacillus_reuteri"]
PRODUCERS = ["Faecalibacterium_prausnitzii", "Roseburia"]


def test_non_producers_make_no_butyrate_in_flux():
    for s in NON_PRODUCERS:
        r = mt.constraint_based_fiber_flux(s, {"inulin": 5, "mucin": 5, "resistant_starch": 5})
        assert r["metabolite_flux"]["butyrate"] == 0.0, s
        assert r["metabolite_flux"]["acetate"] > 0, s


def test_producers_still_make_butyrate():
    for s in PRODUCERS:
        r = mt.constraint_based_fiber_flux(s, {"pectin": 5, "resistant_starch": 5})
        assert r["metabolite_flux"]["butyrate"] > 0, s


def test_scfa_table_butyrate_column_matches_biology():
    for s in NON_PRODUCERS:
        assert mt.SCFA_YIELD[mt.STRAINS.index(s), 2] == 0.0, s
    for s in PRODUCERS:
        assert mt.SCFA_YIELD[mt.STRAINS.index(s), 2] > 0.5, s


def test_migration_is_a_chain_not_a_ring():
    x = np.ones((3, 5)); x[2] = 5.0  # distal-only perturbation
    mig = mt._migration(x)
    assert np.all(mig[0] == 0.0)          # proximal untouched (no wrap-around)
    assert np.all(mig[1] > 0.0)           # transverse feels it
    x0 = np.ones((3, 5)); x0[0] = 5.0
    mig0 = mt._migration(x0)
    assert np.all(mig0[2] == 0.0)         # and the mirror direction


def test_migration_conserves_mass():
    rng = np.random.default_rng(0)
    x = rng.random((3, 5))
    assert abs(mt._migration(x).sum()) < 1e-12


def test_ecology_butyrate_only_from_producers():
    eco = mt.simulate_spatial_ecology({}, {"resistant_starch": 5})
    f = eco["final_relative"]
    expect = sum(f[s] * mt.SCFA_YIELD[mt.STRAINS.index(s)] for s in mt.STRAINS)
    got = eco["metabolite_profile"]
    for k, v in zip(("acetate", "propionate", "butyrate"), expect):
        assert got[k] == pytest.approx(v, abs=2e-6)
    assert got["butyrate"] > 0


def test_lp_flux_matches_analytic_optimum():
    doses = {"inulin": 5.0, "GOS": 3.0, "mucin": 2.0}
    dose = np.array([doses.get(f, 0) for f in mt.FIBERS])
    for s in mt.STRAINS:
        i = mt.STRAINS.index(s)
        r = mt.constraint_based_fiber_flux(s, doses)
        assert r["biomass_flux"] == pytest.approx(mt.YIELDS[i] * float((dose * mt.ENZYME_ACCESS[i]).sum()), abs=1e-6)


def test_fermentation_conserves_mass():
    r = mt.enzymatic_fiber_fermentation("inulin", 10.0)
    tot = (np.array(r["remaining_g"]) + np.array(r["acetate_g"])
           + np.array(r["propionate_g"]) + np.array(r["butyrate_g"]))
    assert float(np.abs(tot - 10.0).max()) < 1e-9
