import math
from decimal import Decimal as D, localcontext
from fractions import Fraction
import pytest
from sugarcode.modules.phage_designer import core, hardened as h

NAN, INF = float("nan"), float("inf")
@pytest.fixture(autouse=True)
def decimal_oracle_context():
    with localcontext() as context:
        context.prec = 60
        yield


def test_core_defects_documented():  # raw core behaviour on b363c3b
    steps = core.design_fiber("OmpC", "Escherichia_coli")["engineering"]
    assert "{host_pathogen}" in steps[2] and "{target_receptor}" in steps[2]  # missing f-prefix
    assert core.design_lysin("gram?")["gram_type"] == "gram?"  # unknown gram type silently scored as gram+
    assert core.design_lysin("gram+", ["CHAP", "CHAP"])["domains"] == ["CHAP", "CHAP"]
    assert math.isnan(core.escape_probability(NAN, 1, 1)["escape_probability"])
    assert core.escape_probability(-1e-6, 1, 1e8)["escape_probability"] < 0
    with pytest.raises(OverflowError):
        core.escape_probability(1e-6, 10**9, 10**400)
    assert math.isnan(core.adsorption_kinetics(INF, 1, 1)["free"])
    with pytest.raises(AttributeError):
        core.host_range(5, {"target_receptor": "OmpC", "predicted_adsorption_rate": .5})
    with pytest.raises(KeyError):
        core.host_range({"s": {"OmpC": 1}}, {})


def test_fiber_placeholders_filled_and_formula_oracle():
    for rec, b in core.RECEPTOR_BINDERS.items():
        out = h.safe_design_fiber(rec, "Pseudomonas_aeruginosa")
        assert "{" not in "".join(out["engineering"])
        assert "Pseudomonas_aeruginosa lawns expressing " + rec in out["engineering"][2]
        assert out["predicted_adsorption_rate"] == float(min(Fraction(99, 100), Fraction(55, 100) + Fraction(12, b["affinity_nM"]))).__round__(3)
        assert out["predicted_binding_nM"] == b["affinity_nM"]
        assert out["off_target_risk"] == ("low" if b["affinity_nM"] < 30 else "moderate")
        assert out["scaffold"] == core.FIBER_SCAFFOLDS[b["scaffold"]]


def test_lysin_matches_fraction_potency():
    fit = {"gram+": {"CHAP": 1, "endopeptidase": 1, "amidase": Fraction(4, 5), "glycosidase": Fraction(3, 5)},
           "gram-": {"CHAP": Fraction(1, 5), "endopeptidase": Fraction(1, 5), "amidase": Fraction(9, 10), "glycosidase": Fraction(9, 10)}}
    act = {"CHAP": Fraction(9, 10), "glycosidase": Fraction(7, 10), "amidase": Fraction(4, 5), "endopeptidase": Fraction(3, 4)}
    for g in ("gram+", "gram-"):
        for doms in (["CHAP"], ["CHAP", "amidase"], ["glycosidase", "amidase", "CHAP", "endopeptidase"], None):
            out = h.safe_design_lysin(g, doms)
            use = doms or ["CHAP", "amidase"]
            pot = sum(act[d] * fit[g][d] for d in use) / len(use)
            assert out["predicted_potency"] == pytest.approx(float(pot), abs=5e-4)
            assert out["MIC_estimate_ug_mL"] == pytest.approx(max(0.1, 8 * (1.1 - float(round(float(pot), 3)))), abs=6e-3)
            assert out["domains"] == use


def test_adsorption_matches_decimal():
    for ph, b, k, t in [(1e6, 1e8, 1e-9, 60), (1e9, 1e7, 2.5e-10, 15.5), (5, 1, 1e-3, 0.5), (1e18, 1e18, 1e6, 1e6), (100, 0, 1, 10), (100, 5, 0, 10), (100, 5, 1, 0)]:
        out = h.safe_adsorption_kinetics(ph, b, k, t)
        frac = 1 - (-D(k) * D(b) * D(t)).exp()
        assert out["adsorbed_fraction"] == pytest.approx(float(frac), rel=1e-9, abs=1e-15)
        assert out["bound"] + out["free"] == pytest.approx(ph, rel=1e-12)
        assert 0 <= out["adsorbed_fraction"] <= 1


def test_escape_matches_decimal():
    for m, s, n in [(1e-8, 1, 1e8), (1e-9, 3, 1e12), (1.0, 1e6, 1e15), (0, 5, 5), (1e-7, 0, 1e9), (0.5, 2, 3)]:
        out = h.safe_escape_probability(m, s, n)
        x = D(m) * D(s) * D(n)
        assert out["expected_escape_variants"] == pytest.approx(float(x), rel=1e-12)
        assert out["escape_probability"] == pytest.approx(float(1 - (-x).exp()), rel=1e-9, abs=1e-15)


def test_host_range_matches_independent_scores_and_cocktail_coverage():
    d = h.safe_design_fiber("OmpC")
    prof = {"s1": {"OmpC": 1.0}, "s2": {"OmpC": 0.2, "LamB": 1.0}, "s3": {}, "s4": {"OmpC": 0.5}}
    out = h.safe_host_range(prof, d)
    r = d["predicted_adsorption_rate"]
    for s, e in prof.items():
        assert out["strain_scores"][s] == pytest.approx(e.get("OmpC", 0) * r)
    assert out["predicted_hosts"] == [s for s, e in prof.items() if e.get("OmpC", 0) * r > .3]
    ph = [{"target_receptor": "OmpC", "predicted_hosts": ["s1", "s4"]}, {"target_receptor": "LamB", "predicted_hosts": ["s1", "s2"]}]
    cd = h.safe_cocktail_design(ph, ["s1", "s2", "s3", "s4"])
    assert cd["coverage"] == {"s1": ["OmpC", "LamB"], "s2": ["LamB"], "s3": [], "s4": ["OmpC"]}
    assert cd["covered_fraction"] == 0.75 and cd["redundant_hosts"] == ["s1"]
    rep = h.safe_phage_report("LamB", prof)
    assert "{" not in "".join(rep["engineering"]) and rep["host_range"]["predicted_hosts"] == out_hosts("LamB", prof)


def out_hosts(rec, prof):
    r = h.safe_design_fiber(rec)["predicted_adsorption_rate"]
    return [s for s, e in prof.items() if e.get(rec, 0) * r > .3]


# ---- refusals ----
@pytest.mark.parametrize("rec", [None, 5, [], {}, b"OmpC", "ompC", "", "Unknown"])
def test_receptor_refused(rec):
    with pytest.raises(ValueError, match="receptor"):
        h.safe_design_fiber(rec)
    with pytest.raises(ValueError, match="receptor"):
        h.safe_phage_report(rec, {})


@pytest.mark.parametrize("host", [None, 5, "", "   ", "x" * 201, b"E", ["E"]])
def test_host_refused(host):
    with pytest.raises(ValueError, match="host_pathogen"):
        h.safe_design_fiber("OmpC", host)


def test_host_edge():
    assert "x" * 200 in h.safe_design_fiber("OmpC", "x" * 200)["engineering"][2]


@pytest.mark.parametrize("g", [None, 5, "gram", "gram+/-", "", "GRAM+", [], b"gram+"])
def test_gram_refused(g):
    with pytest.raises(ValueError, match="gram_type"):
        h.safe_design_lysin(g)


@pytest.mark.parametrize("dom", [[], "CHAP", b"CHAP", {"CHAP": 1}, {"CHAP"}, ["nope"], ["CHAP", "CHAP"], [["CHAP"]], [None], ["CHAP", 5], list(core.LYSIN_DOMAINS) + ["CHAP"], 5])
def test_domains_refused(dom):
    with pytest.raises(ValueError):
        h.safe_design_lysin("gram+", dom)


def test_domains_edges_ok():
    h.safe_design_lysin("gram-", tuple(core.LYSIN_DOMAINS))
    h.safe_design_lysin("gram+", ["endopeptidase"])


ADS = dict(phage=1e6, bacteria=1e8, k_ads=1e-9, time_min=60)


@pytest.mark.parametrize("key,bad", [(k, v) for k in ADS for v in (NAN, INF, -INF, True, "1", None, 10**400, -1e-9)] + [("phage", 0), ("phage", 1e18 * 1.0001), ("bacteria", 1e18 * 1.0001),
                                                                                   ("k_ads", 1e6 * 1.0001), ("time_min", 1e6 * 1.0001)])
def test_adsorption_refused(key, bad):
    with pytest.raises(ValueError):
        h.safe_adsorption_kinetics(**{**ADS, key: bad})


def test_adsorption_edges_ok():
    h.safe_adsorption_kinetics(1e-300, 0, 0, 0)
    h.safe_adsorption_kinetics(1e18, 1e18, 1e6, 1e6)


@pytest.mark.parametrize("args", [(NAN, 1, 1), (INF, 1, 1), (-1e-9, 1, 1), (1.0000001, 1, 1), (True, 1, 1), ("1", 1, 1), (None, 1, 1), (1e-8, -1, 1), (1e-8, 1e6 + 1, 1),
                                  (1e-8, 1, -1), (1e-8, 1, 1e15 * 1.0001), (1e-8, 1, NAN), (1e-8, 10**400, 1), (1e-8, 1, 10**400), (1e-8, 1, True)])
def test_escape_refused(args):
    with pytest.raises(ValueError):
        h.safe_escape_probability(*args)


def test_escape_edges_ok():
    assert h.safe_escape_probability(0, 0, 0)["escape_probability"] == 0.0
    assert h.safe_escape_probability(1, 1e6, 1e15)["escape_probability"] == 1.0


GOOD = {"target_receptor": "OmpC", "predicted_adsorption_rate": .9}


@pytest.mark.parametrize("args", [(5, GOOD), (None, GOOD), ([], GOOD), ({"s": 5}, GOOD), ({"s": {"OmpC": NAN}}, GOOD), ({"s": {"OmpC": 1.5}}, GOOD), ({"s": {"OmpC": -.1}}, GOOD),
                                  ({"s": {"OmpC": True}}, GOOD), ({"s": {1: .5}}, GOOD), ({5: {"OmpC": .5}}, GOOD), ({"s": {"OmpC": "1"}}, GOOD), ({"s": {}}, None), ({"s": {}}, {}),
                                  ({"s": {}}, {"target_receptor": "OmpC"}), ({"s": {}}, {"target_receptor": 5, "predicted_adsorption_rate": .5}),
                                  ({"s": {}}, {"target_receptor": "OmpC", "predicted_adsorption_rate": NAN}), ({"s": {}}, {"target_receptor": "OmpC", "predicted_adsorption_rate": 1.1}),
                                  ({"s": {}}, {"target_receptor": "OmpC", "predicted_adsorption_rate": True}), ({f"s{i}": {} for i in range(1001)}, GOOD)])
def test_host_range_refused(args):
    with pytest.raises(ValueError):
        h.safe_host_range(*args)


def test_host_range_edges_ok():
    h.safe_host_range({f"s{i}": {} for i in range(1000)}, GOOD)
    h.safe_host_range({"s": {"OmpC": 0.0}}, {**GOOD, "predicted_adsorption_rate": 0.0})
    assert h.safe_host_range({"s": {"OmpC": 1.0}}, {**GOOD, "predicted_adsorption_rate": 1.0})["predicted_hosts"] == ["s"]


@pytest.mark.parametrize("args", [(None, ["s"]), ([], ["s"]), ("x", ["s"]), ([5], ["s"]), ([{}], ["s"]), ([{"target_receptor": 5}], ["s"]), ([{"target_receptor": "a", "predicted_hosts": "s1"}], ["s"]),
                                  ([{"target_receptor": "a", "predicted_hosts": [5]}], ["s"]), ([{"target_receptor": "a"}], None), ([{"target_receptor": "a"}], []), ([{"target_receptor": "a"}], "abc"),
                                  ([{"target_receptor": "a"}], [5]), ([{"target_receptor": "a"}], ["s", "s"]), ([{"target_receptor": "a"}] * 101, ["s"]), ([{"target_receptor": "a"}], [f"s{i}" for i in range(1001)])])
def test_cocktail_refused(args):
    with pytest.raises(ValueError):
        h.safe_cocktail_design(*args)


def test_cocktail_edges_ok():
    h.safe_cocktail_design([{"target_receptor": "a"}] * 100, [f"s{i}" for i in range(1000)])
    assert h.safe_cocktail_design([{"target_receptor": "a"}], ["s"])["covered_fraction"] == 0.0
