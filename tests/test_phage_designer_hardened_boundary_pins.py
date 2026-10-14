"""Unit 68 wrapper boundary pins (PARTIAL): hardened.py survivors IDs 8,10,38-40,44,51,55,56,67,68,72,73,84,87,94,106,117,118.

Oracles: Fraction/Decimal exact arithmetic (independent of the module's code path) and hand-derived literals.
Caps in the wrapper boundary tests are the module's own constants, not spec values.
"""
import math
from decimal import Decimal as D, localcontext
from fractions import Fraction

import pytest

from sugarcode.modules.phage_designer import core, hardened as h, kinetics_exact as kx

@pytest.fixture(autouse=True)
def decimal_oracle_context():
    with localcontext() as context:
        context.prec = 80
        yield
NAN, INF = float("nan"), float("inf")


def rel(a, b, tol=1e-14):
    return abs(D(a) - b) <= D(tol) * abs(b)


# ---- wrapper boundaries (hardened.py survivors IDs 8,10,38-40,44,51,55,56,67,68,72,73,84,87,94,106,117,118) ----
def test_adsorption_default_time_is_sixty():
    r = h.safe_adsorption_kinetics(1.0, 2.0, 0.01)       # x = .01*2*60 = 1.2
    assert r["time_min"] == 60
    assert rel(r["adsorbed_fraction"], 1 - (-D("1.2")).exp(), 1e-14)
    # 0.6988057880877... literal
    assert r["adsorbed_fraction"] == pytest.approx(0.6988057880877, abs=1e-12)


@pytest.mark.parametrize("bad", [NAN, INF, -INF])
def test_non_finite_numbers_refused_with_finite_message(bad):
    with pytest.raises(ValueError, match="phage: must be finite"):
        h.safe_adsorption_kinetics(bad, 1.0, 1.0, 1.0)


def test_phage_zero_refused_by_open_lower_bound_message():
    with pytest.raises(ValueError, match=r"^phage: must be in \(0\.0, 1e\+18\]"):
        h.safe_adsorption_kinetics(0.0, 1.0, 1.0, 1.0)
    assert h.safe_adsorption_kinetics(1e-300, 0.0, 1.0, 1.0)["bound"] == 0.0   # tiny positive is accepted
    with pytest.raises(ValueError, match=r"^bacteria: must be in \[0\.0"):
        h.safe_adsorption_kinetics(1.0, -1e-9, 1.0, 1.0)                        # closed lower bound still rejects negatives
    assert h.safe_adsorption_kinetics(1.0, 0.0, 1.0, 1.0)["bound"] == 0.0        # closed lower bound accepts 0


def test_adsorption_upper_caps_inclusive_and_exact():
    assert h.safe_adsorption_kinetics(1.0, 0.0, 1e6, 0.0)["adsorbed_fraction"] == 0.0
    assert h.safe_adsorption_kinetics(1.0, 0.0, 0.0, 1e6)["time_min"] == 1e6
    with pytest.raises(ValueError, match="k_ads: must be in"):
        h.safe_adsorption_kinetics(1.0, 1.0, 1000001.0, 1.0)
    with pytest.raises(ValueError, match="time_min: must be in"):
        h.safe_adsorption_kinetics(1.0, 1.0, 1.0, 1000001.0)


def test_population_cap_inclusive_1e15():
    assert h.safe_escape_probability(0.0, 1.0, 1e15)["escape_probability"] == 0.0
    with pytest.raises(ValueError, match="population: must be in"):
        h.safe_escape_probability(0.0, 1.0, 1000000000000001.0)


def test_core_fault_injection_is_refused_with_provenance(monkeypatch):
    bad_outputs = [{"escape_probability": 1.5, "expected_escape_variants": 1.0},
                   {"escape_probability": -1e-12, "expected_escape_variants": 1.0},
                   {"escape_probability": 0.5, "expected_escape_variants": INF},
                   {"escape_probability": NAN, "expected_escape_variants": 0.0}]
    for out in bad_outputs:
        monkeypatch.setattr(core, "escape_probability", lambda m, s, n, out=out: out)
        with pytest.raises(ValueError, match="non-finite or out-of-range output refused"):
            h.safe_escape_probability(0.1, 1, 1)
    monkeypatch.setattr(core, "escape_probability", lambda m, s, n: {"escape_probability": 1.0, "expected_escape_variants": 1.0})
    assert h.safe_escape_probability(0.1, 1, 1)["escape_probability"] == 1.0     # exactly 1.0 is in range
    monkeypatch.setattr(core, "escape_probability", lambda m, s, n: {"escape_probability": 0.0, "expected_escape_variants": 0.0})
    assert h.safe_escape_probability(0.1, 1, 1)["escape_probability"] == 0.0
    monkeypatch.setattr(core, "adsorption_kinetics", lambda *a: {"bound": NAN, "free": 1.0})
    with pytest.raises(ValueError, match="^non-finite output refused$"):
        h.safe_adsorption_kinetics(1.0, 1.0, 1.0, 1.0)
    monkeypatch.setattr(core, "host_range", lambda p, d: {"strain_scores": {"s": INF}, "predicted_hosts": []})
    with pytest.raises(ValueError, match="^non-finite output refused$"):
        h.safe_host_range({"s": {"OmpC": 1.0}}, {"target_receptor": "OmpC", "predicted_adsorption_rate": 0.5})
    monkeypatch.undo()
    real = core.phage_report
    monkeypatch.setattr(core, "phage_report", lambda r, p: dict(real(r, p), escape={"escape_probability": NAN}))
    with pytest.raises(ValueError, match="^non-finite output refused$"):
        h.safe_phage_report("OmpC", {"s": {"OmpC": 1.0}})


def test_receptor_profile_entry_cap_100_inclusive():
    ok = {"s": {"r%d" % i: 0.5 for i in range(100)}}
    out = h.safe_host_range(ok, {"target_receptor": "r0", "predicted_adsorption_rate": 0.5})
    assert out["strain_scores"] == {"s": 0.25}
    over = {"s": {"r%d" % i: 0.5 for i in range(101)}}
    with pytest.raises(ValueError, match=r"^receptor_profile: \{strain\(str\)"):
        h.safe_host_range(over, {"target_receptor": "r0", "predicted_adsorption_rate": 0.5})


def test_predicted_hosts_cap_1000_inclusive():
    hosts = ["s%d" % i for i in range(1000)]
    out = h.safe_cocktail_design([{"target_receptor": "OmpC", "predicted_hosts": hosts}], hosts[:3])
    assert out["covered_fraction"] == 1.0
    with pytest.raises(ValueError, match="^phage predicted_hosts: list of str required$"):
        h.safe_cocktail_design([{"target_receptor": "OmpC", "predicted_hosts": hosts + ["x"]}], hosts[:3])


def test_phage_report_receptor_message_is_its_own():
    with pytest.raises(ValueError, match=r"^receptor: must be one of"):
        h.safe_phage_report("not-a-receptor", {"s": {"OmpC": 1.0}})

