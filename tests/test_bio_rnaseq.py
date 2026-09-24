"""bio.rnaseq RNA-seq count toolkit (drop 80)."""
import math

import pytest

from sugarcode.bio import rnaseq as rq


def _table(counts, genes=None, samples=None):
    n, m = len(counts), len(counts[0])
    return {"genes": genes or [f"g{i}" for i in range(n)],
            "samples": samples or [f"s{j}" for j in range(m)],
            "counts": [list(map(float, r)) for r in counts]}


def test_parse_counts_tsv_csv_and_roundtrip():
    t = rq.parse_counts("gene\ts1\ts2\ng1\t10\t20\ng2\t5\t0\n")
    assert t["genes"] == ["g1", "g2"]
    assert t["counts"] == [[10.0, 20.0], [5.0, 0.0]]
    t2 = rq.parse_counts("gene,s1\ng1,3.5\n")
    assert t2["counts"] == [[3.5]]
    assert rq.parse_counts(rq.write_counts(t))["counts"] == t["counts"]


def test_parse_counts_rejections():
    with pytest.raises(ValueError):
        rq.parse_counts("")
    with pytest.raises(ValueError):
        rq.parse_counts("gene,s1,s2\ng1,1\n")        # ragged
    with pytest.raises(ValueError):
        rq.parse_counts("gene,s1\ng1,x\n")           # non-numeric
    with pytest.raises(ValueError):
        rq.parse_counts("gene,s1\ng1,-3\n")          # negative
    with pytest.raises(ValueError):
        rq.parse_counts("gene,s1\ng1,1\ng1,2\n")     # duplicate gene
    with pytest.raises(ValueError):
        rq.parse_counts("gene,s1,s1\ng1,1,2\n")      # duplicate sample


def test_cpm_hand_computed():
    r = rq.cpm(_table([[10, 0], [30, 60]]))  # libs 40 and 60
    assert r["counts"] == [[250000.0, 0.0], [750000.0, 1000000.0]]
    assert r["library_sizes"] == [40.0, 60.0]
    with pytest.raises(ValueError):
        rq.cpm(_table([[0, 1], [0, 2]]))  # sample 0 library size 0


def test_rpkm_hand_computed():
    t = _table([[30]], genes=["g1"])
    r = rq.rpkm(t, {"g1": 2000})  # lib 120? no: lib = 30
    # CPM = 30/30*1e6 = 1e6; RPKM = 1e6 / 2 = 500000
    assert r["counts"] == [[500000.0]]
    with pytest.raises(ValueError):
        rq.rpkm(t, {"g1": 0})
    with pytest.raises(ValueError):
        rq.rpkm(t, {})


def test_tpm_hand_computed():
    t = _table([[10], [30]], genes=["a", "b"])
    r = rq.tpm(t, {"a": 1000, "b": 3000})
    # RPK: 10/1 = 10, 30/3 = 10 -> 500000 each
    assert r["counts"] == [[500000.0], [500000.0]]
    # TPM columns always sum to 1e6
    t2 = _table([[10, 5], [30, 15]], genes=["a", "b"])
    r2 = rq.tpm(t2, {"a": 1000, "b": 3000})
    for j in range(2):
        assert sum(r2["counts"][i][j] for i in range(2)) == \
            pytest.approx(1e6)


def test_size_factors_hand_computed():
    # geomeans: g1 (10*20*40)^(1/3)=20, g2 (5*10*20)^(1/3)=10,
    # g3 (1*10*100)^(1/3)=10; ratios per sample -> medians 0.5, 1, 2
    sf = rq.size_factors([[10, 20, 40], [5, 10, 20], [1, 10, 100]])
    assert sf == pytest.approx([0.5, 1.0, 2.0])


def test_size_factors_zero_rows_excluded():
    sf = rq.size_factors([[0, 0, 0], [10, 20, 40], [5, 10, 20]])
    assert sf == pytest.approx([0.5, 1.0, 2.0])
    with pytest.raises(ValueError):
        rq.size_factors([[0, 1], [0, 1]])  # no all-positive gene
    with pytest.raises(ValueError):
        rq.size_factors([])
    with pytest.raises(ValueError):
        rq.size_factors([[1, 2], [3]])     # ragged


def test_normalize_deseq_hand_computed():
    t = _table([[10, 20, 40], [5, 10, 20], [1, 10, 100]])
    r = rq.normalize_deseq(t)
    assert r["size_factors"] == pytest.approx([0.5, 1.0, 2.0])
    for row in r["counts"]:
        assert row == pytest.approx([20.0, 20.0, 20.0]) or \
            row == pytest.approx([10.0, 10.0, 10.0]) or \
            row == pytest.approx([2.0, 10.0, 50.0])
    assert r["counts"][0] == pytest.approx([20.0, 20.0, 20.0])
    assert r["counts"][2] == pytest.approx([2.0, 10.0, 50.0])


def test_filter_genes_rule():
    t = _table([[5, 100], [50, 3], [0, 0]], genes=["x", "y", "z"])
    f = rq.filter_genes(t, min_count=10, min_samples=1)
    assert f["genes"] == ["x", "y"] and f["dropped"] == 1
    f = rq.filter_genes(t, min_count=10, min_samples=2)
    assert f["genes"] == [] and f["kept"] == 0
    f = rq.filter_genes(t, min_count=3, min_samples=2)
    assert f["genes"] == ["x", "y"]  # 5>=3 & 100>=3; 50>=3 & 3>=3
    with pytest.raises(ValueError):
        rq.filter_genes(t, min_count=1, min_samples=3)
