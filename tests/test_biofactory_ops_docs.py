"""Docstring/constant agreement for biofactory_1_a (PARTIAL: text check only).
Limits are choices made in this wrapper, not spec values."""
import re
from sugarcode.modules.biofactory_1_a import boundary_ops as M

EXTRA = ["kp, ki and kd in 0..1000", "NEGATIVE GAINS ARE REFUSED", "dt in 1e-6..1e6"]


def _consts():
    return {n: v for n, v in vars(M).items()
            if re.fullmatch(r"_?[A-Z][A-Z_0-9]*", n) and isinstance(v, (int, float))
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
    assert [s for s in EXTRA if s not in M.__doc__] == []


def test_states_limits_are_choices_not_spec():
    assert "not spec values" in M.__doc__
