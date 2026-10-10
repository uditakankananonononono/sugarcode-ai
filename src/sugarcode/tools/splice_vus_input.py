"""Pure input validation for splice_vus_triage rows (prep, not wired).

Nothing here imports torch/numpy/maxentpy or touches files. Every function
raises SpliceInputError (a ValueError) BEFORE any model call would happen, and
returns normalized values on success. This module does not claim anything about
model accuracy; it only defines which inputs are admissible.

Policy (as specified in the unit request relayed by the parent; adjudication is the peer's):
* ref and alt: exactly one base in ACGT (case-insensitive, normalized to upper).
  N, IUPAC codes, indels, empty, multi-base: rejected. ref != alt.
* pos: 1-based integer >= F+1 (F = 40, matches splice_vus_triage.F). Accepts an
  exact int (not bool) or a str of ASCII digits only (TSV cells); no sign,
  space, decimal point or exponent.
* chrom: non-empty str without whitespace.
* explicit contexts: ref_ctx and alt_ctx each exactly 81 chars from ACGTN
  (case-insensitive, normalized to upper); identical flanks (index 0..39 and
  41..80) compared exactly; center (index 40) must be ACGT in both (N rejected)
  and must differ. N in the flanks is tolerated, but only when it matches in
  both contexts (flanks must be identical).
* prior: exact int/float (not bool), finite, 0 < prior < 1.
Out of scope: strand/GT-AG inference, offset range (parse_offset owns it),
reference-allele match against a genome, resource use, regex/CSV parsing.
"""
from __future__ import annotations

import math

F = 40  # must equal splice_vus_triage.F; asserted by a test, not imported here
CTX_LEN = 2 * F + 1
_BASES = frozenset("ACGT")
_CTX_ALPHABET = frozenset("ACGTN")


class SpliceInputError(ValueError):
    """Row or option is outside the admissible input contract."""

    def __init__(self, field: str, code: str, message: str) -> None:
        super().__init__(f"{field}: {message}")
        self.field = field
        self.code = code


def validate_base(value: object, field: str) -> str:
    if type(value) is not str:
        raise SpliceInputError(field, "type", "must be a string")
    if len(value) != 1:
        raise SpliceInputError(field, "length", "must be exactly one base (indels rejected)")
    base = value.upper()
    if base not in _BASES:
        raise SpliceInputError(field, "alphabet", "must be one of A, C, G, T (N/IUPAC rejected)")
    return base


def validate_ref_alt(ref: object, alt: object) -> tuple[str, str]:
    r = validate_base(ref, "ref")
    a = validate_base(alt, "alt")
    if r == a:
        raise SpliceInputError("alt", "identical", "alt equals ref")
    return r, a


def validate_pos(value: object) -> int:
    if type(value) is int:
        pos = value
    elif type(value) is str and value.isascii() and value.isdigit():
        try:
            pos = int(value)
        except ValueError as exc:  # interpreter digit-limit on very long strings
            raise SpliceInputError("pos", "range", "integer has too many digits") from exc
    else:
        raise SpliceInputError("pos", "type", "must be an integer (digits only)")
    if pos < F + 1:
        raise SpliceInputError("pos", "range", f"must be >= {F + 1} (1-based, needs {F} bases upstream)")
    return pos


def validate_chrom(value: object) -> str:
    if type(value) is not str or not value or any(c.isspace() for c in value):
        raise SpliceInputError("chrom", "format", "must be a non-empty string without whitespace")
    return value


def validate_genome_row(chrom: object, pos: object, ref: object, alt: object) -> dict:
    r, a = validate_ref_alt(ref, alt)
    return {"chrom": validate_chrom(chrom), "pos": validate_pos(pos), "ref": r, "alt": a}


def _ctx(value: object, field: str) -> str:
    if type(value) is not str:
        raise SpliceInputError(field, "type", "must be a string")
    if len(value) != CTX_LEN:
        raise SpliceInputError(field, "length", f"must be exactly {CTX_LEN} characters")
    s = value.upper()
    if not set(s) <= _CTX_ALPHABET:
        raise SpliceInputError(field, "alphabet", "must contain only A, C, G, T, N")
    return s


def validate_contexts(ref_ctx: object, alt_ctx: object) -> tuple[str, str]:
    r = _ctx(ref_ctx, "ref_ctx")
    a = _ctx(alt_ctx, "alt_ctx")
    if r[F] not in _BASES:
        raise SpliceInputError("ref_ctx", "center", f"center base at index {F} must be A, C, G or T")
    if a[F] not in _BASES:
        raise SpliceInputError("alt_ctx", "center", f"center base at index {F} must be A, C, G or T")
    if r[:F] != a[:F] or r[F + 1:] != a[F + 1:]:
        raise SpliceInputError("alt_ctx", "flanks", "flanks must be identical to ref_ctx")
    if r[F] == a[F]:
        raise SpliceInputError("alt_ctx", "identical", f"center base at index {F} must differ from ref_ctx")
    return r, a


def validate_prior(value: object) -> float:
    if type(value) not in (int, float):
        raise SpliceInputError("prior", "type", "must be an int or float")
    try:
        p = float(value)
    except OverflowError as exc:  # int too large for a float
        raise SpliceInputError("prior", "range", "too large to be a float") from exc
    if not math.isfinite(p) or not (0.0 < p < 1.0):
        raise SpliceInputError("prior", "range", "must be finite with 0 < prior < 1")
    return p
