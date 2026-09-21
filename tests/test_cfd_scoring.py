"""Published CFD model (Doench 2016) tests. Expected values are derived from
the vendored matrices themselves plus the verified reference behavior
(cross-validated 0/500 disagreements against the CRISPOR calc_cfd at build time)."""
import json
import pytest

from sugarcode.modules.crispr_opt import cfd_score, score_off_targets_cfd
from sugarcode.modules.crispr_opt.core import _CFD_MM, _CFD_PAM

G = "GAGTCCGAGCAGAAGAAGAA"


def test_matrices_complete():
    # 12 RNA:DNA mismatch types x 20 positions = 240; 16 dinucleotide PAMs
    assert len(_CFD_MM) == 240
    assert len(_CFD_PAM) == 16
    assert _CFD_PAM["GG"] == 1.0  # NGG reference activity


def test_perfect_match_scores_one():
    assert cfd_score(G, G, "GG") == 1.0


def test_seed_mismatch_penalized_harder_than_distal():
    distal = cfd_score(G, "A" + G[1:], "GG")       # position 1
    seed = cfd_score(G, G[:18] + "C" + G[19:], "GG")  # position 19
    assert distal > seed
    assert seed < 0.3


def test_nag_pam_reduces_activity():
    assert cfd_score(G, G, "AG") == pytest.approx(_CFD_PAM["AG"], abs=1e-5)
    assert cfd_score(G, G, "AG") < 1.0


def test_length_mismatch_and_unknown_pam():
    with pytest.raises(ValueError):
        cfd_score(G, G[:19], "GG")
    with pytest.raises(KeyError):
        cfd_score(G, G, "ZZ")


def test_genome_scan_finds_planted_offtarget():
    bg = "T" * 30 + G[:18] + "CA" + "AGG" + "T" * 30
    hits = score_off_targets_cfd(G, bg)
    assert len(hits) >= 1
    top = hits[0]
    assert top["mismatches"] == 1
    assert 0.1 < top["cfd_score"] < 0.5
    assert top["risk"] == "medium"


def test_scan_ignores_distant_sites():
    hits = score_off_targets_cfd(G, "A" * 200)
    assert hits == []


def test_streaming_fasta_scan(tmp_path):
    from sugarcode.modules.crispr_opt import score_off_targets_cfd_fasta
    from sugarcode.bio.fasta import stream_fasta
    fa = tmp_path / "bg.fa"
    fa.write_text(">chr1 description here\n" + "T" * 30 + "\n"
                  + G[:18] + "CA" + "AGG" + "\n" + "T" * 30 + "\n"
                  ">chr2\n" + "A" * 100 + "\n")
    recs = list(stream_fasta(str(fa)))
    assert [r["id"] for r in recs] == ["chr1", "chr2"]
    assert recs[0]["description"] == "chr1 description here"
    r = score_off_targets_cfd_fasta(G, str(fa))
    assert r["records_scanned"][1]["length"] == 100
    assert len(r["hits"]) >= 1
    assert r["hits"][0]["record"] == "chr1"
    assert r["total_bases"] == len("T" * 30 + G[:18] + "CA" + "AGG" + "T" * 30) + 100
