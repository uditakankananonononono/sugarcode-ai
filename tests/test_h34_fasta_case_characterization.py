"""Literal FASTA entrypoint case findings, not a standard-conformance claim."""
from sugarcode.bio.fasta import parse_fasta, stream_fasta, write_fasta


LITERAL = '>first description\nacGt\nTgca\n>second\ngGaA\n'
PRESERVED = [
    {'id': 'first', 'description': 'first description', 'sequence': 'acGtTgca'},
    {'id': 'second', 'description': 'second', 'sequence': 'gGaA'},
]


def test_bulk_uppercases_both_intermediate_and_final_record():
    assert parse_fasta(LITERAL) == [
        {'id': 'first', 'description': 'first description', 'sequence': 'ACGTTGCA'},
        {'id': 'second', 'description': 'second', 'sequence': 'GGAA'},
    ]


def test_stream_preserves_case_at_both_record_yields(tmp_path):
    path = tmp_path / 'mixed.fa'
    path.write_text(LITERAL, encoding='utf-8')
    assert list(stream_fasta(str(path))) == PRESERVED


def test_writer_preserves_case_and_wraps_literal_sequence():
    assert write_fasta(PRESERVED, line_width=4) == LITERAL
