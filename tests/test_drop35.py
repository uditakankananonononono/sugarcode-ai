"""Drop 35: SCN-family AT-AC golden. The SCN1A minor intron is conserved
across the sodium-channel family; 8 more pathogenic ClinVar AT-AC variants
in SCN2A/5A/8A/9A are ALL called loss on the U12 matrices with the
u12_atac flag (-0.158 donors / -0.205 acceptors). Combined with SCN1A's 8:
16/16 pathogenic canonical AT-AC variants called loss. Maps use the
ClinVar-cited transcripts via cdna_junction_map (coverage ~1.0);
SCN2A/5A/8A/9A RefSeqGene records are map-only harvest_meta extensions -
PWM training set untouched. No in-window benign cases exist at these
junctions (nearest benign is SCN9A c.377+93) - recorded honestly."""
import json
from pathlib import Path

FIX = json.loads(Path("tests/fixtures/scn_atac_u12_golden.json").read_text())


def test_fixture_shape():
    assert len(FIX["cases"]) == 8
    assert {c["gene"] for c in FIX["cases"]} == {"SCN2A", "SCN5A", "SCN8A", "SCN9A"}
    assert all(c["sig"] == "pathogenic" for c in FIX["cases"])
    assert "NM_001040142.2" in FIX["source"]


def test_all_atac_cases_called_loss_with_flag():
    for c in FIX["cases"]:
        assert c["delta"] <= -0.15, c
        assert c["u12_atac"] is True, c
    donors = [c for c in FIX["cases"] if c["site_type"] == "donor"]
    accs = [c for c in FIX["cases"] if c["site_type"] == "acceptor"]
    assert len(donors) == 4 and len(accs) == 4
    assert all(c["window"][3:5] == "AT" for c in donors)
    assert all(c["window"][12:14] == "AC" for c in accs)


def test_map_only_meta_extension():
    meta = json.loads(Path("src/sugarcode/bio/data/splice_sites/harvest_meta.json").read_text())
    train = {g["gene"] for g in meta["genes"]}
    maps = {g["gene"] for g in meta["map_only_genes"]}
    assert maps == {"SCN2A", "SCN5A", "SCN8A", "SCN9A"}
    assert not (maps & train)  # training set untouched
