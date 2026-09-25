import pytest
from sugarcode.modules.ecosystem import *

def M(n,caps,deps=()):
    m=plugin_manifest(n,caps); m["depends_on"]=list(deps); return m

def test_bug67_duplicate_names_rejected_not_collapsed():
    with pytest.raises(ValueError,match="duplicate plugin names"):
        resolve_plugin_order([M("alpha",["qc"]),M("alpha",["other"])])

def test_topological_order_and_edges():
    r=resolve_plugin_order([M("beta",["r"],["alpha"]),M("alpha",["q"])])
    assert r["install_order"]==["alpha","beta"] and r["dependency_edges"]==1 and r["parallel_roots"]==["alpha"]

def test_missing_dependency_rejected():
    with pytest.raises(ValueError,match="missing plugin dependencies"):
        resolve_plugin_order([M("beta",["r"],["ghost"])])

def test_cycles_rejected():
    with pytest.raises(ValueError,match="cycle"): resolve_plugin_order([M("xxx",["a"],["xxx"])])
    with pytest.raises(ValueError,match="cycle"): resolve_plugin_order([M("ccc",["a"],["ddd"]),M("ddd",["b"],["ccc"])])

def test_manifest_digest_deterministic():
    assert validate_plugin_manifest(plugin_manifest("alpha",["qc"]))["manifest_sha256"]==validate_plugin_manifest(plugin_manifest("alpha",["qc"]))["manifest_sha256"]

def test_standards_plan_compliance():
    r=standards_plan([{"name":"s","type":"sequence","format":"fasta"},{"name":"v","type":"variants","format":"xls"}])
    assert r["compliant_count"]==1 and r["conversion_count"]==1 and r["assets"][1]["target_format"]=="VCF"

def test_enhancement_features_exactly_50():
    out=enhancement_features([M("alpha",["q"]),M("beta",["r"],["alpha"])],[{"name":"s","type":"sequence","format":"fasta"}],"crispr_muse","design_muse_strategy")
    assert len(out)==50 and out["registry_module_count"]>0

def test_sdk_client_contract():
    s=generate_sdk_client("crispr_muse","design_muse_strategy")
    assert s["method"]=="POST" and "SUGARCODE_KEY" in s["code"]
    with pytest.raises(ValueError): generate_sdk_client("crispr_muse","bad-op!")
