"""Reverse-strand ORFs are placed in forward-strand coordinates before the coding mask is applied."""
from sugarcode.bio.sequence import reverse_complement
from sugarcode.modules.dark_genome.core import decode

ORF = "ATG" + "GCT" * 24 + "TAA"          # 78 nt, 25 aa
FWD = "A" * 5 + ORF + "A" * 100            # ORF at forward 5..83
REV_LOCUS = reverse_complement(FWD)        # ORF now lies on the minus strand
FWD_LOCUS = FWD


def _starts(res):
    return [(c["start"], c["end"], c["strand"]) for c in res["short_noncoding_orf_candidates"]]


def test_reverse_orf_inside_coding_span_is_excluded():
    # forward-strand span of the minus-strand ORF in REV_LOCUS: 183-83 .. 183-5
    res = decode(REV_LOCUS, coding_spans=[(100, 178)])
    assert _starts(res) == []


def test_reverse_orf_outside_coding_span_is_reported_in_forward_coordinates():
    res = decode(REV_LOCUS)
    assert _starts(res) == [(100, 178, "-")]
    res2 = decode(REV_LOCUS, coding_spans=[(0, 50)])
    assert _starts(res2) == [(100, 178, "-")]


def test_forward_orf_behavior_unchanged():
    assert _starts(decode(FWD_LOCUS)) == [(5, 83, "+")]
    assert _starts(decode(FWD_LOCUS, coding_spans=[(5, 83)])) == []
    assert _starts(decode(FWD_LOCUS, coding_spans=[(100, 150)])) == [(5, 83, "+")]


def test_decode_docstring_states_forward_strand_coordinates():
    from sugarcode.modules.dark_genome.core import decode
    assert "coordinates are forward-strand" in " ".join(decode.__doc__.split())
