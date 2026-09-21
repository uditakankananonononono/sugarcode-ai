from sugarcode.modules.metabodesigner import design_pathway, bottleneck_analysis
from sugarcode.modules.synthetic_life import essentiality_scan, design_minimal_genome
from sugarcode.modules.bio_material import design_biomaterial
from sugarcode.modules.cell_free_opt import optimize_cfps, cost_model
from sugarcode.modules.stability_ai import stability_forecast
from sugarcode.modules.syn_stab_ai import evaluate_circuit_stability, suggest_stabilization
from sugarcode.modules.bio_switch import design_biosensor
from sugarcode.modules.biofactory_1_a import generate_protocol
from sugarcode.modules.robotic_flow import schedule_run, pipette_plan, monitor


def test_pathway_to_phB():
    r = design_pathway("PHB_polymer")
    assert r["found"] and r["steps"] >= 3
    assert any("thiolase" in s["enzyme"] for s in r["route"])
    assert r["feasibility"]["score"] > 0


def test_pathway_missing_target():
    r = design_pathway("vanillin")
    assert not r["found"]


def test_bottleneck_ranks():
    p = design_pathway("ethanol")
    b = bottleneck_analysis(p["route"])
    assert b["top_bottleneck"]["risk"] >= b["ranked_bottlenecks"][-1]["risk"]


def test_essentiality_and_minimal():
    e = essentiality_scan()
    assert e["essential_reactions"] and e["essential_fraction"] > 0
    g = design_minimal_genome()
    assert 0 < g["minimal_set_size"] < g["input_genes"]
    assert 0 < g["reduction_fraction"] < 1


def test_biomaterial_pha():
    r = design_biomaterial("PHA", "scaffold", "soft_tissue")
    assert r["production_pathway"]["found"]
    assert r["degradation"]["half_life_days"] > 0
    assert r["predicted_properties"]["meets_application_modulus"]


def test_cfps_optimize_and_cost():
    r = optimize_cfps(grid_step=4)
    assert r["yield_g_l"] > 0 and r["cost"]["plate_usd"] > 0
    assert r["kinetics"]["final_g_l"] > 0


def test_stability_forecast_plasmid_vs_genomic():
    p = stability_forecast({"mode": "plasmid", "burden": 0.5, "size_kb": 6})
    g = stability_forecast({"mode": "genomic", "burden": 0.5, "size_kb": 6})
    assert g["stability_score"] > p["stability_score"]
    assert p["functional_half_life_generations"] <= 200


def test_syn_stab_suggestions():
    r = suggest_stabilization({"n_gates": 4, "expression_level": 0.8, "mode": "plasmid"})
    assert any("genome" in s["change"] for s in r["suggestions"])


def test_biosensor_arsenic():
    r = design_biosensor("arsenic", "Luciferase")
    assert r["limit_of_detection_uM"] > 0
    assert len(r["dose_response"]["response"]) == 21
    assert r["response_time_min"] < 60


def test_biofactory_protocol():
    r = generate_protocol("golden_gate", n_constructs=12)
    assert r["plates"] == 1 and r["estimated_runtime_min"] > 0
    assert "colony picker" in r["equipment_required"]


def test_robotic_flow_schedule():
    tasks = [
        {"id": "dispense", "instrument": "handler", "duration_min": 10},
        {"id": "cycle", "instrument": "thermocycler", "duration_min": 90, "after": ["dispense"]},
        {"id": "read", "instrument": "reader", "duration_min": 5, "after": ["cycle"]},
    ]
    r = schedule_run(tasks)
    assert r["makespan_min"] == 105
    m = monitor(r, [{"task": "cycle", "expected_min": 100, "observed_min": 118}])
    assert m["alerts"] and m["status"] == "review_required"


def test_pipette_plan_viscosity():
    r = pipette_plan([{"source": "A1", "dest": "B1", "volume_ul": 50, "liquid": "glycerol_50"}])
    assert r["steps"][0]["aspirate_speed_ul_s"] == 40
    assert r["estimated_total_min"] > 0
