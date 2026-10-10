"""Authored NOT RUN. Additive schema preparation, not product integration."""
from dataclasses import replace

import pytest

from sugarcode.bio.bed_prefix_schema import (
    BedPrefixRow, FIELDS, parse_bed_prefix_line, write_bed_prefix_line,
)
from bed_prefix_fixtures import ROWS_BY_WIDTH, TOKENS


@pytest.mark.parametrize("width", range(3, 13))
def test_all_ten_widths_roundtrip_lexical_and_typed(width):
    line = ROWS_BY_WIDTH[width]
    row = parse_bed_prefix_line(line, line_number=4)
    assert row.field_count == width
    assert tuple(row.as_record()) == FIELDS[:width]
    assert write_bed_prefix_line(row, line_number=4) == line
    assert parse_bed_prefix_line(write_bed_prefix_line(row, line_number=4), line_number=4) == row
    assert row.has_thick_interval == (width >= 8)
    assert row.has_block_geometry == (width == 12)


@pytest.mark.parametrize("width,missing", [(7, "thick_end"), (10, "block_sizes"), (11, "block_starts")])
def test_partial_prefix_has_no_synthesized_group_fields(width, missing):
    row = parse_bed_prefix_line(ROWS_BY_WIDTH[width], line_number=1)
    assert missing not in row.as_record()
    assert len(row.tokens) == len(row.values) == width


@pytest.mark.parametrize("width", [3, 6, 8, 9, 12])
def test_existing_product_complete_width_semantics_match(width):
    # Later peer execution compares against unchanged real product parser/writer.
    from sugarcode.bio.bed import parse_bed, write_bed
    line = ROWS_BY_WIDTH[width]
    row = parse_bed_prefix_line(line, line_number=1)
    original = parse_bed(line + "\n")
    assert row.as_record() == original["records"][0]
    assert write_bed_prefix_line(row, line_number=1) + "\n" == write_bed(original)


@pytest.mark.parametrize("width", [10, 11])
def test_original_incomplete_block_canary_and_new_prefix(width):
    from sugarcode.bio.bed import parse_bed
    line = ROWS_BY_WIDTH[width]
    with pytest.raises(IndexError):
        parse_bed(line + "\n")
    assert parse_bed_prefix_line(line, line_number=1).field_count == width


def test_original_bed7_silent_loss_canary():
    from sugarcode.bio.bed import parse_bed
    line = ROWS_BY_WIDTH[7]
    assert "thick_start" not in parse_bed(line + "\n")["records"][0]
    assert parse_bed_prefix_line(line, line_number=1).as_record()["thick_start"] == 0


@pytest.mark.parametrize("width", [0, 1, 2, 13])
def test_out_of_domain_width_has_line_context(width):
    line = "\t".join((TOKENS + ("extra",))[:width])
    with pytest.raises(ValueError, match="line 17:"):
        parse_bed_prefix_line(line, line_number=17)


@pytest.mark.parametrize("index,bad", [
    (0, ""), (1, "x"), (1, "-1"), (2, "0"), (4, "bad"), (4, "NaN"),
    (4, "Infinity"), (5, "?"), (6, "bad"), (6, "101"), (7, "-1"),
    (9, "bad"), (9, "0"), (10, ""), (10, "10,,5"), (10, "10,0"),
    (10, "10"), (11, "bad"), (11, "0"), (11, "1,15"),
    (11, "0,-1"), (11, "0,99"),
])
def test_malformed_present_fields_refuse_controlled_with_line_context(index, bad):
    tokens = list(TOKENS)
    tokens[index] = bad
    with pytest.raises(ValueError, match="line 8:"):
        parse_bed_prefix_line("\t".join(tokens), line_number=8)


@pytest.mark.parametrize("width,index,bad", [
    (7, 6, "bad"), (7, 6, "-1"), (10, 9, "bad"), (10, 9, "0"),
    (11, 10, "bad"), (11, 10, "10"), (11, 10, "10,-5"),
])
def test_partial_width_local_validation_never_index_error(width, index, bad):
    tokens = list(TOKENS[:width])
    tokens[index] = bad
    with pytest.raises(ValueError, match="line 9:"):
        parse_bed_prefix_line("\t".join(tokens), line_number=9)


@pytest.mark.parametrize("suffix", ["", "\n", "\r\n", "\r"])
def test_single_line_endings_and_spelling_preserved(suffix):
    line = ROWS_BY_WIDTH[12].replace("\t50\t", "\t0050\t")
    row = parse_bed_prefix_line(line + suffix, line_number=1)
    assert write_bed_prefix_line(row, line_number=1) == line


@pytest.mark.parametrize("line", ["chr1\t0\t100\nextra", "chr1\t0\t100\rextra"])
def test_embedded_line_boundaries_refused(line):
    with pytest.raises(ValueError, match="line 2:"):
        parse_bed_prefix_line(line, line_number=2)


def test_writer_refuses_forged_inconsistent_or_nonbuiltin_values():
    row = parse_bed_prefix_line(ROWS_BY_WIDTH[12], line_number=1)
    with pytest.raises(ValueError, match="line 1:"):
        write_bed_prefix_line(replace(row, values=row.values[:-1]), line_number=1)
    class Custom:
        def __eq__(self, other):
            raise AssertionError("custom equality invoked")
    with pytest.raises(ValueError, match="line 1:"):
        write_bed_prefix_line(replace(row, values=(Custom(),) + row.values[1:]), line_number=1)
    with pytest.raises(ValueError, match="line 1:"):
        write_bed_prefix_line(BedPrefixRow(("a\tb", "0", "1"), ("a\tb", 0, 1)), line_number=1)


def test_partial_arrays_are_immutable_and_record_copy_is_independent():
    row = parse_bed_prefix_line(ROWS_BY_WIDTH[11], line_number=1)
    record = row.as_record()
    record["block_sizes"].append(9)
    assert row.values[10] == (10, 5)


@pytest.mark.parametrize("score", ["50.0", "0.5", "-1", "1001", "1e2", "+50", " 50", "50 ", "NaN", "Infinity", "", "1_000", "５０"])
def test_score_must_be_lexical_ascii_integer_in_range(score):
    tokens = list(TOKENS)
    tokens[4] = score
    with pytest.raises(ValueError, match="line 23:.*score"):
        parse_bed_prefix_line("\t".join(tokens), line_number=23)


@pytest.mark.parametrize("score,expected", [("0", 0), ("1000", 1000), ("50", 50), ("0050", 50), ("000", 0)])
def test_admitted_integer_score_exact_spelling_preserved(score, expected):
    tokens = list(TOKENS)
    tokens[4] = score
    line = "\t".join(tokens)
    row = parse_bed_prefix_line(line, line_number=6)
    assert type(row.values[4]) is int and row.values[4] == expected
    assert write_bed_prefix_line(row, line_number=6) == line
    assert row.tokens[4] == score


def test_writer_refuses_float_score_even_when_numerically_equal():
    row = parse_bed_prefix_line(ROWS_BY_WIDTH[12], line_number=1)
    values = list(row.values)
    values[4] = 50.0
    with pytest.raises(ValueError, match="line 1:"):
        write_bed_prefix_line(replace(row, values=tuple(values)), line_number=1)
