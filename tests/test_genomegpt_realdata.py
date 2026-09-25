"""Real-data validation for genomegpt (module 101).

HBB_GENE_1600 is the 1600-bp slice of NG_000007.3 starting at the HBB CDS
(1-based 70595; GenBank CDS join(70595..70686, 70817..71039, 71890..72018),
verified to translate to the exact 147-aa HBB protein P68871).
True junctions relative to the slice start: IVS1 donor GT at 92 (non-consensus
GTTGGT in this RefSeqGene haplotype), IVS1 acceptor AG at ~220, IVS2 donor GT
at 445, IVS2 acceptor AG at ~1294.
"""
import pytest
from sugarcode.modules.genomegpt.core import (
    predict_loops, reconstruct_contact_map, contact_probability,
    splice_sites, _pwm_scores, _DONOR,
)
from sugarcode.bio.sequence import reverse_complement

CTCF = "CCGCGGGGGGGCAG"  # one concrete 14-mer instance of CCGCGNGGNGGCAG
HBB_GENE_1600 = (
    "ATGGTGCATCTGACTCCTGAGGAGAAGTCTGCCGTTACTGCCCTGTGGGGCAAGGTGAACGTGGATGAAGTTGGTGGTGA"
    "GGCCCTGGGCAGGTTGGTATCAAGGTTACAAGACAGGTTTAAGGAGACCAATAGAAACTGGGCATGTGGAGACAGAGAAG"
    "ACTCTTGGGTTTCTGATAGGCACTGACTCTCTCTGCCTATTGGTCTATTTTCCCACCCTTAGGCTGCTGGTGGTCTACCC"
    "TTGGACCCAGAGGTTCTTTGAGTCCTTTGGGGATCTGTCCACTCCTGATGCTGTTATGGGCAACCCTAAGGTGAAGGCTC"
    "ATGGCAAGAAAGTGCTCGGTGCCTTTAGTGATGGCCTGGCTCACCTGGACAACCTCAAGGGCACCTTTGCCACACTGAGT"
    "GAGCTGCACTGTGACAAGCTGCACGTGGATCCTGAGAACTTCAGGGTGAGTCTATGGGACGCTTGATGTTTTCTTTCCCC"
    "TTCTTTTCTATGGTTAAGTTCATGTCATAGGAAGGGGATAAGTAACAGGGTACAGTTTAGAATGGGAAACAGACGAATGA"
    "TTGCATCAGTGTGGAAGTCTCAGGATCGTTTTAGTTTCTTTTATTTGCTGTTCATAACAATTGTTTTCTTTTGTTTAATT"
    "CTTGCTTTCTTTTTTTTTCTTCTCCGCAATTTTTACTATTATACTTAATGCCTTAACATTGTGTATAACAAAAGGAAATA"
    "TCTCTGAGATACATTAAGTAACTTAAAAAAAAACTTTACACAGTCTGCCTAGTACATTACTATTTGGAATATATGTGTGC"
    "TTATTTGCATATTCATAATCTCCCTACTTTATTTTCTTTTATTTTTAATTGATACATAATCATTATACATATTTATGGGT"
    "TAAAGTGTAATGTTTTAATATGTGTACACATATTGACCAAATCAGGGTAATTTTGCATTTGTAATTTTAAAAAATGCTTT"
    "CTTCTTTTAATATACTTTTTTGTTTATCTTATTTCTAATACTTTCCCTAATCTCTTTCTTTCAGGGCAATAATGATACAA"
    "TGTATCATGCCTCTTTGCACCATTCTAAAGAATAACAGTGATAATTTCTGGGTTAAGGCAATAGCAATATCTCTGCATAT"
    "AAATATTTCTGCATATAAATTGTAACTGATGTAAGAGGTTTCATATTGCTAATAGCAGCTACAATCCAGCTACCATTCTG"
    "CTTTTATTTTATGGTTGGGATAAGGCTGGATTATTCTGAGTCCAAGCTAGGCCCTTTTGCTAATCATGTTCATACCTCTT"
    "ATCTTCCTCCCACAGCTCCTGGGCAACGTGCTGGTCTGTGTGCTGGCCCATCACTTTGGCAAAGAATTCACCCCACCAGT"
    "GCAGGCTGCCTATCAGAAAGTGGTGGCTGGTGTGGCTAATGCCCTGGCCCACAAGTATCACTAAGCTCGCTTTCTTGCTG"
    "TCCAATTTCTATTAAAGGTTCCTTTGTTCCCTAAGTCCAACTACTAAACTGGGGGATATTATGAAGGGCCTTGAGCATCT"
    "GGATTCTGCCTAATAAAAAACATTTATTTTCATTGCAATGATGTATTTAAATTATTTCTGAATATTTTACTAAAAAGGGA"
)

def _synthetic_ctcf_construct():
    seq = list("A" * 4000)
    seq[500:514] = CTCF
    rc = reverse_complement(CTCF)
    seq[3000:3014] = rc
    return "".join(seq)

def test_predict_loops_finds_convergent_ctcf_pair():
    loops = predict_loops(_synthetic_ctcf_construct())
    assert len(loops) == 1
    loop = loops[0]
    assert loop["anchor1"] == 500 and loop["anchor2"] == 3000
    assert loop["span"] == 2500 and loop["orientation"] == "convergent"
    assert loop["confidence"] == 1.0

def test_contact_map_enhances_loop_bin_pair():
    cm = reconstruct_contact_map(_synthetic_ctcf_construct(), bin_size=1000)
    assert cm["ctcf_forward_bins"] == [0] and cm["ctcf_reverse_bins"] == [3]
    assert cm["matrix"][0][3] == pytest.approx(0.3993, abs=1e-3)   # loop bin pair
    assert cm["matrix"][1][3] == pytest.approx(0.2105, abs=1e-3)   # non-loop pair

def test_contact_probability_monotone_and_strand_aware():
    assert contact_probability(1000, ctcf_convergent=True) == pytest.approx(0.9103, abs=1e-3)
    assert contact_probability(1000, ctcf_convergent=False) == pytest.approx(0.354, abs=1e-3)
    assert contact_probability(10000, ctcf_convergent=True) == pytest.approx(0.1619, abs=1e-3)
    assert contact_probability(10000, ctcf_convergent=False) == pytest.approx(0.0629, abs=1e-3)
    assert contact_probability(1000, True) > contact_probability(1000, False)
    assert contact_probability(10000, True) < contact_probability(1000, True)

def test_donor_pwm_consensus_is_shapiro_senapathy():
    consensus = "".join("ACGT"[max(range(4), key=lambda b: col[b])] for col in _DONOR)
    assert consensus == "AAGGTAAGT"  # max-base form of MAG|GTRAGT
    assert tuple(_DONOR[3]) == (0, 0, 1, 0) and tuple(_DONOR[4]) == (0, 0, 0, 1)  # invariant GT

def test_splice_sites_finds_hbb_ivs2_donor_exact():
    sites = splice_sites(HBB_GENE_1600, threshold=0.8)
    donors = {d["position"]: d["score"] for d in sites["donors"]}
    assert 445 in donors and donors[445] >= 0.8  # IVS2 GT dinucleotide at rel 445

def test_splice_sites_finds_hbb_ivs2_acceptor():
    sites = splice_sites(HBB_GENE_1600, threshold=0.8)
    acceptors = {a["position"]: a["score"] for a in sites["acceptors"]}
    assert 1295 in acceptors and acceptors[1295] >= 0.8  # IVS2 AG at rel ~1294

def test_splice_sites_hbb_ivs1_acceptor_within_two_nt():
    sites = splice_sites(HBB_GENE_1600, threshold=0.6)
    assert any(abs(a["position"] - 220) <= 2 for a in sites["acceptors"])

def test_splice_sites_rejects_nonconsensus_ng_000007_ivs1_donor():
    # NG_000007.3's HBB IVS1 donor is GTTGGT, not the canonical GTAAGT; the
    # junction 9-mer CAGGTTGGT scores 0.476 of the consensus log-odds max and
    # is correctly absent at the default 0.8 threshold.
    sites = splice_sites(HBB_GENE_1600)
    assert all(abs(d["position"] - 92) > 5 for d in sites["donors"])
