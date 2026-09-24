import pytest
RNA = pytest.importorskip("RNA")
from sugarcode.modules.rna_nussinov import fold_energy, fold

# yeast tRNA-Phe (RF00005 family member), 76 nt
TRNA_PHE = "GCGGAUUUAGCUCAGUUGGGAGAGCGCCAGACUGAAGAUCUGGAGGUCCUGUGUUCGAUCCACAGAAUUCGCACCA"


def test_mfe_is_negative_and_balanced():
    r = fold_energy(TRNA_PHE)
    assert r["mfe_kcal_mol"] < -15
    assert r["dot_bracket"].count("(") == r["dot_bracket"].count(")") == len(r["pairs"])
    assert r["ensemble_free_energy_kcal_mol"] <= r["mfe_kcal_mol"]
    assert 0 < r["mfe_ensemble_frequency"] <= 1


def test_energy_model_pairs_fewer_than_nussinov_max():
    # Nussinov maximises pair count; the energy model must not exceed it
    assert len(fold_energy(TRNA_PHE)["pairs"]) <= len(fold(TRNA_PHE, count_optimal=False)["pairs"])


def test_acceptor_stem_recovered():
    pairs = {tuple(p) for p in fold_energy(TRNA_PHE)["pairs"]}
    # 7-bp acceptor stem: 0-71 ... 6-65 (G1-C72 ... in 1-based numbering)
    assert sum((i, 71 - i) in pairs for i in range(7)) >= 5


@pytest.mark.parametrize("method", ["mfe", "centroid", "mea"])
def test_methods_run(method):
    assert fold_energy(TRNA_PHE, method=method)["method"] == method


def test_bad_method():
    with pytest.raises(ValueError):
        fold_energy(TRNA_PHE, method="nope")
