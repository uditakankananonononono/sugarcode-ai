from sugarcode.modules.rna_decoder import predict_m6a, modification_map, optimize_mrna

RNA = "AAAAA" + "GGACU".replace("U", "T") * 1 + "ATG" + "GCU" * 40 + "TAA" + "GGACT" * 8 + "A" * 30


def test_m6a_drach_detected():
    sites = predict_m6a(RNA, cds_start=8, cds_end=131, threshold=0.0)
    assert any(s["motif"][2] == "A" for s in sites)


def test_modification_map_structure():
    m = modification_map(RNA, cds_start=8, cds_end=131)
    assert m["drach_motifs"] >= 1
    assert m["writer_eraser_reader"]["writers"]


def test_optimize_mrna_outputs_edits():
    r = optimize_mrna(RNA, cds_start=8, cds_end=131)
    assert "proposed_edits" in r and "predicted_effect" in r
