"""Docstring/constant agreement for openclinvar/boundary.py (PARTIAL: text check only).
Every module-level numeric constant must be named, with its value, in the module
docstring; extra literal limits are listed explicitly.  Limits are choices made
in this wrapper, not spec values."""
import re
from sugarcode.modules.openclinvar import boundary as M

EXTRA = ["out of scope", "prior in [1e-6, 1 - 1e-6]", "age <= 120", "years 1900..2026", "penetrance, quality, variant_probability in [0, 1]", "supporting <= total", "prior_alpha and prior_beta in MIN_PRIOR..MAX_COUNT", "computed beta <= 0 after\n  float cancellation", "total and supporting in 0..MAX_COUNT", "TypeError for bool", "duplicate phenotype or pathway terms", "duplicate graph node ids"]


def _consts():
    return {n: v for n, v in vars(M).items()
            if re.fullmatch(r"_?[A-Z][A-Z_]*", n) and isinstance(v, (int, float))
            and not isinstance(v, bool)}


def test_every_numeric_constant_named_with_value():
    doc = M.__doc__
    missing = []
    for n, v in _consts().items():
        m = re.search(re.escape(n) + r"\s*=\s*([0-9][0-9_.e+]*)", doc)
        if not m or float(m.group(1).rstrip(".").replace("_", "")) != float(v):
            missing.append(n)
    assert not missing, missing
    assert _consts()


def test_extra_literal_limits_present():
    doc = M.__doc__
    assert [s for s in EXTRA if s not in doc] == []


def test_states_limits_are_choices_not_spec():
    assert "not spec values" in M.__doc__
