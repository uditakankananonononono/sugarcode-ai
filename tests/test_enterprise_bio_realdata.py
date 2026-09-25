import pytest
from sugarcode.modules.enterprise_bio import *

def test_audit_chain_verifies_and_detects_tamper():
    g=GovernedOperations("enterprise",tenant_id="t",vault_key="k")
    g.check_module_access("m",50); g.consume_compute(5); g.use_vault()
    assert g.verify_audit_chain()
    g.audit[1]["allowed"]=not g.audit[1]["allowed"]
    assert not g.verify_audit_chain()

def test_vault_roundtrip_and_tenant_isolation(tmp_path):
    g=GovernedOperations("enterprise",tenant_id="t1",vault_key="k",vault_dir=str(tmp_path))
    g.vault_store("s","payload"); assert g.vault_retrieve("s")==b"payload"
    g2=GovernedOperations("enterprise",tenant_id="t2",vault_key="k",vault_dir=str(tmp_path))
    with pytest.raises(Exception): g2.vault_retrieve("s")

def test_vault_denied_on_academic():
    g=GovernedOperations("academic")
    assert g.vault_store("s","x")["stored"] is False
    with pytest.raises(PermissionError): g.vault_retrieve("s")

def test_robot_lifecycle_transitions():
    g=GovernedOperations("enterprise"); j=g.dispatch_robot("pcr")["job_id"]
    with pytest.raises(ValueError): g.robot_advance(j,"done")
    g.robot_advance(j,"running"); g.robot_advance(j,"done")
    with pytest.raises(ValueError): g.robot_advance(j,"failed")

def test_tier_gates_and_guarded_call():
    a=GovernedOperations("academic")
    assert a.check_module_access("m",40)["allowed"] and not a.check_module_access("m",41)["allowed"]
    assert not a.use_vault()["allowed"] and not a.dispatch_robot("x")["allowed"]
    assert not a.guarded_module_call("crispr_muse",41,"pam_matches","GGG","NGG")["called"]
    assert a.guarded_module_call("crispr_muse",10,"pam_matches","GGG","NGG")["result"] is True

def test_budget_enforcement():
    b=GovernedEntitlements("startup",monthly_budget_usd=100)
    assert b.authorize_spend(60,"x")["allowed"] and not b.authorize_spend(50,"y")["allowed"]
    assert b.spend_usd==60

def test_usage_forecast_math():
    g=GovernedOperations("startup"); g.consume_compute(50)
    f=g.usage_forecast(10)
    assert f["projected_monthly_hours"]==150 and f["utilization_fraction"]==pytest.approx(150/1000)

def test_tenant_id_validation():
    with pytest.raises(ValueError): GovernedOperations("enterprise",tenant_id="../etc")
