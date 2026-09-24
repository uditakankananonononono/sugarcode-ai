"""bio.de differential expression toolkit (drop 82)."""
import math

import numpy as np
import pytest

from sugarcode.bio import de as demod
from sugarcode.bio import gstats


def test_log2_fold_change_hand_computed():
    assert demod.log2_fold_change(15, 40, 1.0) == \
        pytest.approx(math.log2(41) - math.log2(16))
    assert demod.log2_fold_change(0, 0, 1.0) == 0.0
    with pytest.raises(ValueError):
        demod.log2_fold_change(1, 2, 0)
    with pytest.raises(ValueError):
        demod.log2_fold_change(-1, 2)


def test_welch_hand_computed_and_scipy_oracle():
    scipy = pytest.importorskip("scipy.stats")
    r = demod.welch_ttest([1, 2, 3], [4, 5, 6])
    assert r["statistic"] == pytest.approx(-3 / math.sqrt(2 / 3))
    assert r["df"] == pytest.approx(4.0)
    ref = scipy.ttest_ind([1, 2, 3], [4, 5, 6], equal_var=False)
    assert r["p"] == pytest.approx(ref.pvalue, abs=1e-12)
    with pytest.raises(ValueError):
        demod.welch_ttest([1], [2, 3])


def test_welch_degenerate_variance_policy():
    assert demod.welch_ttest([0, 0], [0, 0])["p"] == 1.0
    r = demod.welch_ttest([0, 0], [5, 5])
    assert r["p"] == 0.0 and r["statistic"] == -math.inf
    assert r["degenerate"] is True


def test_wilcoxon_hand_computed_and_scipy_oracle():
    scipy = pytest.importorskip("scipy.stats")
    w = demod.wilcoxon_rank_sum([1, 2, 3], [4, 5, 6])
    assert w["statistic"] == 0.0                     # U for group A
    assert w["z"] == pytest.approx(-4.0 / math.sqrt(5.25))
    ref = scipy.mannwhitneyu([1, 2, 3], [4, 5, 6],
                             alternative="two-sided",
                             use_continuity=True, method="asymptotic")
    assert w["p"] == pytest.approx(ref.pvalue, abs=1e-12)
    # ties: midranks + tie-corrected variance must still match scipy
    w2 = demod.wilcoxon_rank_sum([1, 2, 2], [2, 3, 4])
    ref2 = scipy.mannwhitneyu([1, 2, 2], [2, 3, 4],
                              alternative="two-sided",
                              use_continuity=True, method="asymptotic")
    assert w2["p"] == pytest.approx(ref2.pvalue, abs=1e-12)


def test_wilcoxon_all_tied():
    assert demod.wilcoxon_rank_sum([2, 2], [2, 2])["p"] == 1.0
    with pytest.raises(ValueError):
        demod.wilcoxon_rank_sum([], [1])


def _table(counts, genes=None):
    n, m = len(counts), len(counts[0])
    return {"genes": genes or [f"g{i}" for i in range(n)],
            "samples": [f"s{j}" for j in range(m)],
            "counts": [list(map(float, r)) for r in counts]}


def test_de_analysis_composition():
    table = _table([[10, 12, 40, 44], [20, 22, 21, 19], [5, 7, 6, 8]],
                   genes=["g1", "g2", "g3"])
    r = demod.de_analysis(table, ["A", "A", "B", "B"])
    assert r["group_a"] == "A" and r["group_b"] == "B"
    assert r["scope"] == demod.SCOPE          # honest-scope note attached
    rows = r["results"]
    assert [x["gene"] for x in rows] == ["g1", "g2", "g3"]
    q = gstats.benjamini_hochberg([x["pvalue"] for x in rows])
    assert [x["padj"] for x in rows] == pytest.approx(q)
    g1 = rows[0]
    assert g1["mean_b"] > g1["mean_a"] and g1["log2fc"] > 1.5
    assert {"gene", "mean_a", "mean_b", "log2fc", "statistic", "pvalue",
            "padj", "neg_log10_p"} <= set(g1)   # volcano-ready
    with pytest.raises(ValueError):
        demod.de_analysis(table, ["A", "A", "B", "C"])  # 3 groups
    with pytest.raises(ValueError):
        demod.de_analysis(table, ["A", "A", "B"])       # label mismatch
    with pytest.raises(ValueError):
        demod.de_analysis(table, ["A", "A", "B", "B"], method="limma")


def test_de_analysis_wilcoxon_method():
    table = _table([[10, 12, 40, 44], [20, 22, 21, 19]])
    r = demod.de_analysis(table, ["A", "A", "B", "B"], method="wilcoxon")
    assert r["method"] == "wilcoxon"
    assert all(0 <= x["pvalue"] <= 1 for x in r["results"])


def test_null_simulation_bh_keeps_most_genes():
    rng = np.random.default_rng(42)
    n_genes, n_rep = 300, 5
    counts = rng.poisson(50, size=(n_genes, 2 * n_rep)).astype(float)
    counts[0] += 1.0  # guarantee an all-positive gene for the size factors
    tab = _table(counts.tolist())
    res = demod.de_analysis(tab, ["A"] * n_rep + ["B"] * n_rep)
    sig = sum(1 for x in res["results"] if x["padj"] < 0.05)
    assert sig <= n_genes * 0.05


def test_planted_de_detected():
    rng = np.random.default_rng(7)
    n_genes, n_rep = 300, 5
    counts = rng.poisson(50, size=(n_genes, 2 * n_rep)).astype(float)
    planted = [f"de{i}" for i in range(10)]
    for i in range(10):
        counts[i] = np.concatenate([rng.poisson(50, n_rep),
                                    rng.poisson(400, n_rep)])
    genes = planted + [f"g{i}" for i in range(10, n_genes)]
    tab = _table(counts.tolist(), genes=genes)
    res = demod.de_analysis(tab, ["A"] * n_rep + ["B"] * n_rep)
    found = {x["gene"] for x in res["results"]
             if x["padj"] < 0.05 and x["log2fc"] > 0}
    assert set(planted) <= found
