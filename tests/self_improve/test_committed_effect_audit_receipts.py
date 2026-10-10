"""Real approved activation/rollback/dispatch with failed audit append."""
import json
from pathlib import Path

import pytest

from sugarcode.self_improve import engine as em
from sugarcode.self_improve.approval_consumption import CONSUMED_KEY
from sugarcode.self_improve.engine import SelfImprovementEngine, CommittedEffectAuditError
from sugarcode.self_improve.gate import APPROVED


def setup(root):
    return SelfImprovementEngine(module_id=1, module_slug='m', state_dir=root)


def proposal(engine, key, code='def run(items,params=None):return items'):
    engine.registry.save_proposal(key,name='feature',kind='keyword_filter',code=code,
                                 test_code='',gap_signature=key)
    p=engine.registry.get_proposal(key)
    aid=engine.gate.request(module_id=1,module_slug='m',action_type='self_improvement_activation',
        summary='synthetic',payload={'candidate_key':key,'name':'feature','kind':'keyword_filter',
                                    'code_sha256':p['code_sha256'],'gap_signature':key})
    engine.registry.set_proposal_approval(key,aid);engine.gate.decide(aid,APPROVED)
    return aid


def fault(engine, monkeypatch, kind):
    if kind=='cap':monkeypatch.setattr(em,'JSONL_FILE_BYTES',0);return ValueError
    if kind=='corrupt':engine._ledger_path.write_bytes(b'{');return ValueError
    def fail(*args,**kwargs):raise OSError('synthetic audit IO failure')
    monkeypatch.setattr(em,'append_jsonl',fail);return OSError


@pytest.mark.parametrize('operation',['activate','rollback','dispatch'])
@pytest.mark.parametrize('failure',['cap','corrupt','io'])
def test_completed_effect_receipt_and_restart_readback(tmp_path,monkeypatch,operation,failure):
    engine=setup(tmp_path);aid=proposal(engine,'first')
    if operation!='activate':engine.activate('first',approval_id=aid)
    if operation=='rollback':
        second=proposal(engine,'second');engine.activate('second',approval_id=second)
        aid=engine.request_rollback('feature');engine.gate.decide(aid,APPROVED)
    expected=fault(engine,monkeypatch,failure)
    caught=None
    try:
        if operation=='activate':engine.activate('first',approval_id=aid)
        elif operation=='rollback':engine.rollback('feature',approval_id=aid)
        else:engine.dispatch('feature',['synthetic'])
    except BaseException as exc:caught=exc
    assert isinstance(caught,CommittedEffectAuditError), 'completed effect lost typed receipt'
    assert isinstance(caught.__cause__,expected)
    assert caught.committed is True and caught.retry_safe is False
    assert caught.operation==operation and caught.subject==('first' if operation=='activate' else 'feature')
    restarted=setup(tmp_path);state=restarted.registry._load()
    feature=state['features']['feature']
    if operation=='activate':
        assert caught.approval_id==aid and caught.version==1
        assert caught.outcome==feature['versions'][0] and feature['active_version']==1
        assert len(state[CONSUMED_KEY])==1
        with pytest.raises(PermissionError,match='consumed'):restarted.activate('first',approval_id=aid)
    elif operation=='rollback':
        assert caught.approval_id==aid and caught.version==2
        assert caught.outcome=={'name':'feature','rolled_back_from':2,'active_version':1}
        assert feature['active_version']==1 and len(state[CONSUMED_KEY])==3
        with pytest.raises(PermissionError):restarted.rollback('feature',approval_id=aid)
    else:
        assert caught.approval_id is None and caught.version==1
        assert caught.result_reference==['synthetic']
        assert caught.outcome['result_storage']=='in_memory_only'
        assert feature['versions'][0]['dispatch_count']==1


def test_dispatch_preserves_hostile_in_memory_result_without_conversion(tmp_path,monkeypatch):
    engine=setup(tmp_path);marker=tmp_path/'calls'
    code=f'''from pathlib import Path
class Hostile:
 def __repr__(self):raise AssertionError('repr forbidden')
 def __str__(self):raise AssertionError('str forbidden')
def run(items,params=None):
 p=Path({str(marker)!r});p.write_text(p.read_text()+'x' if p.exists() else 'x')
 return Hostile()
'''
    aid=proposal(engine,'hostile',code);engine.activate('hostile',approval_id=aid)
    fault(engine,monkeypatch,'io')
    with pytest.raises(CommittedEffectAuditError) as caught:engine.dispatch('feature',[])
    assert type(caught.value.result_reference).__name__=='Hostile'
    assert marker.read_text()=='x'
    assert engine.registry.features()['feature']['versions'][0]['dispatch_count']==1


@pytest.mark.parametrize('operation',['activate','rollback','dispatch'])
def test_pre_effect_refusals_are_not_claimed_committed(tmp_path,operation):
    engine=setup(tmp_path);aid=proposal(engine,'first')
    try:
        if operation=='activate':engine.activate('first',approval_id='wrong')
        elif operation=='rollback':engine.rollback('feature',approval_id=aid)
        else:engine.dispatch('missing',[])
    except BaseException as exc:
        assert not isinstance(exc,CommittedEffectAuditError)
    else:pytest.fail('expected refusal')
    assert engine.registry.features()=={}


def test_dispatch_counter_failure_does_not_claim_committed_receipt(tmp_path,monkeypatch):
    engine=setup(tmp_path);aid=proposal(engine,'first');engine.activate('first',approval_id=aid)
    def fail(*args):raise OSError('synthetic counter IO failure')
    monkeypatch.setattr(engine.registry,'_save',fail)
    with pytest.raises(OSError) as caught:engine.dispatch('feature',[])
    assert not isinstance(caught.value,CommittedEffectAuditError)
    # Execution may already have happened; generic counter error does NOT imply
    # safe retry. That ambiguity is explicitly outside this audit-only receipt.
    assert engine.registry.features()['feature']['versions'][0]['dispatch_count']==0


def test_normal_returns_unchanged(tmp_path):
    engine=setup(tmp_path);aid=proposal(engine,'first')
    assert engine.activate('first',approval_id=aid)['version']==1
    assert engine.dispatch('feature',['x'])==['x']
    rid=engine.request_rollback('feature');engine.gate.decide(rid,APPROVED)
    assert engine.rollback('feature',approval_id=rid)['active_version'] is None


@pytest.mark.parametrize('operation',['activate','rollback'])
def test_registry_durability_ambiguity_keeps_existing_exception_taxonomy(tmp_path,monkeypatch,operation):
    from sugarcode.self_improve.atomic_file import AtomicDurabilityError
    from sugarcode.self_improve.immutable_source import SourcePublicationError
    engine=setup(tmp_path);aid=proposal(engine,'first')
    if operation=='rollback':
        engine.activate('first',approval_id=aid)
        aid=engine.request_rollback('feature');engine.gate.decide(aid,APPROVED)
    real_save=engine.registry._save
    def uncertain(data):
        real_save(data)
        raise AtomicDurabilityError('synthetic postreplace uncertainty')
    monkeypatch.setattr(engine.registry,'_save',uncertain)
    caught=None
    try:
        if operation=='activate':engine.activate('first',approval_id=aid)
        else:engine.rollback('feature',approval_id=aid)
    except BaseException as exc:caught=exc
    assert not isinstance(caught,CommittedEffectAuditError)
    assert isinstance(caught,SourcePublicationError if operation=='activate' else AtomicDurabilityError)
