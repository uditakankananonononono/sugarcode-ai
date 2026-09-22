"""Drop 31: U12 GT-AG golden - ClinVar variants at the PTEN intron-1 donor,
the first ClinVar-backed exercise of the drop-28 U12 GT-AG routing. PTEN
intron 1 is confirmed U12 by the intronIC gold set
(HomSap-gene-PTEN@rna-NM_001304717.5_2(9); donor window CCTGTATCC matches
the junctions.tsv harvest row). Both likely-pathogenic +1 donor variants
must be called loss WITH the U12 GT-AG subtype; the -1/-2 acceptor
variants are called loss on the U2 matrix (U12 acceptor routing declined
in drop 28). No benign cases fit the +/-6/-14 window (the benign c.79+7A>G
and c.79+778C>T sit deeper) - recorded honestly, not stretched."""
import json
from pathlib import Path

FIX = json.loads(Path("tests/fixtures/pten_u12_gtag_golden.json").read_text())


def test_fixture_shape():
    assert len(FIX["cases"]) == 5
    assert "NM_001304717" in FIX["source"]
    assert all(c["sig"] == "pathogenic" for c in FIX["cases"])


def test_u12_gtag_donor_variants_called_loss_with_subtype():
    donor = [c for c in FIX["cases"] if c["site_type"] == "donor"]
    assert {c["notation"] for c in donor} == {"c.79+1G>A", "c.79+1G>C"}
    for c in donor:
        assert c["delta"] <= -0.15, c
        assert c["donor_subtype"] == "U12 GT-AG", c


def test_acceptor_variants_loss_on_u2_matrix():
    acc = [c for c in FIX["cases"] if c["site_type"] == "acceptor"]
    assert {c["notation"] for c in acc} == {"c.80-1G>A", "c.80-1G>C", "c.80-2A>C"}
    for c in acc:
        assert c["delta"] <= -0.15 and c["donor_subtype"] is None


def test_pten_in_gold_u12_set():
    rows = [l.split("\t") for l in
            Path("src/sugarcode/bio/data/splice_sites/u12_sites.tsv")
            .read_text().splitlines()[1:]]
    assert any(r[0] == "GTAG" and r[1] == "CCTGTATCC" for r in rows)
