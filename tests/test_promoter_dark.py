from sugarcode.modules.promoter_lib import design_promoter, generate_library, score_promoter
from sugarcode.modules.dark_genome import decode


def test_consensus_promoter_strong():
    s = score_promoter("AAAATATTT" + "TTGACA" + "T" * 17 + "TATAAT" + "GGGCC")
    assert s["strength"] > 0.75


def test_design_promoter_near_target():
    d = design_promoter(target_strength=0.6)
    assert abs(d["achieved"]["strength"] - 0.6) < 0.25


def test_library_spanning_range():
    lib = generate_library(n=8)
    lo, hi = lib["strength_range"]
    assert hi > lo
    assert len(lib["motif_heatmap"]) == 4


def test_dark_genome_finds_enhancer_cluster():
    seq = ("TGACTCA" + "N".replace("N", "A") * 50) * 1 + \
          "GGGCGG" + "AT" * 30 + "CCAAT" + "AT" * 30 + "TGACTCA" + "GGGCGG" + "CCAAT"
    r = decode(seq)
    assert r["tf_motif_hits"]
    assert r["dark_matter_fraction"] == 1.0
