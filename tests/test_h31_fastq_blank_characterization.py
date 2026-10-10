"""H31 authored NOT RUN: literal current behavior, not semantics endorsement."""
import pytest
from sugarcode.bio.fastq import parse_fastq, stream_fastq

FIRST = '@r1 first\nACGT\n+\nIIII\n'
SECOND = '@r2 second\nTGCA\n+\nIIII\n'
FIRST_RECORD = {'id': 'r1', 'description': 'r1 first', 'sequence': 'ACGT', 'quality': 'IIII'}
SECOND_RECORD = {'id': 'r2', 'description': 'r2 second', 'sequence': 'TGCA', 'quality': 'IIII'}


def test_ordinary_four_line_bulk_and_stream_control(tmp_path):
    path = tmp_path / 'control.fastq'
    path.write_text(FIRST, encoding='utf-8')
    assert parse_fastq(FIRST) == [FIRST_RECORD]
    assert list(stream_fastq(str(path))) == [FIRST_RECORD]


def test_one_leading_blank_bulk_accepts_stream_valueerror(tmp_path):
    literal = '\n' + FIRST
    path = tmp_path / 'leading.fastq'
    path.write_text(literal, encoding='utf-8')
    assert parse_fastq(literal) == [FIRST_RECORD]
    with pytest.raises(ValueError):
        list(stream_fastq(str(path)))


def test_one_separator_blank_bulk_both_stream_partial_progress(tmp_path):
    literal = FIRST + '\n' + SECOND
    path = tmp_path / 'separator.fastq'
    path.write_text(literal, encoding='utf-8')
    assert parse_fastq(literal) == [FIRST_RECORD, SECOND_RECORD]
    records = stream_fastq(str(path))
    try:
        assert next(records) == FIRST_RECORD
        with pytest.raises(ValueError):
            next(records)
    finally:
        records.close()
