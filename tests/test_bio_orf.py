"""bio.orf ORF/translation toolkit (drop 79)."""
import pytest

from sugarcode.bio import orf


def test_tables_and_genetic_code():
    assert orf.tables() == [1, 2, 4, 11]
    code = orf.genetic_code(2)
    assert "Mitochondrial" in code["name"]
    assert "TGA" not in code["stops"] and code["forward"]["TGA"] == "W"
    with pytest.raises(ValueError):
        orf.genetic_code(999)


def test_translate_hand_computed():
    assert orf.translate("ATGAAATAA") == "MK*"
    assert orf.translate("TGATAA", table=2) == "W*"   # mito TGA = Trp
    assert orf.translate("AGAAGG", table=2) == "**"    # mito Arg -> stop
    assert orf.translate("AUGAAAUAA") == "MK*"         # U treated as T
    assert orf.translate("ATGAAATA") == "MK"           # trailing 2 nt dropped
    assert orf.translate("ATGNNNTAA") == "MX*"         # ambiguous codon -> X


def test_translate_cds_validation():
    assert orf.translate("ATGAAATAA", cds=True) == "MK*"
    assert orf.translate("GTGAAATAA", table=11, cds=True) == "VK*"  # literal
    with pytest.raises(ValueError):
        orf.translate("ATGAA", cds=True)          # not a multiple of 3
    with pytest.raises(ValueError):
        orf.translate("GTGAAATAA", cds=True)      # not a table-1 start
    with pytest.raises(ValueError):
        orf.translate("ATGAAAGGG", cds=True)      # no terminal stop
    with pytest.raises(ValueError):
        orf.translate("ATGTAATAA", cds=True)      # internal stop


def test_translate_oracle_all_codons_all_tables():
    pytest.importorskip("Bio")
    from Bio.Seq import Seq
    codons = [a + b + c for a in "ACGT" for b in "ACGT" for c in "ACGT"]
    blob = "".join(codons)
    for tid in (1, 2, 4, 11):
        assert orf.translate(blob, table=tid) == \
            str(Seq(blob).translate(table=tid))


def test_find_orfs_forward_hand_computed():
    r = orf.find_orfs("CCATGAAAGGCTAACC", min_aa=1)
    assert len(r) == 1
    o = r[0]
    assert (o["start"], o["end"]) == (2, 14)     # stop TAA included
    assert o["frame"] == 3 and o["strand"] == "+"
    assert o["protein"] == "MKG" and o["length_aa"] == 3
    assert o["length_nt"] == 12 and o["stop_codon"] == "TAA"
    assert o["truncated"] is False
    assert o["gc"] == pytest.approx(4 / 12, abs=1e-6)


def test_find_orfs_reverse_strand_coordinates():
    r = orf.find_orfs("GGTTATTTCATGG", min_aa=1)
    assert len(r) == 1
    o = r[0]
    assert o["strand"] == "-" and o["frame"] == -3
    assert (o["start"], o["end"]) == (2, 11)     # input coordinates
    assert o["protein"] == "MK"


def test_find_orfs_min_aa_filter():
    assert orf.find_orfs("CCATGAAAGGCTAACC", min_aa=4) == []
    assert orf.find_orfs("CCATGAAAGGCTAACC", min_aa=3) != []


def test_find_orfs_alternative_starts():
    # GTG is not ATG: default mode finds nothing; table-11 Starts row does
    assert orf.find_orfs("GTGAAATAA", table=11, min_aa=1) == []
    r = orf.find_orfs("GTGAAATAA", table=11, starts="table", min_aa=1)
    assert len(r) == 1
    assert r[0]["start_codon"] == "GTG"
    assert r[0]["protein"] == "MK"   # initiator forced to M (documented)


def test_find_orfs_nested_policies():
    seq = "ATGAAAATGCCCTAA"
    r = orf.find_orfs(seq, min_aa=1, both_strands=False, nested="longest")
    assert len(r) == 1 and r[0]["protein"] == "MKMP"
    r = orf.find_orfs(seq, min_aa=1, both_strands=False, nested="all")
    assert [o["length_aa"] for o in r] == [4, 2]  # nested ORFs share the stop
    assert all(o["stop_codon"] == "TAA" for o in r)


def test_find_orfs_truncated_policy():
    assert orf.find_orfs("ATGAAA", min_aa=1, both_strands=False) == []
    r = orf.find_orfs("ATGAAA", min_aa=1, both_strands=False,
                      allow_truncated=True)
    assert len(r) == 1
    o = r[0]
    assert o["truncated"] is True and o["stop_codon"] is None
    assert o["protein"] == "MK" and (o["start"], o["end"]) == (0, 6)


def test_find_orfs_input_validation():
    with pytest.raises(ValueError):
        orf.find_orfs("ATG", starts="aug")
    with pytest.raises(ValueError):
        orf.find_orfs("ATG", nested="some")
    with pytest.raises(ValueError):
        orf.find_orfs("ATG", min_aa=0)
