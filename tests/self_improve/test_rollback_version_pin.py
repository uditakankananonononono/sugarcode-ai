import pytest
from sugarcode.self_improve.engine import SelfImprovementEngine
from sugarcode.self_improve.gate import ManualApprovalGate


def setup(tmp_path):
    gate=ManualApprovalGate(tmp_path/'gate',auto_approve=True)
    engine=SelfImprovementEngine(module_id=1,module_slug='m',state_dir=tmp_path,gate=gate)
    add_version(engine,1)
    return engine,gate


def add_version(engine,n):
    key=f'key{n}'
    engine.registry.save_proposal(key,name='test_feature',kind='keyword_filter',code=f'# {n}\ndef run(items,params=None):return items',test_code='',gap_signature='gap')
    engine.registry.activate(key,approval_id='seed')


def test_request_pins_exact_active_version(tmp_path):
    engine,gate=setup(tmp_path);aid=engine.request_rollback('test_feature')
    assert gate.record(aid)['payload']=={'feature':'test_feature','active_version_at_request':1}


def test_new_activation_after_request_refuses_and_preserves_state(tmp_path):
    engine,gate=setup(tmp_path);aid=engine.request_rollback('test_feature');add_version(engine,2)
    before=engine.registry._path.read_bytes()
    with pytest.raises(PermissionError):engine.rollback('test_feature',approval_id=aid)
    assert engine.registry._path.read_bytes()==before


def test_successful_rollback_cannot_replay_for_prior_version(tmp_path):
    engine,gate=setup(tmp_path);add_version(engine,2);aid=engine.request_rollback('test_feature')
    assert engine.rollback('test_feature',approval_id=aid)['active_version']==1
    before=engine.registry._path.read_bytes()
    with pytest.raises(PermissionError):engine.rollback('test_feature',approval_id=aid)
    assert engine.registry._path.read_bytes()==before


@pytest.mark.parametrize('pin',[None,True,0,-1,'1',1.0])
def test_bad_or_absent_pin_refuses_unchanged(tmp_path,pin):
    engine,gate=setup(tmp_path)
    payload={'feature':'test_feature'}
    if pin is not None:payload['active_version_at_request']=pin
    aid=gate.request(module_id=1,module_slug='m',action_type='self_improvement_rollback',summary='legacy',payload=payload)
    before=engine.registry._path.read_bytes()
    with pytest.raises(PermissionError):engine.rollback('test_feature',approval_id=aid)
    assert engine.registry._path.read_bytes()==before


def test_in_process_race_checked_inside_registry_lock(tmp_path,monkeypatch):
    engine,gate=setup(tmp_path);aid=engine.request_rollback('test_feature')
    original=engine.registry.rollback
    def race(*args,**kwargs):
        add_version(engine,2)
        return original(*args,**kwargs)
    monkeypatch.setattr(engine.registry,'rollback',race)
    with pytest.raises(PermissionError):engine.rollback('test_feature',approval_id=aid)
    assert engine.registry.features()['test_feature']['active_version']==2


def test_correct_new_pin_still_rolls_back(tmp_path):
    engine,gate=setup(tmp_path);add_version(engine,2)
    aid=engine.request_rollback('test_feature')
    assert engine.rollback('test_feature',approval_id=aid)['rolled_back_from']==2


def test_request_missing_has_no_gate_mutation(tmp_path):
    engine,gate=setup(tmp_path);before=gate._path.read_bytes()
    with pytest.raises(KeyError):engine.request_rollback('missing')
    assert gate._path.read_bytes()==before
