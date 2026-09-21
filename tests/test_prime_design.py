from sugarcode.modules.prime_design import design_pegrna, design_edit

REGION = ("ACGT" * 30) + "AGG" + ("TTGCA" * 20)


def test_pegrna_pbs_rtt_ranges():
    d = design_pegrna("ACGTACGTACGTACGTACGT", "TTGCAAGGCC")
    assert 10 <= d["pbs_length"] <= 17
    assert 10 <= d["rtt_length"] <= 20
    assert d["full_pegrna"].endswith(d["pegrna_3p_extension"])


def test_design_edit_substitution():
    edit = {"type": "substitution", "position": 60, "ref": "A", "alt": "G"}
    r = design_edit(REGION, edit, background=REGION)
    assert r["edited_region"][60] == "G"
    assert r["pe_system"] in ("PE2", "PE3")
