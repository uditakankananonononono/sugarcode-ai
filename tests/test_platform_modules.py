from sugarcode.modules.neuro_hub import dashboard, initiate_search
from sugarcode.modules.omega_stats import record, stats, subnetwork_rollup
from sugarcode.modules.ecosystem import sdk_snippet, plugin_manifest, api_reference
from sugarcode.modules.dna_to_code import translate_concept


def test_dashboard_global_view():
    d = dashboard()
    assert d["compute_flux"]["modules_total"] == 88
    assert len(d["subnetworks"]) == 9


def test_hub_search():
    r = initiate_search("protein docking affinity")
    assert r["results"]


def test_omega_stats_pipeline():
    record("crispr_opt", "on_target_accuracy", 0.83, "accuracy")
    record("crispr_opt", "on_target_accuracy", 0.87, "accuracy")
    s = stats("accuracy")
    ser = [x for x in s["series"] if x["module"] == "crispr_opt"][0]
    assert ser["n"] == 2 and abs(ser["mean"] - 0.85) < 1e-6
    assert subnetwork_rollup()


def test_ecosystem_snippets():
    assert "from sugarcode.modules import crispr_opt" in sdk_snippet("crispr_opt")
    assert plugin_manifest("x", ["y"])["api_version"] == "omega/v7"
    assert api_reference()["modules"] == 88


def test_dna_to_code():
    r = translate_concept("transcription")
    assert "def transcribe" in r["python"]
