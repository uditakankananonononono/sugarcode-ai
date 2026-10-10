import pytest
from sugarcode.self_improve.events import GapEventStore, GapEvent
from sugarcode.self_improve.engine import SelfImprovementEngine
from sugarcode.self_improve.gate import ManualApprovalGate
from sugarcode.self_improve.registry import FeatureRegistry, RegistryError
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
    with pytest.raises((ValueError,RegistryError)):read()
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
        obj=FeatureRegistry('m',tmp_path);path=obj._path;write=lambda:obj._save({'module':'m','features':{},'proposals':{},'x':'x'*100});cap='REGISTRY_FILE_BYTES'
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


def test_combined_registry_exact_cap_then_strict_duplicate_refusal(tmp_path,monkeypatch):
    from sugarcode.self_improve import registry
    obj=FeatureRegistry('m',tmp_path)
    raw=b'{"module":"m","features":{},"proposals":{},"extra":"finite"}'
    monkeypatch.setattr(registry,'REGISTRY_FILE_BYTES',len(raw))
    obj._path.write_bytes(raw)
    assert obj._load()['extra']=='finite'
    obj._path.write_bytes(raw+b' ')
    with pytest.raises(RegistryError) as caught:obj._load()
    assert isinstance(caught.value.__cause__,InputLimitExceeded)
    duplicate=b'{"module":"m","module":"m","features":{},"proposals":{}}'
    obj._path.write_bytes(duplicate)
    with pytest.raises(RegistryError):obj._load()


def test_combined_registry_preflight_overcap_no_candidate_mutation(tmp_path,monkeypatch):
    from sugarcode.self_improve import registry
    obj=FeatureRegistry('m',tmp_path)
    from sugarcode.self_improve import proposal_preflight_r01
    monkeypatch.setattr(proposal_preflight_r01,'REGISTRY_FILE_BYTES',10)
    before=obj._path.read_bytes()
    with pytest.raises(InputLimitExceeded):obj.save_proposal('key',name='name',kind='generic',code='code',test_code='test',gap_signature='gap')
    assert not (obj._dir/'candidates').exists()
    assert obj._path.read_bytes()==before
