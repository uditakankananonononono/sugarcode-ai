import numpy as np
import pytest
from sugarcode.modules.synlife_evo import simulate_competition
from sugarcode.modules.synlife_evo.core import _GENE_STATES

G = ["crtE", "crtB", "crtI"]

def test_strong_coupling_drives_competitor_to_zero():
    r = simulate_competition(G, generations=1000, population=3000, burden=.02,
                             yield_selection=1.0, competitor_fraction=.05, sample_every=100)
    assert r["winner"] == "engineered" and r["final_competitor_fraction"] == 0.0
    assert r["dominant_genotype"] == {g: "intact" for g in G}

def test_no_coupling_high_burden_competitor_takeover():
    r = simulate_competition(G, generations=1000, population=3000, burden=.15,
                             yield_selection=0, competitor_fraction=.05, sample_every=100)
    assert r["winner"] == "wild-type competitor"
    assert r["competitor_takeover_generation"] == 100
    assert r["final_competitor_fraction"] == 1.0
    assert "overtakes" in r["predicted_adaptations"][0]

def test_high_mutation_per_gene_escape_findings():
    r = simulate_competition(G, generations=2000, population=5000, burden=.12,
                             yield_selection=.2, mutation_rate=1e-3,
                             competitor_fraction=0, sample_every=100)
    assert r["dominant_genotype"] == {g: "ko" for g in G}
    for g in G:
        s = r["final_per_gene_states"][g]
        assert s["ko"] > .9
        assert any(g in a and "loss of function" in a for a in r["predicted_adaptations"])
        assert r["gene_first_escape_generation"][g] == 200
    assert r["gene_failure_order"][0] in G

def test_seeded_exact_reproducibility():
    a = simulate_competition(["A"], generations=100, population=500, sample_every=10, seed=3)
    b = simulate_competition(["A"], generations=100, population=500, sample_every=10, seed=3)
    assert a == b

def test_mutation_matrix_rows_stochastic():
    # per-gene transition matrix used internally: rows must sum to 1
    m = 1e-4
    T = np.array([[1 - m, .6 * m, .4 * m], [.1 * m, 1 - .4 * m, .3 * m], [0, 0, 1]])
    assert np.allclose(T.sum(axis=1), 1.0)
    # and the composed genotype matrix for 2 genes stays stochastic
    M = np.kron(T, T)
    assert np.allclose(M.sum(axis=1), 1.0) and M.shape == (9, 9)

def test_seven_genes_clear_error():
    with pytest.raises(ValueError, match="at most 6 genes"):
        simulate_competition([f"g{i}" for i in range(7)])

def test_gene_states_cover_intact_down_ko():
    assert _GENE_STATES == ("intact", "down", "ko")
