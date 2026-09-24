import json, os
import pytest
from sugarcode.modules.enterprise_bio import GovernedOperations

pytest.importorskip("cryptography")
from cryptography.fernet import InvalidToken

KEY = b"test-master-key-0123456789abcdef"


def test_ciphertext_on_disk_has_no_plaintext(tmp_path):
    g = GovernedOperations("startup", tenant_id="labA", vault_dir=str(tmp_path), vault_key=KEY)
    secret = "BRCA1 patient cohort 42 genotype table"
    assert g.vault_store("cohort", secret)["stored"]
    raw = (tmp_path / "cohort.enc").read_bytes()
    assert secret.encode() not in raw and b"BRCA1" not in raw
    assert KEY not in raw
    assert g.vault_retrieve("cohort") == secret.encode()
    assert oct(os.stat(tmp_path / "cohort.enc").st_mode & 0o777) == "0o600"


def test_key_never_written_to_vault_dir_or_audit(tmp_path):
    g = GovernedOperations("startup", tenant_id="labA", vault_dir=str(tmp_path), vault_key=KEY)
    g.vault_store("x", "data"); g.vault_retrieve("x")
    for f in tmp_path.iterdir():
        assert KEY not in f.read_bytes()
    assert KEY.decode() not in json.dumps(g.audit)
    assert g.vault_key_source == "argument"


def test_tenant_a_cannot_decrypt_tenant_b(tmp_path):
    a = GovernedOperations("startup", tenant_id="labA", vault_dir=str(tmp_path), vault_key=KEY)
    b = GovernedOperations("startup", tenant_id="labB", vault_dir=str(tmp_path), vault_key=KEY)
    b.vault_store("plate", "tenant B assay results")
    with pytest.raises(InvalidToken):
        a.vault_retrieve("plate")


def test_academic_tier_blocked(tmp_path):
    g = GovernedOperations("academic", tenant_id="uni", vault_dir=str(tmp_path), vault_key=KEY)
    assert g.vault_store("x", "data") == {"stored": False, "reason": "private vault requires startup tier or above"}
    assert not list(tmp_path.iterdir())
    with pytest.raises(PermissionError):
        g.vault_retrieve("x")
    r = g.guarded_module_call("virtual_cell", 77, "anything")
    assert r["called"] is False
    assert g.audit[-1]["allowed"] is False


def test_env_key_and_ephemeral_key(tmp_path, monkeypatch):
    monkeypatch.setenv("SUGARCODE_VAULT_KEY", "env-key")
    g = GovernedOperations("startup", tenant_id="t", vault_dir=str(tmp_path))
    assert g.vault_key_source == "env"
    g.vault_store("x", "data")
    assert GovernedOperations("startup", tenant_id="t", vault_dir=str(tmp_path)).vault_retrieve("x") == b"data"
    monkeypatch.delenv("SUGARCODE_VAULT_KEY")
    e = GovernedOperations("startup", tenant_id="t", vault_dir=str(tmp_path))
    assert e.vault_key_source == "ephemeral"
    with pytest.warns(UserWarning, match="ephemeral"):
        e.vault_store("y", "data")


def test_tampered_audit_entry_breaks_chain(tmp_path):
    g = GovernedOperations("startup", tenant_id="labA", vault_dir=str(tmp_path), vault_key=KEY)
    g.check_module_access("omega_stats", 74); g.consume_compute(5); g.vault_store("x", "d"); g.dispatch_robot("pcr")
    assert len(g.audit) == 4 and g.verify_audit_chain()
    g.audit[1]["hours"] = 0.1
    assert not g.verify_audit_chain()


def test_deleted_audit_entry_breaks_chain(tmp_path):
    g = GovernedOperations("startup", tenant_id="labA", vault_dir=str(tmp_path), vault_key=KEY)
    g.check_module_access("omega_stats", 74); g.consume_compute(5); g.dispatch_robot("pcr")
    del g.audit[1]
    assert not g.verify_audit_chain()


def test_robot_job_lifecycle_and_invalid_transition(tmp_path):
    g = GovernedOperations("enterprise", tenant_id="labA", vault_dir=str(tmp_path), vault_key=KEY)
    job = g.dispatch_robot("miniprep")
    assert job["allowed"] and job["status"] == "queued"
    with pytest.raises(ValueError):
        g.robot_advance(job["job_id"], "done")      # queued -> done skips running
    assert g.robot_advance(job["job_id"], "running")["status"] == "running"
    assert g.robot_advance(job["job_id"], "done")["status"] == "done"
    with pytest.raises(ValueError):
        g.robot_advance(job["job_id"], "running")   # done is terminal
    with pytest.raises(KeyError):
        g.robot_advance("nope", "running")
    exported = json.loads(g.export_robot_queue())
    assert exported["jobs"][0]["status"] == "done"
    assert g.verify_audit_chain()


def test_enterprise_guarded_call_executes(tmp_path):
    g = GovernedOperations("enterprise", tenant_id="labA", vault_dir=str(tmp_path), vault_key=KEY)
    r = g.guarded_module_call("enterprise_bio", 75, "GovernedEntitlements", "startup")
    assert r["called"] is True and r["result"].tier == "startup"
    assert g.audit[-1]["action"] == "module_call"
    assert g.verify_audit_chain()


def test_tenant_id_cannot_escape_vault_directory():
    from sugarcode.modules.enterprise_bio.core import GovernedOperations
    for bad in ("../other", "a/b", "", "..", "a\\b"):
        with pytest.raises(ValueError, match="tenant_id"):
            GovernedOperations("enterprise", tenant_id=bad, vault_key=b"k" * 32)
