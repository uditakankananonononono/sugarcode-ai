from sugarcode.bio.sequence import (translate, transcribe, reverse_complement,
                                    gc_content, find_motif, orfs, tm_wallace)
from sugarcode.bio.fasta import parse_fasta, write_fasta
from sugarcode.bio import codon, pwm


def test_translate_standard_code():
    assert translate("ATGGCCATTGTAATGGGCCGCTGAAAGGGTGCCCGATAG") == "MAIVMGR*KGAR*"


def test_translate_to_stop():
    assert translate("ATGAAATAAGGG", to_stop=True) == "MK"


def test_transcribe_and_rc():
    assert transcribe("ACGT") == "ACGU"
    assert reverse_complement("AACG") == "CGTT"


def test_gc_content():
    assert abs(gc_content("ATGC") - 0.5) < 1e-9


def test_find_motif_iupac():
    assert find_motif("AAATTTCCCGGG", "NGG") == [8, 9]
    assert find_motif("ATACG", "A") == [0, 2]


def test_orfs_finds_atg_stop():
    seq = "CCC" + "ATG" + "AAA" * 12 + "TAA" + "GGG"
    hits = orfs(seq, min_aa=5, both_strands=False)
    assert any(h["aa_length"] >= 12 for h in hits)


def test_tm_wallace_short():
    assert tm_wallace("ATGC") == 2 * 2 + 4 * 2


def test_fasta_roundtrip():
    recs = [{"id": "x", "sequence": "ACGT" * 20}]
    parsed = parse_fasta(write_fasta(recs))
    assert parsed[0]["sequence"] == "ACGT" * 20


def test_cai_perfect_for_top_codons():
    table = codon.ECOLI_K12
    seq = "".join(max(codon.synonymous_codons(a), key=lambda c: table[c])
                  for a in "LLVVGG")
    assert codon.cai(seq, table) > 0.9


def test_optimize_sequence_motif_avoidance():
    out = codon.optimize_sequence("MKTLLLG", codon.ECOLI_K12, avoid_motifs=["GAATTC"])
    assert "GAATTC" not in out


def test_pwm_scan():
    m = pwm.log_odds_matrix(pwm.build_pwm(["ACGT", "ACGT", "ACGA"]))
    hits = pwm.scan("TTACGTTT", m, threshold=0.9)
    assert hits and hits[0]["position"] == 2
