from sugarcode.modules.genomegpt import analyze_sequence, predict_loops, interpret_sequence_variant
from sugarcode.modules.gene_analysis import gene_profile

CTCF = "CCGCGAGGCGGCAG"
SEQ = "AT" * 100 + CTCF + "GC" * 1500 + CTCF[::-1].translate(str.maketrans("ACGT", "TGCA")) + "AT" * 100


def test_kmer_and_motifs():
    r = analyze_sequence(CTCF * 3 + "ATGC" * 50)
    assert r["gc_content"] > 0
    assert "kmer_anomalies" in r


def test_loops_convergent():
    loops = predict_loops(SEQ, min_span=1000)
    assert loops and loops[0]["orientation"] == "convergent"
    assert loops[0]["span"] >= 1000


def test_sequence_variant_motif():
    r = interpret_sequence_variant("GENE", CTCF, 5, "T")
    assert r["ref_base"] == CTCF[5]
    assert r["motifs_broken"] or r["regulatory_impact"]


def test_gene_profile_full():
    locus = ("GCGC" * 60) + "ATG" + "GCT" * 40 + "TAA" + ("ATGC" * 60) + "AGG" + ("TTGC" * 40)
    p = gene_profile("DEMO1", locus, variants=[{"variant": "c.5A>G", "consequence": "missense"}],
                     publications=[2001, 2003, 2007, 2012, 2019, 2021])
    assert p["symbol"] == "DEMO1"
    assert p["protein"] and p["crispr_targets"]
    assert p["variants"][0]["classification"]
    assert p["publication_trend"]["total"] == 6
