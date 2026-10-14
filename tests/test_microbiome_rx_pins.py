"""microbiome_rx second-look pins (tests only, PARTIAL). An independent sweep showed the existing 13 tests leave most
constants of the toy gLV/metabolite model unpinned. Oracles here: (1) hand-computed closed forms (_metabolites, _shift,
validation), (2) independent fixed-step RK4 re-implementations of the two ODE right-hand sides written from the model
equations (not calling the module's solver), (3) the module's own tables as literals. Toy simulation arithmetic only:
no clinical, diagnostic or wet-lab claim. Values depend on the model as coded; they are regression pins, not validation."""
import math
import numpy as np
import pytest
from sugarcode.modules.microbiome_rx import core
from sugarcode.modules.microbiome_rx import (simulate_community, simulate_metabolic_community, validate_community,
                                              design_intervention, optimize_intervention)

C6 = {"Faecalibacterium": .1, "Bacteroides": .2, "Escherichia": .1, "Lactobacillus": .15, "Akkermansia": .1,
      "Bifidobacterium": .2}
METS = ("fiber", "sugar", "mucin", "oxygen", "acetate", "butyrate", "lactate", "succinate", "propionate")


def test_tables_are_pinned_literals():
    assert core.METABOLITES == METS
    assert core.SPECIES_TRAITS == {
        "Faecalibacterium": {"growth": 0.3, "consumes": ["acetate"], "produces": ["butyrate"]},
        "Bacteroides": {"growth": 0.4, "consumes": ["fiber"], "produces": ["acetate", "succinate"]},
        "Escherichia": {"growth": 0.6, "consumes": ["sugar", "oxygen"], "produces": ["lactate"]},
        "Lactobacillus": {"growth": 0.5, "consumes": ["sugar"], "produces": ["lactate"]},
        "Akkermansia": {"growth": 0.2, "consumes": ["mucin"], "produces": ["propionate"]},
        "Bifidobacterium": {"growth": 0.4, "consumes": ["fiber", "sugar"], "produces": ["acetate"]}}
    assert core.INTERACTIONS == {("Faecalibacterium", "Bacteroides"): 0.3, ("Faecalibacterium", "Bifidobacterium"): 0.25,
                                 ("Escherichia", "Lactobacillus"): -0.1, ("Bacteroides", "Escherichia"): -0.2}


def rk4(f, y, t1, h):
    n = int(round(t1 / h))
    for _ in range(n):
        k1 = f(y); k2 = f(y + h / 2 * k1); k3 = f(y + h / 2 * k2); k4 = f(y + h * k3)
        y = y + h / 6 * (k1 + 2 * k2 + 2 * k3 + k4)
    return y


def ref_metabolic(initial, days, diet=None, abx=None, h=0.005):
    d = {"fiber": 1., "sugar": 1., "mucin": .5, "oxygen": .1, **(diet or {})}
    sp = list(initial); abx = abx or {}
    y0 = np.array([initial[s] for s in sp] + [d.get(m, 0) for m in METS], float)
    S = len(sp)
    def f(y):
        X = np.maximum(y[:S], 0); M = dict(zip(METS, np.maximum(y[S:], 0)))
        dm = {m: .02 * (d.get(m, 0) - M[m]) for m in METS}; dx = []
        for i, s in enumerate(sp):
            tr = core.SPECIES_TRAITS[s]
            lim = sum(M[m] / (1 + M[m]) for m in tr["consumes"]) / len(tr["consumes"])
            inter = sum(core.INTERACTIONS.get((s, o), 0) * X[j] for j, o in enumerate(sp))
            rate = X[i] * (tr["growth"] * lim + inter - .08 * X.sum() - abx.get(s, 0))
            dx.append(rate)
            for m in tr["consumes"]: dm[m] -= .15 * max(rate, 0) / len(tr["consumes"])
            for m in tr["produces"]: dm[m] += .12 * max(rate, 0) / len(tr["produces"])
        return np.array(dx + [dm[m] for m in METS])
    y = rk4(f, y0, days, h)
    return {s: max(0.0, y[i]) for i, s in enumerate(sp)}, {m: max(0.0, y[S + i]) for i, m in enumerate(METS)}


@pytest.mark.parametrize("kw", [dict(), dict(diet={"fiber": 2.0, "sugar": .3, "butyrate": .4}),
                                dict(antibiotic_effects={"Escherichia": .3, "Bacteroides": .1})])
def test_metabolic_ode_matches_independent_rk4(kw):
    sim = simulate_metabolic_community(C6, days=2, **kw)
    sp, mt = ref_metabolic(C6, 2, kw.get("diet"), kw.get("antibiotic_effects"))
    fin = sim["trajectory"][-1]
    for s in C6:
        assert fin["species"][s] == pytest.approx(sp[s], abs=2e-6, rel=1e-5)
    for m in METS:
        assert sim["final_metabolites"][m] == pytest.approx(mt[m], abs=2e-6, rel=1e-5)
    tot = sum(sp.values())
    for s in C6:
        assert sim["final_relative"][s] == pytest.approx(sp[s] / tot, abs=2e-6)


def test_metabolic_trajectory_grid_and_initial_row_and_status():
    sim = simulate_metabolic_community(C6, days=1)
    assert [r["day"] for r in sim["trajectory"]] == [0.0, .25, .5, .75, 1.0]
    r0 = sim["trajectory"][0]
    assert r0["species"] == {s: float(v) for s, v in C6.items()}
    assert r0["metabolites"] == {"fiber": 1.0, "sugar": 1.0, "mucin": .5, "oxygen": .1, "acetate": 0.0, "butyrate": 0.0,
                                 "lactate": 0.0, "succinate": 0.0, "propionate": 0.0}
    assert sim["solver"]["method"] == "BDF" and sim["solver"]["success"] is True and sim["solver"]["nfev"] > 0
    assert sim["model_status"] == "mechanistic hermetic community-metabolite ODE; no clinical response claim"
    odd = simulate_metabolic_community(C6, days=1, sample_hours=7)
    assert [round(r["day"], 6) for r in odd["trajectory"]] == [0.0, round(7 / 24, 6), round(14 / 24, 6), round(21 / 24, 6), 1.0]
    one = simulate_metabolic_community(C6, days=0.5, sample_hours=24)
    assert [r["day"] for r in one["trajectory"]] == [0.0, 0.5]
    assert sum(sim["final_relative"].values()) == pytest.approx(1.0, abs=1e-12)
    d = simulate_metabolic_community({"Bacteroides": 1.0}, days=1, diet={"fiber": 0.0, "sugar": 0.0, "mucin": 0.0, "oxygen": 0.0})
    assert d["trajectory"][0]["metabolites"]["fiber"] == 0.0


def err(fn, *a, **k):
    with pytest.raises(ValueError) as e:
        fn(*a, **k)
    return str(e.value)


def test_validation_messages_and_branches():
    assert err(validate_community, {}, {}) == "initial community must be non-empty"
    assert err(validate_community, [("Bacteroides", 1)], {}) == "initial community must be non-empty"
    assert err(validate_community, {"bad": 1, "Bacteroides": 1}, {}) == "unknown species: ['bad']"
    m = "species abundances must be non-negative with positive total"
    assert err(validate_community, {"Bacteroides": -0.1, "Escherichia": 5}, {}) == m
    assert err(validate_community, {"Bacteroides": "1"}, {}) == m
    assert err(validate_community, {"Bacteroides": 0, "Escherichia": 0}, {}) == m
    d = "diet must use known metabolites with non-negative values"
    assert err(validate_community, {"Bacteroides": 1}, {"zzz": 1}) == d
    assert err(validate_community, {"Bacteroides": 1}, {"fiber": -0.1}) == d
    assert err(validate_community, {"Bacteroides": 1}, {"fiber": "1"}) == d
    assert validate_community({"Bacteroides": 0, "Escherichia": 2}, {"fiber": 0}) == ({"Bacteroides": 0.0, "Escherichia": 2.0}, {"fiber": 0.0})
    out = validate_community({"Bacteroides": 1}, {"fiber": 2})
    assert all(type(v) is float for part in out for v in part.values())


def test_simulation_argument_messages():
    for kw in (dict(days=0), dict(days=-1), dict(sample_hours=0), dict(sample_hours=-6)):
        assert err(simulate_metabolic_community, C6, **kw) == "days and sample_hours must be positive"
    m = "antibiotic effects must map present species to [0,1]"
    assert err(simulate_metabolic_community, C6, days=1, antibiotic_effects={"Bacteroides": 1.01}) == m
    assert err(simulate_metabolic_community, C6, days=1, antibiotic_effects={"Bacteroides": -0.01}) == m
    assert err(simulate_metabolic_community, C6, days=1, antibiotic_effects={"Nope": 0.5}) == m
    simulate_metabolic_community(C6, days=1, antibiotic_effects={"Bacteroides": 1.0, "Escherichia": 0.0})


def test_metabolites_closed_form():
    f = core._metabolites(["Bacteroides", "Faecalibacterium", "Bifidobacterium"],
                          {"Bacteroides": 2.0, "Faecalibacterium": 1.0, "Bifidobacterium": 4.0}, {"fiber": 3.0})
    assert f == {"acetate": 9.0, "succinate": 3.0, "butyrate": 1.5}
    g = core._metabolites(["Bacteroides"], {"Bacteroides": 2.0}, {})
    assert g == {"acetate": 1.0, "succinate": 1.0}
    h = core._metabolites(["Escherichia"], {"Escherichia": 0.12345}, {"fiber": 1.0})
    assert h == {"lactate": 0.062}                      # 0.12345 * 0.5 = 0.061725 -> 0.062 (3 places)


def test_shift_closed_form():
    assert core._shift({"A": 1, "B": 3}, {"A": 2, "B": 2}) == {"A": 0.25, "B": -0.25}
    assert core._shift({"A": 1, "B": 1}, {"A": 2}) == {"A": 0.5, "B": -0.5}
    assert core._shift({"A": 1, "B": 2}, {"A": 3, "B": 3}) == {"A": 0.167, "B": -0.167}
    assert core._shift({"A": 0}, {"A": 0}) == {"A": 0.0}


def ref_legacy(initial, days, diet=None, abx=None, h=0.005):
    d = diet or {"fiber": 1.0, "sugar": 1.0}; sp = list(initial); abx = abx or {}
    def f(x):
        out = np.zeros_like(x)
        for i, s in enumerate(sp):
            tr = core.SPECIES_TRAITS[s]
            g = tr["growth"] * np.mean([d.get(c, 0.5) for c in tr["consumes"]])
            inter = sum(core.INTERACTIONS.get((s, o), 0.0) * x[j] for j, o in enumerate(sp))
            out[i] = x[i] * (g + inter - 0.1 * x[i] / 5 - abx.get(s, 0.0))
        return out
    return dict(zip(sp, rk4(f, np.array([initial[s] for s in sp], float), days, h)))


@pytest.mark.parametrize("abx,table", [(None, {}), ("amoxicillin", {"Bacteroides": .5, "Lactobacillus": .3, "Escherichia": .1}),
                                       ("ciprofloxacin", {"Escherichia": .7, "Bifidobacterium": .4}), ("unknown", {})])
def test_legacy_simulation_matches_rk4_and_shapes(abx, table):
    days = 3
    r = simulate_community(C6, days=days, antibiotic=abx)
    fin = ref_legacy(C6, days, abx=table)
    tot = sum(round(max(v, 0), 4) for v in fin.values())
    for s in C6:
        assert r["final_relative"][s] == pytest.approx(round(max(fin[s], 0), 4) / tot, abs=2e-3)
        assert r["trajectory"][s][-1] == pytest.approx(fin[s], abs=2e-3)
    assert r["trajectory"]["t_d"] == [0.0, 1.0, 2.0, 3.0] and r["days"] == 3 and r["antibiotic"] == abx
    assert r["diet"] == {"fiber": 1.0, "sugar": 1.0}


def test_legacy_defaults_and_grid():
    r = simulate_community(C6)
    assert r["days"] == 14 and r["trajectory"]["t_d"] == [float(i) for i in range(15)]
    assert len(r["trajectory"]["Bacteroides"]) == 15
    r2 = simulate_community(C6, days=2.5)
    assert r2["trajectory"]["t_d"] == [0.0, 1.0, 2.0] and len(r2["trajectory"]["Akkermansia"]) == 3
    d = simulate_community(C6, days=2, diet={"fiber": 2.0, "sugar": 0.2})
    fin = ref_legacy(C6, 2, diet={"fiber": 2.0, "sugar": 0.2})
    assert d["trajectory"]["Bifidobacterium"][-1] == pytest.approx(fin["Bifidobacterium"], abs=2e-3)
    assert sum(r["final_relative"].values()) == pytest.approx(1.0, abs=2e-3)
    fin4 = {s: round(float(max(v, 0)), 4) for s, v in zip(C6, [r["trajectory"][s][-1] for s in C6])}
    assert all(abs(r["dysbiosis_shift"][s] - core._shift(C6, fin4)[s]) <= 0.002 for s in C6)   # trajectory is rounded to 3 places


PROFILE = {"Faecalibacterium": 0.05, "Bacteroides": 0.2, "Escherichia": 0.4, "Lactobacillus": 0.1}


def test_design_intervention_structure_and_constants():
    r = design_intervention()
    assert r["condition"] == "dysbiosis" and r["rationale"] == "maximize butyrate producers while suppressing pro-inflammatory Enterobacteriaceae"
    base = simulate_community(PROFILE, days=7)
    assert r["baseline"] == {"metabolite_flux": base["metabolite_flux"], "final_relative": base["final_relative"]}
    opts = {"high-fiber diet (30g/d)": {"fiber": 2.0, "sugar": 0.5}, "inulin prebiotic": {"fiber": 1.6, "sugar": 0.8},
            "low-sugar diet": {"fiber": 1.0, "sugar": 0.3}}
    assert {o["intervention"]: o["diet"] for o in r["interventions_ranked"]} == opts
    scores = []
    for o in r["interventions_ranked"]:
        s = simulate_community(PROFILE, days=7, diet=o["diet"])
        b = s["metabolite_flux"].get("butyrate", 0); e = s["final_relative"].get("Escherichia", 0)
        assert o["butyrate_flux"] == b and o["escherichia_fraction"] == e and o["benefit_score"] == round(b - 0.5 * e, 3)
        scores.append(o["benefit_score"])
    assert scores == sorted(scores, reverse=True) and r["recommended"] == r["interventions_ranked"][0]
    r2 = design_intervention("mycondition", {"Bacteroides": 0.3, "Escherichia": 0.3})
    assert r2["condition"] == "mycondition"
    assert r2["baseline"]["final_relative"] == simulate_community({"Bacteroides": 0.3, "Escherichia": 0.3}, days=7)["final_relative"]


def test_optimizer_report_fields_are_self_consistent():
    tgt = {"butyrate": 0.05, "acetate": 0.1}
    r = optimize_intervention(C6, tgt, days=2)
    d = r["diet"]
    assert set(d) == {"fiber", "sugar"} and 0 <= d["fiber"] <= 3 and 0 <= d["sugar"] <= 3
    sim = simulate_metabolic_community(C6, days=2, diet=d, sample_hours=24)
    expect = sum((sim["final_metabolites"][m] - v) ** 2 for m, v in tgt.items()) + 1e-6 * (d["fiber"] + d["sugar"])
    assert r["objective"] == pytest.approx(expect, rel=1e-3, abs=1e-9)
    for m, v in tgt.items():
        t = r["target_vs_achieved"][m]
        assert t["target"] == v and t["achieved"] == r["simulation"]["final_metabolites"][m]
        assert t["abs_error"] == abs(t["achieved"] - v)
    assert r["solver"] == "differential_evolution" and isinstance(r["converged"], bool) and r["evaluations"] > 12
    assert r["simulation"]["trajectory"][-1]["day"] == 2.0 and r["simulation"]["trajectory"][1]["day"] == 0.25
    for bad in ({}, {"nope": 1}, None):
        assert err(optimize_intervention, C6, bad) == "target_metabolites must use known metabolites"


def trap(a, t):
    return float(sum((a[i] + a[i + 1]) / 2 * (t[i + 1] - t[i]) for i in range(len(t) - 1)))


def test_enhancement_features_values_and_keyset():
    sim = simulate_metabolic_community(C6, days=1)
    opt = {"objective": .25, "diet": {"fiber": 1.5, "sugar": 2.0}, "evaluations": 99}
    f = core.enhancement_features(sim, opt)
    rows = sim["trajectory"]; t = [r["day"] for r in rows]
    assert len(f) == 50 and f["duration_days"] == 1.0 and f["timepoint_count"] == 5
    assert f["solver_evaluations"] == sim["solver"]["nfev"] and f["species_count"] == 6 and f["metabolite_count"] == 9
    for s in C6:
        a = [r["species"][s] for r in rows]
        assert f[f"{s}_initial"] == a[0] and f[f"{s}_final"] == a[-1]
        assert f[f"{s}_fold_change"] == pytest.approx(a[-1] / max(a[0], 1e-12), rel=1e-12)
    for s in ("Akkermansia", "Bacteroides"):           # per-species AUC survive the trim only for the first two (sorted) species
        a = [r["species"][s] for r in rows]
        assert f[f"{s}_auc"] == pytest.approx(trap(a, t), rel=1e-12)
    assert not any(k.endswith("_auc") for k in f if k.split("_")[0] not in ("Akkermansia", "Bacteroides"))
    for m in METS:
        a = [r["metabolites"][m] for r in rows]
        assert f[f"{m}_final"] == a[-1] and f[f"{m}_change"] == pytest.approx(a[-1] - a[0], abs=1e-15)
    fin = list(sim["final_relative"].values())
    assert f["final_richness"] == sum(1 for v in fin if v > 1e-6)
    assert f["final_shannon"] == pytest.approx(-sum(v * math.log(v) for v in fin if v > 0), rel=1e-12)
    assert f["dominant_fraction"] == max(fin)
    assert (f["optimization_objective"], f["optimized_fiber"], f["optimized_sugar"], f["optimization_evaluations"]) == (.25, 1.5, 2.0, 99)
    assert not any(k.startswith("total_biomass") or k == "community_fold_change" for k in f)


def test_enhancement_features_four_species_adds_extras_three_species_refused():
    c4 = dict(list(C6.items())[:4])
    sim = simulate_metabolic_community(c4, days=1)
    opt = {"objective": .25, "diet": {"fiber": 1.5, "sugar": 2.0}, "evaluations": 99}
    f = core.enhancement_features(sim, opt)
    assert len(f) == 50
    rows = sim["trajectory"]; t = [r["day"] for r in rows]
    tot = [sum(r["species"].values()) for r in rows]
    assert f["total_biomass_initial"] == pytest.approx(tot[0], rel=1e-12)
    assert f["total_biomass_final"] == pytest.approx(tot[-1], rel=1e-12)
    assert f["total_biomass_peak"] == pytest.approx(max(tot), rel=1e-12)
    assert f["total_biomass_auc"] == pytest.approx(trap(tot, t), rel=1e-12)
    assert "community_fold_change" not in f                       # cap of 50 reached before the fifth extra
    c3 = dict(list(C6.items())[:3])
    assert err(core.enhancement_features, simulate_metabolic_community(c3, days=1), opt) == \
        "at least five species are required for 50-diagnostic community analysis"


def test_analyze_microbiome_constants():
    r = core.analyze_microbiome(C6, {"butyrate": .1}, days=1)
    assert r["diagnostic_count"] == 50 and len(r["diagnostics"]) == 50
    assert r["lab_plan"] == ["run anaerobic batch cultures", "quantify metabolites by LC-MS", "track species by shotgun metagenomics",
                             "test antibiotic and diet perturbations"]
    assert r["diagnostics"]["optimized_fiber"] == r["optimization"]["diet"]["fiber"]
    assert r["diagnostics"]["optimization_evaluations"] == r["optimization"]["evaluations"]


def test_default_arguments_pinned():
    import inspect
    assert inspect.signature(core.simulate_community).parameters["days"].default == 14
    assert inspect.signature(core.simulate_metabolic_community).parameters["days"].default == 14
    assert inspect.signature(core.simulate_metabolic_community).parameters["sample_hours"].default == 6
    assert inspect.signature(core.optimize_intervention).parameters["days"].default == 7
    assert inspect.signature(core.analyze_microbiome).parameters["days"].default == 7
    assert inspect.signature(core.design_intervention).parameters["condition"].default == "dysbiosis"


def test_legacy_rounding_places_and_missing_diet_default():
    r = simulate_community(C6, days=1.3)
    assert r["trajectory"]["t_d"] == [0.0, 1.04]                      # linspace(0, 1.3, 6)[::4], rounded to 2 places
    for s in C6:
        for v in r["trajectory"][s]:
            assert v == round(v, 3)
    for v in r["final_relative"].values():
        assert v == round(v, 3)
    # a diet that omits a consumed metabolite uses the 0.5 default for it (sugar users): compare to RK4 reference
    d = simulate_community(C6, days=2, diet={"fiber": 2.0})
    fin = ref_legacy(C6, 2, diet={"fiber": 2.0})
    for s in C6:
        assert d["trajectory"][s][-1] == pytest.approx(fin[s], abs=2e-3)


def test_shift_zero_total_guards_and_missing_final():
    assert core._shift({"A": 0, "B": 0}, {"A": 1, "B": 1}) == {"A": 0.5, "B": 0.5}        # initial total 0 -> divisor 1
    assert core._shift({"A": 1}, {"A": 0}) == {"A": -1.0}                                 # final total 0 -> divisor 1
    assert core._shift({"A": 0}, {"A": 0}) == {"A": 0.0}
    assert core._shift({"A": 2, "B": 2}, {}) == {"A": -0.5, "B": -0.5}                    # keys absent from final count as 0


def test_legacy_zero_and_negative_start():
    z = simulate_community({"Bacteroides": 0.0}, days=1)
    assert z["final_relative"] == {"Bacteroides": 0.0} and z["metabolite_flux"] == {"acetate": 0.0, "succinate": 0.0}
    assert z["dysbiosis_shift"] == {"Bacteroides": 0.0}
    n = simulate_community({"Bacteroides": -0.5, "Escherichia": 1.0}, days=1)           # negative final is clamped at 0
    assert n["final_relative"]["Bacteroides"] == 0.0 and n["final_relative"]["Escherichia"] == 1.0
    assert n["metabolite_flux"].get("acetate") == 0.0


def test_design_intervention_defaults_when_metabolites_absent():
    r = design_intervention(current_profile={"Bacteroides": 0.3, "Lactobacillus": 0.2})
    for o in r["interventions_ranked"]:
        assert o["butyrate_flux"] == 0 and o["escherichia_fraction"] == 0 and o["benefit_score"] == 0
    assert [o["intervention"] for o in r["interventions_ranked"]] == ["high-fiber diet (30g/d)", "inulin prebiotic", "low-sugar diet"]
    assert r["recommended"]["intervention"] == "high-fiber diet (30g/d)"


def test_design_intervention_score_has_three_places():
    for prof in (PROFILE, C6, {"Faecalibacterium": 0.3, "Escherichia": 0.3, "Bacteroides": 0.1}):
        for o in design_intervention(current_profile=prof)["interventions_ranked"]:
            assert abs(o["benefit_score"] * 1000 - round(o["benefit_score"] * 1000)) < 1e-9
            assert o["benefit_score"] == round(o["butyrate_flux"] - 0.5 * o["escherichia_fraction"], 3)


def test_empty_consumption_list_uses_half(monkeypatch):
    monkeypatch.setitem(core.SPECIES_TRAITS, "Ghost", {"growth": 0.4, "consumes": [], "produces": []})
    r = simulate_community({"Ghost": 1.0}, days=1)
    a, b = 0.4 * 0.5, 0.1 / 5                     # x' = x (a - b x): logistic, exact solution
    x1 = a / (b + (a / 1.0 - b) * math.exp(-a * 1.0))
    assert r["trajectory"]["Ghost"][-1] == pytest.approx(round(x1, 3), abs=1e-3)
    assert r["trajectory"]["Ghost"] == [1.0, pytest.approx(round(x1, 3), abs=1e-3)]


def test_sample_hours_lower_boundary_and_wide_values():
    s = simulate_metabolic_community(C6, days=1, sample_hours=1)
    assert len(s["trajectory"]) == 25 and s["trajectory"][1]["day"] == pytest.approx(1 / 24)
    t = simulate_metabolic_community(C6, days=1, sample_hours=2)
    assert len(t["trajectory"]) == 13
    u = simulate_metabolic_community(C6, days=0.25, sample_hours=0.5)
    assert len(u["trajectory"]) == 13 and u["trajectory"][-1]["day"] == 0.25


def test_legacy_default_tolerance_characterization_30_days():
    """Characterization of the current numbers at scipy rtol=1e-6 (scipy 1.15.3, numpy 2.2.6); looser or tighter rtol changes them.
    Values are produced by the module as coded, not by an independent oracle."""
    r = simulate_community(C6, days=30)
    assert r["metabolite_flux"] == {"butyrate": 278.349, "acetate": 19.973, "succinate": 9.979, "lactate": 12.499, "propionate": 0.727}
    assert r["trajectory"]["Faecalibacterium"][-3:] == [555.715, 556.303, 556.697]
    assert r["trajectory"]["Akkermansia"][-3:] == [1.256, 1.353, 1.454]
    assert len(r["trajectory"]["t_d"]) == 31


class _Fit:
    def __init__(self, x, fun, nfev, success): self.x, self.fun, self.nfev, self.success = x, fun, nfev, success


def test_optimizer_configuration_objective_and_selection_with_mocked_de(monkeypatch):
    import scipy.optimize as so
    seen = {}
    def fake_de(func, bounds, **kw):
        seen["func"], seen["bounds"], seen["kw"] = func, bounds, kw
        return _Fit(np.array([1.25, 2.5]), 0.123, 77, False)
    monkeypatch.setattr(so, "differential_evolution", fake_de)
    calls = []
    real = core.simulate_metabolic_community
    def spy(initial, **kw):
        calls.append(kw); return real(initial, **kw)
    monkeypatch.setattr(core, "simulate_metabolic_community", spy)
    tgt = {"butyrate": 0.05, "acetate": 0.1}
    r = core.optimize_intervention(C6, tgt, days=2)
    assert list(seen["bounds"]) == [(0, 3), (0, 3)]
    assert seen["kw"] == dict(seed=4, maxiter=20, popsize=6, polish=True)
    # selection and pass-through of the fit
    assert r["diet"] == {"fiber": 1.25, "sugar": 2.5} and all(type(v) is float for v in r["diet"].values())
    assert r["objective"] == 0.123 and r["evaluations"] == 77 and r["converged"] is False
    assert r["solver"] == "differential_evolution"
    assert calls[-1] == dict(days=2, diet={"fiber": 1.25, "sugar": 2.5}) and "sample_hours" not in calls[-1]
    # the objective handed to DE: independent recomputation at two points, with sample_hours=24 and the 1e-6 per-gram penalty
    for z in ((1.5, 2.0), (0.0, 3.0)):
        calls.clear()
        got = seen["func"](np.array(z))
        assert calls == [dict(days=2, diet={"fiber": z[0], "sugar": z[1]}, sample_hours=24)]
        fm = real(C6, days=2, diet={"fiber": z[0], "sugar": z[1]}, sample_hours=24)["final_metabolites"]
        want = sum((fm[m] - v) ** 2 for m, v in tgt.items()) + 1e-6 * (z[0] + z[1])
        assert got == pytest.approx(want, rel=1e-9, abs=1e-12)
    # penalty is exactly 1e-6 per unit of input: two z with equal metabolites would differ only by it; check the zero-target case
    zero = seen["func"](np.array((0.0, 0.0)))
    fm0 = real(C6, days=2, diet={"fiber": 0.0, "sugar": 0.0}, sample_hours=24)["final_metabolites"]
    assert zero == pytest.approx(sum((fm0[m] - v) ** 2 for m, v in tgt.items()), rel=1e-9, abs=1e-12)
    r2 = core.optimize_intervention(C6, {"butyrate": 0.05}, days=3)
    assert r2["simulation"]["trajectory"][-1]["day"] == 3.0
    assert r["target_vs_achieved"]["butyrate"]["target"] == 0.05


def test_optimizer_swapped_outputs_are_detected(monkeypatch):
    import scipy.optimize as so
    monkeypatch.setattr(so, "differential_evolution", lambda f, b, **kw: _Fit(np.array([0.5, 2.75]), 1.0, 5, True))
    r = core.optimize_intervention(C6, {"butyrate": 0.05}, days=1)
    assert r["diet"]["fiber"] == 0.5 and r["diet"]["sugar"] == 2.75 and r["converged"] is True
    assert r["simulation"]["trajectory"][0]["metabolites"]["fiber"] == 0.5
    assert r["simulation"]["trajectory"][0]["metabolites"]["sugar"] == 2.75


def test_keyword_only_signatures():
    with pytest.raises(TypeError):
        simulate_metabolic_community(C6, 2)
    with pytest.raises(TypeError):
        optimize_intervention(C6, {"butyrate": 0.05}, 2)
    with pytest.raises(TypeError):
        core.analyze_microbiome(C6, {"butyrate": 0.05}, 2)


import types as _types


def _fake_solver(calls, last=None, zero=False, fail=False):
    def solve(rhs, span, y0, **kw):
        calls.append(dict(kw, span=span))
        if fail:
            return _types.SimpleNamespace(success=False, message="backend-boom")
        ts = kw["t_eval"]
        Y = np.zeros((len(y0), len(ts))) if zero else np.tile(np.array(y0, float)[:, None], (1, len(ts)))
        if last is not None:
            Y[0, -1] = last
        return _types.SimpleNamespace(y=Y, t=ts, success=True, nfev=9)
    return solve


def test_solver_arguments_and_rounding_via_backend_spy(monkeypatch):
    calls = []
    monkeypatch.setattr(core, "solve_ivp", _fake_solver(calls, last=0.123456789))
    r = core.simulate_community({"Bacteroides": 1, "Escherichia": 0.5}, days=1.333)
    assert calls[-1]["rtol"] == 1e-6 and calls[-1]["span"] == (0, 1.333)
    # final = round(0.123456789, 4) = 0.1235; Escherichia stays 0.5; total 0.6235
    assert r["final_relative"] == {"Bacteroides": round(0.1235 / 0.6235, 3), "Escherichia": round(0.5 / 0.6235, 3)}
    assert r["final_relative"]["Bacteroides"] == 0.198
    assert r["trajectory"]["t_d"] == [0.0, 1.07]
    assert r["trajectory"]["Bacteroides"] == [1.0, 1.0]  # stride-4 samples skip the faked last point
    calls.clear()
    core.simulate_metabolic_community({"Bacteroides": 1}, days=1)
    assert (calls[-1]["rtol"], calls[-1]["atol"], calls[-1]["method"]) == (1e-8, 1e-9, "BDF")
    assert calls[-1]["span"] == (0, 1)


def test_zero_totals_and_backend_failure(monkeypatch):
    calls = []
    monkeypatch.setattr(core, "solve_ivp", _fake_solver(calls, zero=True))
    assert core.simulate_community({"Bacteroides": 0.0}, days=1)["final_relative"] == {"Bacteroides": 0}
    assert core.simulate_metabolic_community({"Bacteroides": 1}, days=1)["final_relative"] == {"Bacteroides": 0}
    monkeypatch.setattr(core, "solve_ivp", _fake_solver([], fail=True))
    with pytest.raises(RuntimeError, match="backend-boom"):
        core.simulate_metabolic_community({"Bacteroides": 1}, days=1)


def test_fractional_sample_hours_accepted():
    r = simulate_metabolic_community({"Bacteroides": 1}, days=1, sample_hours=0.5)
    assert len(r["trajectory"]) == 49 and r["trajectory"][1]["day"] == pytest.approx(0.5 / 24)
    r = simulate_metabolic_community({"Bacteroides": 1}, days=1, sample_hours=1)
    assert len(r["trajectory"]) == 25


def test_feature_thresholds_and_zero_start_fold():
    sp = ["Faecalibacterium", "Bacteroides", "Escherichia", "Lactobacillus", "Akkermansia", "Bifidobacterium"]
    rows = [{"day": t, "species": dict.fromkeys(sp, 0 if t == 0 else 0.1), "metabolites": dict.fromkeys(core.METABOLITES, 0)} for t in (0, 1)]
    fin = dict(zip(sp, [0, 1e-6, 0.2, 0.3, 0.2, 0.299999]))
    sim = {"trajectory": rows, "solver": {"nfev": 1}, "final_relative": fin}
    out = core.enhancement_features(sim, {"objective": 0, "diet": {"fiber": 0, "sugar": 0}, "evaluations": 1})
    # richness counts strictly > 1e-6: 1e-6 itself excluded, 0 excluded
    assert out["final_richness"] == 4
    assert out["Bacteroides_fold_change"] == pytest.approx(0.1 / 1e-12)
    want_h = -sum(v * math.log(v) for v in fin.values() if v > 0)
    assert out["final_shannon"] == pytest.approx(want_h, rel=1e-12)
    assert out["dominant_fraction"] == 0.3
    fin2 = dict(fin, Bacteroides=1.0000001e-6)
    out2 = core.enhancement_features(dict(sim, final_relative=fin2), {"objective": 0, "diet": {"fiber": 0, "sugar": 0}, "evaluations": 1})
    assert out2["final_richness"] == 5


def test_design_stubbed_backend_missing_metabolites_and_rounding(monkeypatch):
    monkeypatch.setattr(core, "simulate_community", lambda initial, **kw: {"metabolite_flux": {}, "final_relative": {"Bacteroides": 1}})
    r = core.design_intervention(current_profile={"Bacteroides": 1})
    assert all(o["benefit_score"] == 0 for o in r["interventions_ranked"])
    monkeypatch.setattr(core, "simulate_community", lambda initial, **kw: {"metabolite_flux": {"butyrate": .123456}, "final_relative": {"Escherichia": .123456}})
    # score = round(0.123456 - 0.5*0.123456, 3) = round(0.061728, 3) = 0.062
    assert core.design_intervention()["recommended"]["benefit_score"] == 0.062


def test_tiny_day_grid_and_final_precision(monkeypatch):
    r = simulate_metabolic_community({"Bacteroides": 1}, days=1e-10, sample_hours=.5)
    assert [x["day"] for x in r["trajectory"]] == [0, 1e-10]
    def solve(rhs, span, y0, **kw):
        Y = np.tile(np.array([.123456, .234567])[:, None], (1, len(kw["t_eval"])))
        return _types.SimpleNamespace(y=Y)
    monkeypatch.setattr(core, "solve_ivp", solve)
    ini = {"Bacteroides": 1, "Escherichia": 1}
    r = core.simulate_community(ini, days=1)
    assert r["dysbiosis_shift"] == core._shift(ini, {"Bacteroides": .1235, "Escherichia": .2346})


def test_grid_stop_value_is_days_plus_1e9(monkeypatch):
    orig = np.arange
    stops = []
    def arange(*a, **kw):
        if len(a) == 3:
            stops.append(a[1])
        return orig(*a, **kw)
    monkeypatch.setattr(core.np, "arange", arange)
    simulate_metabolic_community({"Bacteroides": 1}, days=1, sample_hours=24)
    assert stops == [1 + 1e-9]


def test_generic_species_features_fill_and_single_row():
    opt = {"objective": 0, "diet": {"fiber": 1, "sugar": 2}, "evaluations": 1}
    rows = [{"day": t, "species": {"s%d" % i: i + 1 + t for i in range(12)}, "metabolites": dict.fromkeys(core.METABOLITES, 0)} for t in (0, 1)]
    sim = {"trajectory": rows, "solver": {"nfev": 1}, "final_relative": {"s%d" % i: 1 / 12 for i in range(12)}}
    r = core.enhancement_features(sim, opt)
    assert len(r) == 50 and {"optimization_objective", "optimized_fiber", "optimized_sugar", "optimization_evaluations"} <= set(r)
    sp = ["s%d" % i for i in range(6)]
    row = {"day": 0, "species": dict.fromkeys(sp, 1), "metabolites": dict.fromkeys(core.METABOLITES, 0)}
    one = {"trajectory": [row], "solver": {"nfev": 1}, "final_relative": dict.fromkeys(sp, 1 / 6)}
    assert len(core.enhancement_features(one, opt)) == 50


def test_shift_zero_total_with_nonzero_components_and_missing_final_key():
    # initial total 0 (1 + -1): denominators fall back to 1, not 2 or 0.5
    # A: 1/3 - 1/1 = -0.667 ; B: 2/3 - (-1)/1 = 1.667
    assert core._shift({"A": 1, "B": -1}, {"A": 1, "B": 2}) == {"A": -0.667, "B": 1.667}
    # final total 0 (1 + -1): A: 1/1 - 1/3 = 0.667 ; B: -1/1 - 2/3 = -1.667
    assert core._shift({"A": 1, "B": 2}, {"A": 1, "B": -1}) == {"A": 0.667, "B": -1.667}
    # missing final key defaults to 0 (not 1 or 2): B: 0 - 2/3
    assert core._shift({"A": 1, "B": 2}, {"A": 3}) == {"A": round(1 - 1 / 3, 3), "B": -0.667}


def test_tiny_total_relative_uses_1e12_floor(monkeypatch):
    monkeypatch.setattr(core, "solve_ivp", _fake_solver([], last=1e-13, zero=True))
    r = core.simulate_metabolic_community({"Bacteroides": 1}, days=1)
    # total 1e-13 < 1e-12 floor -> 1e-13 / 1e-12 = 0.1 (floor 5e-13 gives 0.2, 2e-12 gives 0.05)
    assert r["final_relative"]["Bacteroides"] == pytest.approx(0.1, rel=1e-9)
