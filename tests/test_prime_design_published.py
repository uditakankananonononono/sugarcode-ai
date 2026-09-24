"""Regression against the published HEK3 +1 CTT insertion pegRNA (Anzalone et
al. 2019, Addgene 132778): spacer GGCCCAGACTGAGCACGTGA, 3' extension
TCTGCCATCAAAGCGTGCTCAGTCTG = RTT TCTGCCATCAAAGC (14 nt) + PBS GTGCTCAGTCTG
(12 nt). RTT = revcomp of the edited strand 3' of the nick; PBS = revcomp of
the protospacer's PAM-proximal end (the 3' flap of the nicked strand)."""
from sugarcode.modules.prime_design import design_pegrna
from sugarcode.bio.sequence import reverse_complement

SPACER = "GGCCCAGACTGAGCACGTGA"
RTT = "TCTGCCATCAAAGC"
PBS = "GTGCTCAGTCTG"


def test_hek3_ctt_ins_extension_matches_published():
    edit_seq = reverse_complement(RTT)  # edited strand 3' of the nick
    d = design_pegrna(SPACER, edit_seq, pbs_len=12, rtt_len=14)
    assert d["rt_template"] == RTT
    assert d["pbs"] == PBS
    assert d["pegrna_3p_extension"] == RTT + PBS


def test_pbs_comes_from_spacer_flap_not_edit_seq():
    # any edit sequence: PBS must stay the flap sequence
    d1 = design_pegrna(SPACER, "AAAAAAAAAAAAAA", pbs_len=12, rtt_len=14)
    d2 = design_pegrna(SPACER, "CCCCCCCCCCCCCC", pbs_len=12, rtt_len=14)
    assert d1["pbs"] == d2["pbs"] == PBS


def test_insertion_edit_with_empty_ref_does_not_crash():
    from sugarcode.modules.prime_design import design_edit
    region = "CCTGGGTCAATCCTTGGGGCCCAGACTGAGCACGTGATGGCAGAGGAAAGG"
    r = design_edit(region, {"type": "insertion", "position": 34, "ref": "", "alt": "CTT"})
    assert r["pegrna_designs"] and r["pegrna_designs"][0]["spacer"] == "GGCCCAGACTGAGCACGTGA"
    top = r["pegrna_designs"][0]
    assert top["pbs"] == reverse_complement(top["spacer"][16 - top["pbs_length"]:16])
    assert top["rt_template"].endswith("TCTGCCATCAAAGC")  # published RTT templates from the nick


def test_rtt_truncation_keeps_nick_proximal_end():
    # 20 nt of edited context, 14 nt RTT: must template the 14 nt at the nick
    d = design_pegrna(SPACER, "GCTTTGATGGCAGAGGAAAG", pbs_len=12, rtt_len=14)
    assert d["rt_template"] == RTT
