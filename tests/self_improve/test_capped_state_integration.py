import pytest
from sugarcode.self_improve.events import GapEventStore, GapEvent
from sugarcode.self_improve.engine import SelfImprovementEngine
from sugarcode.self_improve.gate import ManualApprovalGate
from sugarcode.self_improve.registry import FeatureRegistry
from sugarcode.self_improve.capped_readers import InputLimitExceeded


@pytest.mark.parametrize('kind',['events','ledger','gate','registry'])
def test_actual_reader_oversize_refuses_before_json_decode(tmp_path,monkeypatch,kind):
    from sugarcode.self_improve import events,engine,gate,registry
    modules={'events':events,'ledger':engine,'gate':gate,'registry':registry}
    module=modules[kind]
    if kind=='events':
        obj=GapEventStore(tmp_path);path=obj._path('m');read=lambda:obj.all('m');cap='JSONL_FILE_BYTES'
    elif kind=='ledger':
        obj=SelfImprovementEngine(module_id=1,module_slug='m',state_dir=tmp_path);path=obj._ledger_path;read=obj.ledger;cap='JSONL_FILE_BYTES'
    elif kind=='gate':
        obj=ManualApprovalGate(tmp_path/'gate');path=obj._path;read=obj._load;cap='APPROVAL_FILE_BYTES'
    else:
        obj=FeatureRegistry('m',tmp_path);path=obj._path;read=obj._load;cap='REGISTRY_FILE_BYTES'
    monkeypatch.setattr(module,cap,10)
    path.write_bytes(b'x'*11);before=path.read_bytes()
    def fail(*args,**kwargs):pytest.fail('JSON decoding before limit')
    monkeypatch.setattr(module.json,'loads',fail)
    with pytest.raises(ValueError):read()
    assert path.read_bytes()==before


@pytest.mark.parametrize('kind',['events','ledger'])
def test_actual_line_cap_before_decode(tmp_path,monkeypatch,kind):
    from sugarcode.self_improve import events,engine
    module=events if kind=='events' else engine
    monkeypatch.setattr(module,'JSONL_LINE_BYTES',10)
    if kind=='events':obj=GapEventStore(tmp_path);path=obj._path('m');read=lambda:obj.all('m')
    else:obj=SelfImprovementEngine(module_id=1,module_slug='m',state_dir=tmp_path);path=obj._ledger_path;read=obj.ledger
    path.write_bytes(b'x'*11)
    with pytest.raises(InputLimitExceeded) as caught:read()
    assert caught.value.scope=='line'
    assert path.read_bytes()==b'x'*11


@pytest.mark.parametrize('kind',['events','ledger','gate','registry'])
def test_prospective_write_cap_refuses_unchanged(tmp_path,monkeypatch,kind):
    from sugarcode.self_improve import events,engine,gate,registry
    module={'events':events,'ledger':engine,'gate':gate,'registry':registry}[kind]
    if kind=='events':
        obj=GapEventStore(tmp_path);obj.append(GapEvent('m','ok'));path=obj._path('m');write=lambda:obj.append(GapEvent('m','large',detail='x'*100));cap='JSONL_LINE_BYTES'
    elif kind=='ledger':
        obj=SelfImprovementEngine(module_id=1,module_slug='m',state_dir=tmp_path);obj._log('ok');path=obj._ledger_path;write=lambda:obj._log('large',value='x'*100);cap='JSONL_LINE_BYTES'
    elif kind=='gate':
        obj=ManualApprovalGate(tmp_path/'gate');path=obj._path;write=lambda:obj._save({'x':'x'*100});cap='APPROVAL_FILE_BYTES'
    else:
        obj=FeatureRegistry('m',tmp_path);path=obj._path;write=lambda:obj._save({'x':'x'*100});cap='REGISTRY_FILE_BYTES'
    before=path.read_bytes();monkeypatch.setattr(module,cap,10)
    with pytest.raises(InputLimitExceeded):write()
    assert path.read_bytes()==before


@pytest.mark.parametrize('kind',['events','ledger'])
def test_crlf_and_literal_unicode_separator_roundtrip(tmp_path,kind):
    if kind=='events':
        obj=GapEventStore(tmp_path);path=obj._path('m');path.write_text('{"module_slug":"m","signature":"a\u2028b"}\r\n');assert obj.all('m')[0].signature=='a\u2028b'
    else:
        obj=SelfImprovementEngine(module_id=1,module_slug='m',state_dir=tmp_path);path=obj._ledger_path;path.write_text('{"module":"m","event":"a\u2028b"}\r\n');assert obj.ledger()[0]['event']=='a\u2028b'


@pytest.mark.parametrize('kind',['events','ledger'])
def test_aggregate_append_limit_never_adds_partial_record(tmp_path,monkeypatch,kind):
    from sugarcode.self_improve import events,engine
    module=events if kind=='events' else engine
    if kind=='events':obj=GapEventStore(tmp_path);obj.append(GapEvent('m','ok'));path=obj._path('m');write=lambda:obj.append(GapEvent('m','next'))
    else:obj=SelfImprovementEngine(module_id=1,module_slug='m',state_dir=tmp_path);obj._log('ok');path=obj._ledger_path;write=lambda:obj._log('next')
    before=path.read_bytes();monkeypatch.setattr(module,'JSONL_FILE_BYTES',len(before))
    with pytest.raises(InputLimitExceeded):write()
    assert path.read_bytes()==before


def test_legacy_bare_cr_between_docs_is_not_a_record_separator(tmp_path):
    obj=GapEventStore(tmp_path);path=obj._path('m')
    content=b'{"module_slug":"m","signature":"one"}\r{"module_slug":"m","signature":"two"}'
    path.write_bytes(content)
    with pytest.raises(ValueError):obj.all('m')
    assert path.read_bytes()==content
