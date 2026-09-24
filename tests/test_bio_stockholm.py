"""Stockholm/A3M toolkit: parse, roundtrip, match states, stats, filters."""
import pytest

from sugarcode.bio.stockholm import (parse_stockholm, write_stockholm,
                                     parse_a3m, write_a3m, a3m_match_states,
                                     pairwise_identity, stats, consensus,
                                     filter_columns, filter_sequences)

STO = """# STOCKHOLM 1.0
#=GF ID test
#=GF AC PF00001
seq1 ACGT
seq2 A-GT

seq1 TGCA
seq2 TGCA
#=GS seq1 DE first
#=GC SS_cons <<<<>>>>
#=GR seq1 SS xx..xx..
//
"""

A3M = ">master\nACdeGTf-\n>s2\nAgGT-eA\n"

ALN = [{"id": "a", "sequence": "ACGT"}, {"id": "b", "sequence": "AC-T"},
       {"id": "c", "sequence": "TCGT"}]


def test_parse_wrapped_blocks_and_markup():
    a = parse_stockholm(STO)
    assert a["seqs"] == [("seq1", "ACGTTGCA"), ("seq2", "A-GTTGCA")]
    assert a["gf"] == {"ID": "test", "AC": "PF00001"}
    assert a["gs"] == {"DE": {"seq1": "first"}}
    assert a["gc"] == {"SS_cons": "<<<<>>>>"}
    assert a["gr"] == {"SS": {"seq1": "xx..xx.."}}


def test_stockholm_semantic_roundtrip():
    a = parse_stockholm(STO)
    assert parse_stockholm(write_stockholm(a)) == a


def test_stockholm_rejections():
    with pytest.raises(ValueError, match="must start"):
        parse_stockholm("seq1 ACGT\n//\n")
    with pytest.raises(ValueError, match="terminator"):
        parse_stockholm("# STOCKHOLM 1.0\nseq1 ACGT\n")
    with pytest.raises(ValueError, match="inconsistent widths"):
        parse_stockholm("# STOCKHOLM 1.0\na ACGT\nb ACG\n//\n")
    with pytest.raises(ValueError, match="#=GC SS width"):
        parse_stockholm("# STOCKHOLM 1.0\ns AC\n#=GC SS <<<\n//\n")
    with pytest.raises(ValueError, match="unknown sequence"):
        parse_stockholm("# STOCKHOLM 1.0\ns AC\n#=GR zz SS <<\n//\n")
    with pytest.raises(ValueError, match="content after"):
        parse_stockholm("# STOCKHOLM 1.0\ns AC\n//\ns AC\n")


def test_a3m_preserves_case_and_inserts():
    recs = parse_a3m(A3M)
    assert [r["sequence"] for r in recs] == ["ACdeGTf-", "AgGT-eA"]
    ms = a3m_match_states(recs)
    assert [r["sequence"] for r in ms] == ["ACGT-", "AGT-A"]
    assert parse_a3m(write_a3m(recs)) == recs


def test_a3m_invalid_widths_rejected():
    with pytest.raises(ValueError, match="match-state widths disagree"):
        a3m_match_states(parse_a3m(">a\nACGT\n>b\nACGGT\n"))


def test_pairwise_identity_gaps_excluded():
    assert pairwise_identity("ACGT", "TCGT") == 0.75
    assert pairwise_identity("AC-T", "ACGT") == 1.0      # gap col excluded
    assert pairwise_identity("----", "----") == 0.0
    with pytest.raises(ValueError, match="equal width"):
        pairwise_identity("ACG", "ACGT")


def test_stats_math():
    s = stats([{"id": "a", "sequence": "ACGT"},
               {"id": "b", "sequence": "A-GT"}])
    assert s["nseq"] == 2 and s["width"] == 4
    assert s["gap_fraction"] == 0.125                    # 1 gap / 8 cells
    assert s["mean_pairwise_identity"] == 1.0            # gap col excluded
    with pytest.raises(ValueError, match="widths disagree"):
        stats([{"id": "a", "sequence": "A"}, {"id": "b", "sequence": "AA"}])


def test_consensus_threshold():
    assert consensus(ALN, 0.5) == "ACGT"
    strict = consensus(ALN, 0.99)                        # col 1 is 2/3 A
    assert strict == "-C-T"
    assert consensus([{"id": "x", "sequence": "----"}], 0.5) == "----"


def test_filters():
    assert filter_columns(ALN, 0.99)[0]["sequence"] == "ACT"
    assert filter_columns(ALN, 0.5)[0]["sequence"] == "ACGT"
    out = filter_sequences([{"id": "x", "sequence": "A-GT"},
                            {"id": "y", "sequence": "----"}], 0.5)
    assert [r["id"] for r in out] == ["x"]
    with pytest.raises(ValueError, match="\\[0, 1\\]"):
        filter_columns(ALN, 1.5)
