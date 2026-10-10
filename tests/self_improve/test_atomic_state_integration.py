"""Real gate/registry save wiring under injected pre/post-replace failures."""
import os
import stat

import pytest

from sugarcode.self_improve import atomic_file as af
from sugarcode.self_improve.gate import APPROVED, PENDING, InvalidApprovalState, ManualApprovalGate
from sugarcode.self_improve.registry import FeatureRegistry


def test_preserve_mode_despite_restrictive_umask(tmp_path):
    path=tmp_path/'state';path.write_text('old');path.chmod(0o664)
    previous=os.umask(0o077)
    try: af.atomic_write_text(path,'new')
    finally: os.umask(previous)
    assert stat.S_IMODE(path.stat().st_mode)==0o664


@pytest.mark.parametrize('kind',['gate','registry'])
@pytest.mark.parametrize('failure',['write','fsync','replace'])
def test_real_state_save_failure_keeps_old_bytes(tmp_path,monkeypatch,kind,failure):
    state=ManualApprovalGate(tmp_path/'gate') if kind=='gate' else FeatureRegistry('m',tmp_path)
    before=state._path.read_bytes()
    def fail(*args,**kwargs): raise OSError('injected '+failure)
    monkeypatch.setattr(af.ops,failure,fail)
    with pytest.raises(OSError): state._save({'new':1})
    assert state._path.read_bytes()==before
    assert not list(state._path.parent.glob('.*.tmp'))


def test_gate_serialize_rejection_precedes_atomic_io(tmp_path,monkeypatch):
    gate=ManualApprovalGate(tmp_path/'gate');before=gate._path.read_bytes()
    def fail(*args,**kwargs): pytest.fail('filesystem open invoked')
    monkeypatch.setattr(af.ops,'open',fail)
    with pytest.raises(InvalidApprovalState): gate._save({'x':float('nan')})
    assert gate._path.read_bytes()==before


def test_postreplace_durability_error_means_decision_landed(tmp_path,monkeypatch):
    gate=ManualApprovalGate(tmp_path/'gate')
    identifier=gate.request(module_id=1,module_slug='m',action_type='activate',summary='x',payload={})
    original=af._fsync_dir
    def fail(directory): raise OSError('directory sync failed')
    monkeypatch.setattr(af,'_fsync_dir',fail)
    with pytest.raises(af.AtomicDurabilityError) as caught: gate.decide(identifier,APPROVED)
    assert caught.value.replaced is True
    assert gate.decision(identifier)==APPROVED
    monkeypatch.setattr(af,'_fsync_dir',original)


def test_gate_and_registry_initialize_private_complete_files(tmp_path):
    gate=ManualApprovalGate(tmp_path/'gate')
    registry=FeatureRegistry('m',tmp_path)
    assert gate._load()=={}
    assert registry.features()=={}
    assert stat.S_IMODE(gate._path.stat().st_mode)==0o600
    assert stat.S_IMODE(registry._path.stat().st_mode)==0o600


def test_permission_preservation_failure_keeps_old_state(tmp_path,monkeypatch):
    path=tmp_path/'state';path.write_text('old')
    def fail(*args): raise OSError('chmod failed')
    monkeypatch.setattr(af.ops,'fchmod',fail)
    with pytest.raises(OSError): af.atomic_write_text(path,'new')
    assert path.read_text()=='old'
    assert not list(tmp_path.glob('.*.tmp'))


def test_request_directory_failure_exposes_persisted_id(tmp_path,monkeypatch):
    gate=ManualApprovalGate(tmp_path/'gate')
    def fail(directory): raise OSError('dir sync failed')
    monkeypatch.setattr(af,'_fsync_dir',fail)
    with pytest.raises(af.AtomicDurabilityError) as caught:
        gate.request(module_id=1,module_slug='m',action_type='activate',summary='x',payload={})
    assert caught.value.replaced is True
    approval_id=caught.value.approval_id
    assert gate.decision(approval_id)==PENDING
    assert list(gate._load())==[approval_id]


def test_hardlink_other_name_keeps_old_inode(tmp_path):
    path=tmp_path/'target';other=tmp_path/'other'
    path.write_text('old');os.link(path,other)
    af.atomic_write_text(path,'new')
    assert path.read_text()=='new'
    assert other.read_text()=='old'
