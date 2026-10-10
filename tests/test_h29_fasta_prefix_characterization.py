"""H29 authored NOT RUN, plain status-quo characterization, not endorsement."""
import pytest
from sugarcode.bio.fasta import parse_fasta, stream_fasta

HEADER_FIRST = '>record description\nACGT\nTGCA\n'
PREFIX_THEN_HEADER = 'TTTT\n' + HEADER_FIRST
HEADERLESS = 'ACGT\nTGCA\n'
EXPECTED_RECORD = {'id': 'record', 'description': 'record description',
                   'sequence': 'ACGTTGCA'}


def test_stream_sequence_prefix_is_discarded_before_first_header(tmp_path):
    path = tmp_path / 'prefix.fa'
    path.write_text(PREFIX_THEN_HEADER, encoding='utf-8')
    assert list(stream_fasta(str(path))) == [EXPECTED_RECORD]


def test_stream_headerless_input_yields_no_records(tmp_path):
    path = tmp_path / 'headerless.fa'
    path.write_text(HEADERLESS, encoding='utf-8')
    assert list(stream_fasta(str(path))) == []


def test_stream_header_first_control(tmp_path):
    path = tmp_path / 'control.fa'
    path.write_text(HEADER_FIRST, encoding='utf-8')
    assert list(stream_fasta(str(path))) == [EXPECTED_RECORD]


def test_direct_bulk_parser_preheader_valueerror_characterization():
    # Direct parser only, no CLI/case-normalization/collision cross-reference.
    with pytest.raises(ValueError, match='FASTA sequence data encountered before any header'):
        parse_fasta(PREFIX_THEN_HEADER)
