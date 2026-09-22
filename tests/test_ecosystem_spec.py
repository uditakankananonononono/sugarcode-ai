import pytest
from sugarcode.modules.ecosystem import *

def manifests():
 a=plugin_manifest("lab_io",["ingest_fastq"])
 b=plugin_manifest("variant_report",["render_vcf"]); b["depends_on"]=["lab_io"]
 return [a,b]
def assets(): return [{"name":"reads","type":"sequence","format":"FASTA"},{"name":"calls","type":"variants","format":"TXT"}]

def test_plugin_manifest_validation_and_digest():
 r=validate_plugin_manifest(manifests()[0]); assert r["valid"] and len(r["manifest_sha256"])==64 and r["install_checks"]

def test_dependency_solver_is_real_topological_order_and_rejects_cycles():
 assert resolve_plugin_order(manifests())["install_order"]==["lab_io","variant_report"]
 a,b=manifests(); a["depends_on"]=["variant_report"]
 with pytest.raises(ValueError,match="cycle"): resolve_plugin_order([a,b])

def test_sdk_client_is_executable_authenticated_and_validated():
 r=generate_sdk_client("crispr_opt","design_guides")
 assert "requests.post" in r["code"] and "SUGARCODE_KEY" in r["code"] and r["path"].endswith("/design_guides")
 with pytest.raises(ValueError,match="https"): generate_sdk_client("crispr_opt","design_guides",base_url="http://unsafe")

def test_standards_plan_produces_actions_and_collaboration_package():
 r=standards_plan(assets()); assert r["compliant_count"]==1 and r["conversion_count"]==1
 assert "convert TXT to VCF" in r["workflow_actions"] and "provenance.json" in r["collaboration_package"]

def test_exactly_fifty_input_derived_diagnostics():
 f=enhancement_features(manifests(),assets(),"crispr_opt","design_guides")
 assert len(f)==50 and len(set(f))==50 and f["dependency_edge_count"]==1 and f["conversion_asset_count"]==1

def test_end_to_end_package_is_developer_ready():
 r=build_integration_package(manifests(),assets(),"crispr_opt","design_guides")
 assert r["diagnostic_count"]==50 and r["plugin_order"]["install_order"][-1]=="variant_report"
 assert r["release_checklist"] and r["model_status"]=="deterministic hermetic integration tooling"

def test_informative_manifest_errors():
 with pytest.raises(ValueError,match="missing required fields"): validate_plugin_manifest({})
 with pytest.raises(ValueError,match="name"): validate_plugin_manifest({**plugin_manifest("OK",["x"]),"metadata":{"name":"OK"}})
