"""Additive BED3..12 prefix schema preparation, not wired to product parser.

Partial widths carry explicit column presence, not synthesized grouped values.
No runtime tests were run during preparation. See the accompanying contract.
"""
from __future__ import annotations

from dataclasses import dataclass
import re

FIELDS = ("chrom", "start", "end", "name", "score", "strand", "thick_start",
          "thick_end", "item_rgb", "block_count", "block_sizes", "block_starts")


@dataclass(frozen=True)
class BedPrefixRow:
    """Exact admitted lexical prefix and its typed values, both immutable.

    tokens preserve spelling (e.g. 0050, trailing comma) for faithful emission.
    values use tuples for block arrays. Absent columns have no token/value.
    A BED7 row is not a complete thick interval, nor BED10/11 a block geometry.
    """
    tokens: tuple[str, ...]
    values: tuple[object, ...]

    @property
    def field_count(self) -> int:
        return len(self.tokens)

    def as_record(self) -> dict:
        """Legacy-compatible field names, but no fabricated absent columns."""
        return {name: list(value) if type(value) is tuple else value
                for name, value in zip(FIELDS, self.values)}

    @property
    def has_thick_interval(self) -> bool:
        return self.field_count >= 8

    @property
    def has_block_geometry(self) -> bool:
        return self.field_count == 12


def _error(line_number: int, reason: str) -> None:
    raise ValueError(f"line {line_number}: {reason}")


def _integer(token: str, line_number: int, field: str) -> int:
    try:
        return int(token)
    except ValueError:
        _error(line_number, f"{field} not an integer")


def _array(token: str, line_number: int, field: str) -> tuple[int, ...]:
    # A single optional final comma is allowed; doubled/empty interior cells are not.
    body = token[:-1] if token.endswith(",") else token
    if not body:
        _error(line_number, f"{field} must not be empty")
    return tuple(_integer(cell, line_number, field) for cell in body.split(","))


def parse_bed_prefix_line(line: str, *, line_number: int) -> BedPrefixRow:
    """Parse a data line, with controlled line-context errors at every width.

    Header/blank-line classification stays with the product parser. Accept a
    single LF/CRLF line ending or bare trailing CR. Tokens never contain embedded line boundaries.
    """
    if type(line_number) is not int or line_number < 1:
        raise ValueError("line_number must be a positive integer")
    if type(line) is not str:
        _error(line_number, "BED data line must be text")
    line = line.removesuffix("\n").removesuffix("\r")
    if "\n" in line or "\r" in line:
        _error(line_number, "embedded line boundary")
    tokens = tuple(line.split("\t"))
    width = len(tokens)
    if not 3 <= width <= 12:
        _error(line_number, "BED data must have 3..12 fields")
    if not tokens[0]:
        _error(line_number, "chrom must not be empty")
    values: list[object] = list(tokens)
    start = _integer(tokens[1], line_number, "start")
    end = _integer(tokens[2], line_number, "end")
    if start < 0 or end <= start:
        _error(line_number, "invalid 0-based interval")
    values[1:3] = [start, end]
    if width >= 5:
        if re.fullmatch(r"[0-9]+", tokens[4]) is None:
            _error(line_number, "score must be a lexical integer 0..1000")
        score = _integer(tokens[4], line_number, "score")
        if not 0 <= score <= 1000:
            _error(line_number, "score outside integer range 0..1000")
        values[4] = score
    if width >= 6 and tokens[5] not in ("+", "-", "."):
        _error(line_number, "invalid strand")
    if width >= 7:
        thick_start = _integer(tokens[6], line_number, "thick_start")
        if not start <= thick_start <= end:
            _error(line_number, "thick_start outside interval")
        values[6] = thick_start
    if width >= 8:
        thick_end = _integer(tokens[7], line_number, "thick_end")
        if not thick_start <= thick_end <= end:
            _error(line_number, "thick interval outside interval")
        values[7] = thick_end
    if width >= 10:
        count = _integer(tokens[9], line_number, "block_count")
        if count < 1:
            _error(line_number, "block_count must be positive")
        values[9] = count
    if width >= 11:
        sizes = _array(tokens[10], line_number, "block_sizes")
        if len(sizes) != count or any(size < 1 or size > end - start for size in sizes):
            _error(line_number, "block_sizes count or size invalid")
        values[10] = sizes
    if width == 12:
        starts = _array(tokens[11], line_number, "block_starts")
        if len(starts) != count:
            _error(line_number, "block_starts count mismatch")
        if starts[0] != 0:
            _error(line_number, "first blockStart must be 0")
        for offset, size in zip(starts, sizes):
            if offset < 0 or offset + size > end - start:
                _error(line_number, "block escapes interval")
        values[11] = starts
    return BedPrefixRow(tokens, tuple(values))


def write_bed_prefix_line(row: BedPrefixRow, *, line_number: int) -> str:
    """Emit exactly the prefix admitted at parse, after validating consistency.

    Full thick/block groups exist only at >=8/12; partial prefix columns retain
    their individual presence at 7/10/11. No defaults or grouped substitution.
    """
    if type(row) is not BedPrefixRow or type(row.tokens) is not tuple or type(row.values) is not tuple:
        _error(line_number, "BedPrefixRow with exact tuple fields required")
    if any(type(token) is not str or "\t" in token or "\n" in token or "\r" in token
           for token in row.tokens):
        _error(line_number, "invalid lexical token")
    emitted = "\t".join(row.tokens)
    checked = parse_bed_prefix_line(emitted, line_number=line_number)
    # Do not invoke custom value equality hooks on caller-constructed rows.
    for value in row.values:
        if type(value) not in (str, int, tuple):
            _error(line_number, "unsupported typed value")
        if type(value) is tuple and any(type(item) is not int for item in value):
            _error(line_number, "block arrays require exact integers")
    if row.values != checked.values:
        _error(line_number, "typed values differ from lexical prefix")
    return emitted
