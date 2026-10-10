"""Service status inspection does not consume its own finite audit history."""
import pytest

from sugarcode.self_improve import engine as em
from sugarcode.self_improve.engine import SelfImprovementEngine, InvalidLedgerValue
from sugarcode.self_improve.mixin import SelfImprovingMixin


def setup(root):
    engine=SelfImprovementEngine(module_id=1,module_slug='m',state_dir=root)
    engine.record_gap('needs filter');engine.record_gap('needs filter')
    return engine


def state_bytes(engine):
    paths=[engine._ledger_path,engine.store._path('m'),engine.registry._path,engine.gate._path]
    return {str(path):path.read_bytes() for path in paths}


@pytest.mark.parametrize('via_mixin',[False,True])
def test_repeated_status_and_restart_never_log_or_change_state(tmp_path,monkeypatch,via_mixin):
    engine=setup(tmp_path);before=state_bytes(engine)
    calls=[]
    def forbidden(*args,**kwargs):calls.append(args)
    monkeypatch.setattr(engine,'_log',forbidden)
    service=SelfImprovingMixin();service.attach_self_improvement(engine)
    read=service.self_improvement_status if via_mixin else engine.status
    first=read();second=read()
    assert calls==[], 'status attempted audit append'
    assert first==second and first['ledger_events']==2
    assert first['gap_events']==2 and first['open_gaps']==['needs filter']
    assert state_bytes(engine)==before
    restarted=SelfImprovementEngine(module_id=1,module_slug='m',state_dir=tmp_path)
    monkeypatch.setattr(restarted,'_log',forbidden)
    assert restarted.status()==first and calls==[]
    assert state_bytes(restarted)==before


def test_status_reads_exact_full_valid_ledger_but_refuses_corruption(tmp_path,monkeypatch):
    engine=setup(tmp_path);before=state_bytes(engine)
    monkeypatch.setattr(em,'JSONL_FILE_BYTES',len(engine._ledger_path.read_bytes()))
    def forbidden(*args,**kwargs):pytest.fail('full ledger status attempted append')
    monkeypatch.setattr(engine,'_log',forbidden)
    assert engine.status()['ledger_events']==2
    assert state_bytes(engine)==before
    engine._ledger_path.write_bytes(b'{')
    caught=None
    try:engine.status()
    except InvalidLedgerValue as exc:caught=exc
    assert caught is not None, 'status hid corrupt history'
    assert engine._ledger_path.read_bytes()==b'{'


@pytest.mark.parametrize('covered',['proposal','activated'])
def test_status_filters_covered_gaps_without_logging(tmp_path,monkeypatch,covered):
    engine=setup(tmp_path)
    engine.registry.save_proposal('k',name='feature',kind='keyword_filter',
        code='def run(items,params=None):return items',test_code='',gap_signature='needs filter')
    if covered=='activated':engine.registry.activate('k',approval_id='trusted-fixture')
    before=state_bytes(engine);calls=[]
    monkeypatch.setattr(engine,'_log',lambda *args,**kwargs:calls.append(args))
    assert engine.status()['open_gaps']==[]
    assert calls==[] and state_bytes(engine)==before


def test_explicit_detection_and_cycle_keep_audit_events(tmp_path):
    engine=setup(tmp_path)
    assert len(engine.detect_gaps())==1
    assert engine.ledger()[-1]['event']=='gap_detected'
    report=engine.run_cycle(max_new=0)
    assert len(report['gaps'])==1
    assert [r['event'] for r in engine.ledger()]==[
        'gap_event_recorded','gap_event_recorded','gap_detected','gap_detected','cycle_completed']
    before=state_bytes(engine)
    assert engine.status()['ledger_events']==5
    assert state_bytes(engine)==before


def test_status_reads_each_state_once(tmp_path,monkeypatch):
    engine=setup(tmp_path);counts={'events':0,'registry':0,'ledger':0}
    def spy(label, original):
        def call(*args,**kwargs):counts[label]+=1;return original(*args,**kwargs)
        return call
    monkeypatch.setattr(engine.store,'all',spy('events',engine.store.all))
    monkeypatch.setattr(engine.registry,'_load',spy('registry',engine.registry._load))
    monkeypatch.setattr(engine,'ledger',spy('ledger',engine.ledger))
    assert engine.status()['open_gaps']==['needs filter']
    assert counts=={'events':1,'registry':1,'ledger':1}
