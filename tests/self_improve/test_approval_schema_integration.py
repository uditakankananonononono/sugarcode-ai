import json
import pytest
from sugarcode.self_improve.engine import SelfImprovementEngine
from sugarcode.self_improve.gate import ManualApprovalGate, APPROVED, InvalidApprovalState


def make(tmp_path,auto=False):
    gate=ManualApprovalGate(tmp_path/'gate',auto_approve=auto)
    engine=SelfImprovementEngine(module_id=1,module_slug='m',state_dir=tmp_path/'state',gate=gate)
    for _ in range(2): engine.record_gap('filter biology grants',exemplar='biology grant')
    p=engine.run_cycle()['proposals'][0]
    return engine,gate,p


@pytest.mark.parametrize('field,value',[('module_id',2),('module_slug','other'),('action_type','generic')])
def test_activation_wrong_record_identity_refuses(tmp_path,field,value):
    engine,gate,p=make(tmp_path)
    gate.decide(p['approval_id'],APPROVED)
    data=gate._load();data[p['approval_id']][field]=value;gate._save(data)
    with pytest.raises(PermissionError): engine.activate(p['key'],approval_id=p['approval_id'])
    assert engine.registry.features()=={}


@pytest.mark.parametrize('field,value',[('name','other'),('kind','other'),('code_sha256','b'*64),('candidate_key','other'),('gap_signature','other')])
def test_activation_payload_mismatch_refuses(tmp_path,field,value):
    engine,gate,p=make(tmp_path)
    gate.decide(p['approval_id'],APPROVED)
    data=gate._load();data[p['approval_id']]['payload'][field]=value;gate._save(data)
    with pytest.raises(PermissionError): engine.activate(p['key'],approval_id=p['approval_id'])
    assert engine.registry.features()=={}


def test_full_record_detached_and_generic_request_compatible(tmp_path):
    gate=ManualApprovalGate(tmp_path/'gate')
    key=gate.request(module_id=1,module_slug='m',action_type='generic',summary='x',payload={'x':[1]})
    record=gate.record(key);record['payload']['x'].append(2)
    assert gate.record(key)['payload']=={'x':[1]}
    gate.decide(key,APPROVED,decided_by=None)
    assert gate.decision(key)==APPROVED


def test_legacy_minimal_read_preserved_not_engine_authority(tmp_path):
    gate=ManualApprovalGate(tmp_path/'gate')
    gate._path.write_text('{"old":{"status":"pending","payload":{}}}')
    assert gate.decision('old')=='pending'
    gate.decide('old',APPROVED)
    assert gate.record('old')['status']==APPROVED


def test_autoapprove_valid_only_explicit_gate_auto(tmp_path):
    engine,gate,p=make(tmp_path,auto=True)
    assert engine.activate(p['key'],approval_id=p['approval_id'])['version']==1


def test_unrecorded_approval_not_accepted_by_manual_gate(tmp_path):
    engine,gate,p=make(tmp_path)
    data=gate._load();data[p['approval_id']]['status']=APPROVED;gate._save(data)
    with pytest.raises(PermissionError): engine.activate(p['key'],approval_id=p['approval_id'])
    assert engine.registry.features()=={}


def test_activation_id_cannot_authorize_rollback(tmp_path):
    engine,gate,p=make(tmp_path)
    gate.decide(p['approval_id'],APPROVED);engine.activate(p['key'],approval_id=p['approval_id'])
    with pytest.raises(PermissionError): engine.rollback(p['name'],approval_id=p['approval_id'])
    assert engine.registry.features()[p['name']]['active_version']==1


@pytest.mark.parametrize('record',[None,[],{'status':'yes'},{'status':True}])
def test_bad_generic_status_refuses_unchanged(tmp_path,record):
    gate=ManualApprovalGate(tmp_path/'gate');gate._save({'id':record});before=gate._path.read_bytes()
    with pytest.raises(InvalidApprovalState):gate.decision('id')
    with pytest.raises(InvalidApprovalState):gate.decide('id',APPROVED)
    assert gate._path.read_bytes()==before


def test_status_only_custom_gate_fails_closed_before_activation(tmp_path):
    engine,gate,p=make(tmp_path)
    class StatusOnly:
        def decision(self,identifier):return APPROVED
    engine.gate=StatusOnly()
    with pytest.raises(PermissionError,match='full approval record'):engine.activate(p['key'],approval_id=p['approval_id'])
    assert engine.registry.features()=={}


def test_unknown_full_record_id_unchanged(tmp_path):
    gate=ManualApprovalGate(tmp_path/'gate');before=gate._path.read_bytes()
    with pytest.raises(KeyError):gate.record('unknown')
    assert gate._path.read_bytes()==before
