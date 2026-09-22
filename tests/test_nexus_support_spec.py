from datetime import datetime, timezone
import pytest
from sugarcode.modules.nexus_support import (
    classify_inquiry, custom_build_plan, detect_modules, enhancement_features,
    integration_plan, match_expertise, schedule_queue, support_case, triage,
)


def test_inquiry_classification_is_evidence_backed_and_security_precedes_bug():
    r = classify_inquiry("Urgent security credential leak causes an API error")
    assert r["primary"] == "security"
    assert {"security", "bug", "integration"} <= set(r["labels"])
    assert "credential" in r["keyword_evidence"]["security"]
    assert r["urgency_score"] > 0


def test_registry_module_resolution_and_expertise_routing():
    mods = detect_modules("Our crispr opt guide pipeline fails")
    assert mods and mods[0]["module"] == "crispr_opt"
    experts = match_expertise("VCF genomics pipeline", mods)
    assert experts[0]["score"] >= experts[-1]["score"]
    assert any(x["expertise"] == "bioinformatics" for x in experts)
    with pytest.raises(KeyError): detect_modules("x", "not_a_module")


def test_triage_has_sla_deadline_kb_and_honest_status():
    now = datetime(2026, 9, 22, tzinfo=timezone.utc)
    r = triage("How do I score a CRISPR Opt PAM guide?", tier="enterprise", submitted_at=now)
    assert r["routed_to"]["module"] == "crispr_opt"
    assert r["sla_hours"] == 12
    assert r["kb_matches"] and r["auto_resolvable"]
    assert "mechanistic hermetic" in r["model_status"]
    assert r["response_due_at"].startswith("2026-09-22T12:00:00")


def test_custom_build_plan_traces_contract_phases_and_risks():
    r = custom_build_plan("Custom CRISPR Opt build ingesting FASTQ and returning JSON API",
                          {"deadline": "2026-10-01"})
    assert r["input_formats"] == ["fastq"]
    assert {"api", "json"} <= set(r["output_formats"])
    assert [x["phase"] for x in r["work_packages"]] == ["discovery", "prototype", "validation", "integration"]
    assert "delivery deadline unspecified" not in r["open_risks"]


def test_integration_plan_is_dependency_ordered_with_rollback():
    r = integration_plan("LIMS", "warehouse", data_types=["VCF", "FASTQ", "VCF"])
    by_id = {x["id"]: x for x in r["steps"]}
    assert r["data_types"] == ["FASTQ", "VCF"]
    assert by_id["ingest"]["depends_on"] == ["contract", "auth"]
    assert by_id["deliver"]["depends_on"] == ["validate"]
    assert "revoke credential" in r["rollback"]


def test_exact_queue_solver_beats_greedy_highest_priority_item():
    tickets = [
      {"ticket_id":"A", "estimated_hours":4, "priority_score":9, "sla_risk":1},
      {"ticket_id":"B", "estimated_hours":2, "priority_score":6, "sla_risk":1},
      {"ticket_id":"C", "estimated_hours":2, "priority_score":6, "sla_risk":1},
    ]
    r = schedule_queue(tickets, 4)
    assert {x["ticket_id"] for x in r["selected"]} == {"B", "C"}
    assert r["objective_value"] == 12 and r["optimal"]


def test_exactly_fifty_six_meaningful_computed_diagnostics():
    f = enhancement_features("Urgent API error 500 in Docker production for crispr opt; attached screenshot")
    assert len(f) == 56 and len(set(f)) == 56
    assert f["error_code_present"] and f["environment_present"]
    assert f["attachment_reference_present"] and f["candidate_module_count"] == 1


def test_end_to_end_support_case_covers_spec_and_rejects_invalid_input():
    r = support_case("Build a custom virtual cell research dashboard from CSV", constraints={})
    assert r["diagnostic_count"] == 56 and "custom_build" in r
    assert r["triage"]["routed_to"]["module"] == "virtual_cell"
    with pytest.raises(ValueError): classify_inquiry("  ")
    with pytest.raises(ValueError): integration_plan("", "warehouse")
