"""Two literal CIGAR arithmetic shapes, not alignment/standard validation."""
from sugarcode.bio.sam import parse_cigar, cigar_reference_length, cigar_query_length


def test_literal_hp_equal_x_consuming_lengths():
    ops = parse_cigar('1H2P3=4X')
    assert ops == [(1, 'H'), (2, 'P'), (3, '='), (4, 'X')]
    assert cigar_reference_length(ops) == 7
    assert cigar_query_length(ops) == 7


def test_literal_hp_only_consumes_neither_reference_nor_query():
    ops = parse_cigar('1H2P')
    assert ops == [(1, 'H'), (2, 'P')]
    assert cigar_reference_length(ops) == 0
    assert cigar_query_length(ops) == 0
