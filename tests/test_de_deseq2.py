import random
import pytest


def test_deseq2_recovers_spiked_gene():
    pytest.importorskip("pydeseq2")
    from sugarcode.bio.de import de_analysis_deseq2
    rng = random.Random(0)
    genes = [f"g{i}" for i in range(200)]
    counts = []
    for i in range(200):
        base = rng.randint(50, 500)
        row = [max(0, int(rng.gauss(base, base ** 0.5 * 1.5))) for _ in range(6)]
        if i == 0:
            row = row[:3] + [v * 8 for v in row[3:]]
        counts.append(row)
    t = {"genes": genes, "samples": [f"s{j}" for j in range(6)], "counts": counts}
    r = de_analysis_deseq2(t, ["a"] * 3 + ["b"] * 3, blocks=["d1", "d2", "d3"] * 2)
    g0 = next(x for x in r["results"] if x["gene"] == "g0")
    assert g0["padj"] < 0.01 and g0["log2fc"] > 2
