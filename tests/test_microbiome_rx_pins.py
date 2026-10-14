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
