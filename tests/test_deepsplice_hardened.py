import math, random
from decimal import Decimal, getcontext
import pytest
from sugarcode.modules.deepsplice import core
from sugarcode.modules.deepsplice.hardened import (
    safe_branchpoint_variant_effect as bp, safe_variant_at as va, safe_exon_inclusion as ei,
    safe_isoform_distribution as iso, safe_active_learning as al, safe_intervention_simulation as sim)

NAN = float("nan")
W60 = "".join(random.Random(1).choice("ACGT") for _ in range(60))
REG = {"exon_definition_support": .5}
ALT30 = "A" if W60[30] != "A" else "C"


def test_red_core_defects():
    ref = core.branchpoint_variant_effect(W60, 30, ALT30)
    # index -1 and 100 are silently accepted: no error, a result is returned
    assert core.branchpoint_variant_effect(W60, -1, "A")["bp_applicable"] is True
    assert core.branchpoint_variant_effect(W60, 100, "A")["bp_applicable"] is True
    assert ref["bp_applicable"] is True
    assert core.variant_at("CAGGTAAGT", True, "A")["ref_base"] == "A"  # bool True treated as index 1
    with pytest.raises(OverflowError):
        core.exon_inclusion(.9, -1e6, REG)
    assert math.isnan(core.exon_inclusion(NAN, .5, REG)["psi"])
    d = core.isoform_distribution(2)["isoforms"]
    assert d["canonical"] == 2.0 and d["intron_retained"] < 0
    assert core.active_learning([{"probability": 2}])[0]["priority"] < 0
    assert core.intervention_simulation(.8, .2, [{"psi_shift": 5, "offtarget_risk": -3}])[0]["net_score"] > 1 - 0.2 - 0


@pytest.mark.parametrize("a", [(-1, "A"), (60, "A"), (100, "A"), (5, "AC"), (5, ""), (5, "N"), (True, "A"), (1.0, "A"), (5, None)])
def test_green_bp_rejects(a):
    with pytest.raises(ValueError):
        bp(W60, *a)


def test_green_bp_window_rejects():
    for w in ["ACGT", "N" * 60, None, W60 + "A"]:
        with pytest.raises(ValueError):
            bp(w, 5, "A")


@pytest.mark.parametrize("a", [(True, "A"), (1.0, "A"), (-1, "A"), (9, "A"), (0, "AC"), (0, "")])
def test_green_va_rejects(a):
    with pytest.raises(ValueError):
        va("CAGGTAAGT", *a)


@pytest.mark.parametrize("a", [(.9, -1e6, REG), (NAN, .5, REG), (.9, .5, None), (.9, .5, {}), (.9, .5, REG, 0), (.9, .5, REG, -5),
                               (.9, .5, REG, True), (True, .5, REG), (1e300, 0, REG)])
def test_green_ei_rejects(a):
    with pytest.raises(ValueError):
        ei(*a)


@pytest.mark.parametrize("kw", [dict(psi=2), dict(psi=-.5), dict(psi=NAN), dict(psi=True), dict(cryptic_strength=2),
                                dict(intron_retention=-1), dict(frame_preserved=1)])
def test_green_iso_rejects(kw):
    args = dict(psi=.5)
    args.update(kw)
    with pytest.raises(ValueError):
        iso(**args)


@pytest.mark.parametrize("c", [[{"probability": 2}], [{"probability": NAN}], [{"probability": .5, "impact": -1}], ["x"], "ab", [{}]])
def test_green_al_rejects(c):
    with pytest.raises(ValueError):
        al(c)


@pytest.mark.parametrize("a", [(.8, .2, [{"psi_shift": NAN}]), (.8, .2, [{"psi_shift": 5}]), (.8, .2, [{"offtarget_risk": -3}]),
                               (2, .2, []), (.8, .2, "x"), (.8, .2, [1])])
def test_green_sim_rejects(a):
    with pytest.raises(ValueError):
        sim(*a)


def test_green_bp_delta_oracle():
    out = bp(W60, 30, ALT30)
    alt = W60[:30] + ALT30 + W60[31:]
    assert len(alt) == 60
    assert out["alt_bp_score"] == pytest.approx(round(core._bp_raw(alt), 4))
    assert out["delta"] == pytest.approx(round(-.25 * out["bp_drop_bits"], 4), abs=1e-4)
    same = bp(W60, 30, W60[30])
    assert same["bp_drop_bits"] == 0 and same["delta"] == 0


def test_green_ei_decimal_oracle():
    getcontext().prec = 40
    ref, alt, sup = Decimal("0.9"), Decimal("0.5"), Decimal("0.5")
    logit_ref = Decimal("-0.5") + 5 * ref + 2 * sup
    logit = logit_ref + (alt - ref) * max(Decimal(5), logit_ref / Decimal("0.15"))
    psi = 1 / (1 + (-logit).exp())
    assert ei(0.9, 0.5, REG, 200)["psi"] == pytest.approx(float(psi), rel=1e-9)


def test_green_iso_sums_to_one_and_hand_oracle():
    out = iso(.6, True, .5, .05)["isoforms"]
    assert out["canonical"] == .6 and out["cryptic_site"] == pytest.approx(.5 * .4)
    assert out["intron_retained"] == pytest.approx(.05) and sum(out.values()) == pytest.approx(1)
    assert out["exon_skipped"] == pytest.approx(1 - .6 - .2 - .05)


def test_green_active_learning_and_sim_oracle():
    r = al([{"probability": .5, "impact": 1}, {"probability": .9, "impact": 1}])
    assert [x["probability"] for x in r] == [.5, .9] and r[0]["priority"] == pytest.approx(1.0)
    s = sim(.8, .2, [{"psi_shift": .6, "offtarget_risk": .1}, {"psi_shift": .1, "offtarget_risk": 0}])
    assert s[0]["restored_psi"] == pytest.approx(.8) and s[0]["net_score"] == pytest.approx(1 - 0 - .1)


def test_v2_admitted_extreme_exon_inclusion_no_overflow():
    # auditor case: passes the input limits, core.exon_inclusion raises OverflowError here
    out = ei(10, -10, {"exon_definition_support": 100})
    assert 0 <= out["psi"] <= 1 and math.isfinite(out["psi"])
    with pytest.raises(OverflowError):
        core.exon_inclusion(10, -10, {"exon_definition_support": 100})
    # equals core wherever core is defined
    for r, a, s in [(.9, .5, .5), (.2, .9, -3), (-1, 1, 50)]:
        assert ei(r, a, {"exon_definition_support": s})["psi"] == pytest.approx(core.exon_inclusion(r, a, {"exon_definition_support": s})["psi"], rel=1e-12)


def test_v2_boundary_sweep_only_valueerror_or_finite():
    import itertools
    E = [-10.0, -1e-9, 0.0, 1e-9, .5, 1.0, 10.0]
    P = [0.0, 1e-12, .5, 1 - 1e-12, 1.0]

    def fin(x):
        if isinstance(x, dict):
            return all(fin(v) for v in x.values())
        if isinstance(x, (list, tuple)):
            return all(fin(v) for v in x)
        return not isinstance(x, float) or math.isfinite(x)

    calls = []
    for r, a, s, n in itertools.product(E, E, [-100.0, 0, 100.0, .5], [1, 10**9]):
        calls.append((ei, (r, a, {"exon_definition_support": s}, n)))
    for p, c, i, fp in itertools.product(P, P, P, [True, False]):
        calls.append((iso, (p, fp, c, i)))
    for p, i in itertools.product(P, [0.0, .5, 1e6]):
        calls.append((al, ([{"probability": p, "impact": i}],)))
    for w, a, s, o in itertools.product(P, P, [-1.0, 0, 1.0], [0.0, .5, 1.0]):
        calls.append((sim, (w, a, [{"psi_shift": s, "offtarget_risk": o}])))
    for i, b in itertools.product([0, 29, 59], "ACGT"):
        calls.append((bp, (W60, i, b)))
    for st, win in (("donor", "CAGGTAAGT"), ("acceptor", "TTTTTTTTTTCCAGG")):
        for i, b in itertools.product(range(len(win)), "ACGT"):
            calls.append((va, (win, i, b, st)))
    bad = []
    for f, a in calls:
        try:
            out = f(*a)
        except ValueError:
            continue
        except Exception as e:  # any other exception type is a defect
            bad.append((f.__name__, a, type(e).__name__))
            continue
        if not fin(out):
            bad.append((f.__name__, a, "nonfinite"))
    assert not bad, bad[:5]
