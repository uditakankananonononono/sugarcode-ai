"""Stack B7 claim-guard tests: bioprint_pro + neuro_hub_dashboard.

Each test pins the honest, bounded behaviour behind a scoped capability claim.
Reverting the implementation function a test names must make that test fail.
Text guards pin the claim wording (spec disclaimers, corrections sections,
honest registry/README capability strings).
"""
import math
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from sugarcode.modules.bioprint_pro import core as bp
from sugarcode.modules.neuro_hub_dashboard import core as nh

ROOT = Path(__file__).resolve().parents[1]


# ---- bioprint_pro capability guards ---------------------------------------

def test_cross_model_viscosity_formula():
    # S5-007.A01, S5-022.A01, S5-070.01.C01, S5-096.01.C01, S5-096.02.C03
    ink = bp.INKS["alginate_2pct"]
    lo, hi = bp._viscosity(ink, 1e-6), bp._viscosity(ink, 1e9)
    assert lo == pytest.approx(ink["eta0"], rel=1e-3)
    assert hi == pytest.approx(ink["eta_inf"], rel=1e-2)
    mid = bp._viscosity(ink, 100.0)
    expect = ink["eta_inf"] + (ink["eta0"] - ink["eta_inf"]) / (1 + (ink["lambda_s"] * 100.0) ** ink["n"])
    assert mid == pytest.approx(expect, rel=1e-9)
    # shear-thinning: monotone decreasing across decades
    curve = [bp._viscosity(ink, s) for s in (0.1, 1, 10, 100, 1000)]
    assert all(a > b for a, b in zip(curve, curve[1:]))


def test_hagen_poiseuille_printability_window_si():
    # S5-007.A02, S5-022.A02, S5-070.01.C02
    cal = bp.calibrate("alginate_2pct")
    w8 = next(w for w in cal["printability_window"] if w["speed_mm_s"] == 8)
    assert w8["viscosity_Pa_s"] == pytest.approx(6.512, abs=0.01)
    assert w8["pressure_kPa"] == pytest.approx(104.2, abs=0.2)
    # independent SI Hagen-Poiseuille recomputation
    q = math.pi * 0.2 ** 2 * 8 * 1e-9
    shear = 4 * q / (math.pi * (2e-4) ** 3)
    eta = bp._viscosity(bp.INKS["alginate_2pct"], shear)
    p = 8 * eta * 0.010 * q / (math.pi * (2e-4) ** 4)
    assert w8["pressure_kPa"] == pytest.approx(p / 1000, abs=0.2)
    assert w8["wall_shear_s-1"] == pytest.approx(shear, rel=0.01)


def test_first_order_crosslinking_schedule():
    # S5-007.A03, S5-022.A03, S5-070.01.C03
    cal = bp.calibrate("alginate_2pct")
    k = bp.INKS["alginate_2pct"]["k_crosslink_s"]
    assert cal["crosslinking"]["t95_s"] == pytest.approx(-math.log(0.05) / k, abs=0.01)
    assert cal["crosslinking"]["t95_s"] == pytest.approx(3.74, abs=0.01)
    assert cal["crosslinking"]["conversion_at_10s"] == pytest.approx(1 - math.exp(-k * 10), abs=1e-3)


def test_shape_fidelity_proxy_from_conversion():
    # S5-007.A04
    cal = bp.calibrate("alginate_2pct")
    x = cal["crosslinking"]["conversion_at_10s"]
    best = cal["recommended"]
    expect = round(min(1.0, (1 - math.exp(-bp.INKS["alginate_2pct"]["k_crosslink_s"] * 10)) * 1.2) * (1.0 if best else 0.5), 2)
    assert cal["structural_integrity"]["predicted_shape_fidelity"] == pytest.approx(expect, abs=1e-9)
    assert 0.0 <= cal["structural_integrity"]["predicted_shape_fidelity"] <= 1.0
    assert x > 0


def test_carreau_yasuda_curve():
    # S5-096.02.C02
    eta = bp.carreau_yasuda([1e-6, 100.0, 1e9])
    assert eta[0] == pytest.approx(150.0, rel=1e-3)
    expect = 0.5 + 149.5 * (1 + (2 * 100.0) ** 2) ** ((0.55 - 1) / 2)
    assert eta[1] == pytest.approx(expect, rel=1e-9)
    assert eta[2] < 1.0  # approaches eta_inf from above
    assert eta[0] > eta[1] > eta[2]


def test_extrusion_fixed_point_and_giesekus_note():
    # supports S5-096.02.C01 correction (function must not claim Oldroyd-B dynamics)
    r = bp.oldroyd_b_extrusion(100, 0.4)
    assert r["flow_rate_mm3_s"] == pytest.approx(0.9280045, rel=1e-3)
    assert "cannot shear-thin" in r["constitutive_model"]
    # fixed point: flow(q) == q
    ink = bp.INKS["alginate_2pct"]
    q = r["flow_rate_mm3_s"] * 1e-9
    eta = bp._viscosity(ink, 4 * q / (math.pi * (2e-4) ** 3))
    assert q == pytest.approx(math.pi * (2e-4) ** 4 * 1e5 / (8 * eta * 0.010), rel=1e-3)


def test_cell_radial_distribution_and_local_shear():
    # S5-097.01.C03
    r = bp.oldroyd_b_extrusion(100, 0.4, cells=200)
    pos = r["cell_radial_position_mm"]
    assert len(pos) == 200 and all(0 <= p <= 0.2 for p in pos)
    assert len(r["cell_viability"]) == 200
    assert all(0 < v <= 1 for v in r["cell_viability"])


def test_reaction_diffusion_gelation_ionic():
    # S5-096.01.C03, S5-098.01.C01, S5-098.01.C02
    r = bp.crosslink_reaction_diffusion("ionic", seconds=60)
    assert r["diffusion_mm2_s"] == pytest.approx(0.008)
    assert r["rate_s-1"] == pytest.approx(0.8)
    gel, c = r["conversion"], r["concentration"]
    assert all(0 <= g <= 1 for g in gel) and all(0 <= ci <= 1 for ci in c)
    assert gel[0] > 0.9 and gel[-1] > 0.9      # boundaries gelled
    assert gel[len(gel) // 2] < gel[0]          # diffusion front still inbound
    assert len(r["history"]) > 0


def test_coupled_gel_depends_on_kinetics():
    # S5-098.02.C01 (bounded: one RD equation with coupled algebraic gel update)
    slow = bp.crosslink_reaction_diffusion("enzymatic", seconds=60)
    fast = bp.crosslink_reaction_diffusion("ionic", seconds=60)
    assert slow["rate_s-1"] != fast["rate_s-1"]
    mid = len(slow["conversion"]) // 2
    assert fast["conversion"][mid] != pytest.approx(slow["conversion"][mid], rel=1e-6)


def test_polymer_network_stiffness_evolution_heterogeneity():
    # S5-098.02.C02, S5-098.02.C03, S5-098.02.C04
    r = bp.crosslink_reaction_diffusion("ionic", seconds=60)
    stiff = r["stiffness_kPa"]
    assert all(s == pytest.approx(2 + 48 * g * g, abs=1e-9) for s, g in zip(stiff[:5], r["conversion"][:5]))
    assert max(stiff) > min(stiff)                       # network is spatially nonuniform
    assert r["heterogeneity_CV"] > 0
    import statistics
    assert r["heterogeneity_CV"] == pytest.approx(statistics.pstdev(stiff) / statistics.mean(stiff), rel=1e-6)
    assert len(r["history"]) >= 2                        # spatial stiffness evolution recorded


def test_viscoelastic_relaxation_and_load():
    # S5-099.01.C04, S5-CODEDOC-062.C02, S5-CODEDOC-062.C04, S5-070.01.C04
    cross = bp.crosslink_reaction_diffusion("ionic", seconds=30)
    mech = bp.scaffold_mechanics(cross, load_kpa=10, seconds=3600)
    inst, rel = mech["instantaneous_strain"], mech["relaxed_strain"]
    assert all(r <= i + 1e-12 for i, r in zip(inst, rel))   # relaxation reduces strain
    assert any(r < i for i, r in zip(inst, rel))
    # linear in load (algebraic relation, honestly not nonlinear)
    mech2 = bp.scaffold_mechanics(cross, load_kpa=20, seconds=3600)
    assert max(mech2["instantaneous_strain"]) == pytest.approx(2 * max(inst), rel=1e-9)
    # zero load -> zero strain
    mech0 = bp.scaffold_mechanics(cross, load_kpa=0, seconds=3600)
    assert max(mech0["instantaneous_strain"]) == pytest.approx(0.0, abs=1e-12)
    assert mech["safety_factor"] > 0 and len(mech["buckling_load_kPa"]) == len(inst)


def test_porosity_effect():
    # S5-CODEDOC-064.C05, S5-CODEDOC-064.C06
    cross = bp.crosslink_reaction_diffusion("ionic", seconds=30)
    dense = bp.scaffold_mechanics(cross, load_kpa=10, porosity=0.1)
    porous = bp.scaffold_mechanics(cross, load_kpa=10, porosity=0.6)
    assert max(porous["instantaneous_strain"]) > max(dense["instantaneous_strain"])
    # pore pressure prescribed to decay along the scaffold
    p = dense["pore_pressure_kPa"]
    assert p[0] > p[-1] and all(a >= b for a, b in zip(p, p[1:]))


def test_maturation_pathway_ode():
    # S5-070.03.C04, S5-100.03.C04
    m = bp.maturation_pathway(0.8, 15.0, days=28)
    assert len(m["day"]) == len(m["cell_density"]) == len(m["ECM"]) == 113
    assert m["cell_density"][-1] != pytest.approx(m["cell_density"][0])  # ODE dynamics, not a constant
    assert m["ECM"][-1] > 0.05                       # matrix accumulates
    assert all(0 <= o <= 1.0001 for o in m["oxygen"])


def test_simulate_diagnostics_fidelity_viability_resilience():
    # S5-100.02.C01, S5-100.02.C02, S5-100.03.C03
    sim = bp.simulate_bioprint()
    d = sim["diagnostics"]
    assert 0 < d["shape_fidelity"] <= 1
    assert 0 < d["mean_cell_viability"] <= 1
    assert d["mechanical_resilience"] > 0
    assert len(d) >= 50
    assert "not clinically validated" in sim["model_status"]


def test_optimize_print_evolutionary_in_bounds():
    # S5-100.01.C01, S5-100.01.C03
    out = bp.optimize_print()
    p = out["parameters"]
    assert 20 <= p["pressure_kPa"] <= 200 and 0.2 <= p["nozzle_mm"] <= 0.8
    assert 5 <= p["crosslink_seconds"] <= 90 and 0.15 <= p["porosity"] <= 0.65 and 2 <= p["load_kPa"] <= 25
    assert out["solver"] == "differential evolution"
    assert out["objective"] > 0


# ---- neuro_hub_dashboard capability guards ---------------------------------

RECORDS = [{"module": "m1", "importable": True, "latency_ms": 5},
           {"module": "m2", "importable": True, "latency_ms": 15},
           {"module": "m3", "importable": False, "latency_ms": 0}]


def test_platform_health_counts():
    # S5-030.A01, S5-064.03.C01
    h = nh.platform_health(RECORDS)
    assert h["modules_total"] == 3 and h["modules_online"] == 2
    assert h["global_flux"] == pytest.approx(2 / 3)
    assert h["degraded"] == ["m3"]
    assert h["latency_mean_ms"] == pytest.approx(20 / 3)


def test_flux_series_timestamp_order_decides_trend():
    # S5-CODEDOC-005
    samples = [{"timestamp": 3, "modules_online": 3, "modules_total": 4},
               {"timestamp": 1, "modules_online": 1, "modules_total": 4},
               {"timestamp": 2, "modules_online": 2, "modules_total": 4}]
    r = nh.compute_flux_series(samples)
    assert r["timestamps"] == [1, 2, 3]
    assert r["global_flux"] == [0.25, 0.5, 0.75]
    assert r["trend"] == pytest.approx(0.5)
    # input order does not decide the sign
    r2 = nh.compute_flux_series(list(reversed(samples)))
    assert r2["trend"] == pytest.approx(0.5)


def test_unified_search_whole_token():
    # S5-030.A03, S5-064.02.C02, S5-CODEDOC-006.C02
    recs = [{"module": "a", "text": "rna folding internal dynamics"},
            {"module": "b", "text": "internal state only"},
            {"module": "c", "text": "rna rna design"}]
    out = nh.unified_search("rna", recs)
    mods = [r["module"] for r in out["results"]]
    assert "b" not in mods                       # 'rna' must not match inside 'internal'
    assert mods[0] == "c"                        # whole-token count 2 beats 1
    assert out["results"][0]["relevance"] == 2
    with pytest.raises(ValueError):
        nh.unified_search("rna", recs, limit=-1)


def test_project_state_and_snapshot():
    # S5-064.03.C02
    st = nh.project_state("demo", "bioprint_pro", state="running")
    assert st["completion"] == pytest.approx(0.5) and st["state"] == "running"
    with pytest.raises(ValueError):
        nh.project_state("demo", "bioprint_pro", state="bogus")
    snap = nh.dashboard_snapshot(RECORDS, projects=[st])
    assert snap["health"]["modules_online"] == 2
    assert snap["alerts"] == ["1 modules degraded"]
    assert "no neural inference model" in snap["model_status"]


def test_dashboard_diagnostics_over_core():
    # S5-030.A04
    snap = nh.dashboard_snapshot(RECORDS, projects=[nh.project_state("p", "m")])
    d = nh.dashboard_diagnostics(snap)
    assert d["modules_total"] == 3 and d["degraded_count"] == 1
    assert d["global_flux"] == pytest.approx(2 / 3)
    assert d["project_count"] == 1


# ---- claim-text guards ------------------------------------------------------

def test_spec_disclaimer_headers_present():
    # DISC-bioprint_pro, DISC-neuro_hub_dashboard
    for f in ("spec/bioprint_pro.md", "spec/neuro_hub_dashboard.md"):
        head = (ROOT / f).read_text()[:400]
        assert head.startswith("> **Spec vs implementation:**"), f
        assert "aspirational product-spec" in head


def test_spec_corrections_cover_flagged_rows():
    # guards the CORRECT-row rewording (each flagged row id has a recorded correction)
    bio = (ROOT / "spec/bioprint_pro.md").read_text()
    for rid in ("S5-022.A04", "S5-070.02.C01", "S5-070.02.C02", "S5-070.03.C01",
                "S5-070.03.C02", "S5-070.03.C03", "S5-096.01.C02", "S5-096.01.C04",
                "S5-096.02.C01", "S5-096.02.C04", "S5-097.01.C01", "S5-097.01.C02",
                "S5-097.02.C01", "S5-097.02.C02", "S5-097.02.C03", "S5-098.01.C03",
                "S5-098.01.C04", "S5-098.02.C01", "S5-098.02.C05", "S5-099.01.C01",
                "S5-099.01.C02", "S5-099.01.C03", "S5-099.02.C01", "S5-099.02.C02",
                "S5-099.02.C03", "S5-100.01.C02", "S5-100.02.C03", "S5-100.03.C01",
                "S5-100.03.C02"):
        assert f"- {rid}," in bio, rid
    neuro = (ROOT / "spec/neuro_hub_dashboard.md").read_text()
    for rid in ("S5-064.01", "S5-064.02.C01", "S5-064.02.C02", "S5-064.02.C03",
                "S5-064.03.C01", "S5-064.03.C02", "S5-064.03.C03"):
        assert f"- {rid}," in neuro, rid


def test_docstrings_and_model_fields_honest():
    # S5-CODEDOC-059.C03, 061.C03, 062.C01, 062.C03
    src = (ROOT / "src/sugarcode/modules/bioprint_pro/core.py").read_text()
    assert "structural prediction.\"" not in src.replace("not a structural prediction", "")
    assert "stiffness PDE.\"" not in src.replace("not a solved stiffness PDE", "")
    assert "Nonlinear poro-viscoelastic" not in src
    assert "FE chain" not in src
    flux_doc = nh.compute_flux_series.__doc__
    assert "input order does not decide the sign" in flux_doc
