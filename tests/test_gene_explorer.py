from sugarcode.modules.gene_explorer import explore, central_dogma_report

SEQ = "ATG" + "GCT" * 30 + "TAA" + "CCC" * 10


def test_explore_central_dogma():
    r = explore(SEQ, "demo")
    assert r["dna"]["length"] == len(SEQ)
    assert r["mrna"]["sequence"].startswith("AUG")
    assert r["protein"]["sequence"] == "M" + "A" * 30
    assert r["protein"]["molecular_weight_da"] > 1000
    assert len(r["animation_script"]) == 5


def test_report_mentions_orf():
    txt = central_dogma_report(SEQ, "demo")
    assert "demo" in txt and "Longest ORF" in txt
