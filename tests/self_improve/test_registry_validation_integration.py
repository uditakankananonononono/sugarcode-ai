import pytest
from sugarcode.self_improve.registry import FeatureRegistry, RegistryError


@pytest.mark.parametrize('raw',[
    '{"module":"m","module":"wrong","features":{},"proposals":{}}',
    '{"module":"m","features":{},"proposals":{},"x":NaN}',
    '{"module":"m","features":{"x":{"versions":[],"active_version":1}},"proposals":{}}',
    '{"module":"other","features":{},"proposals":{}}',
    '[]','{bad',
])
def test_bad_actual_registry_refuses_read_and_activation_without_mutation(tmp_path,raw):
    registry=FeatureRegistry('m',tmp_path)
    registry._path.write_text(raw);before=registry._path.read_bytes()
    with pytest.raises(RegistryError):registry.features()
    with pytest.raises(RegistryError):registry.activate('x',approval_id='id')
    assert registry._path.read_bytes()==before
    assert not list(registry._ext_dir.iterdir())


def test_bad_registry_write_refuses_before_atomic_io(tmp_path,monkeypatch):
    from sugarcode.self_improve import atomic_file as af
    registry=FeatureRegistry('m',tmp_path);before=registry._path.read_bytes()
    def fail(*args,**kwargs):pytest.fail('filesystem open')
    monkeypatch.setattr(af.ops,'open',fail)
    with pytest.raises(RegistryError):registry._save({'module':'m','features':{},'proposals':{},'bad':float('nan')})
    assert registry._path.read_bytes()==before


def test_unicode_identifiers_and_generic_kind_remain_usable(tmp_path):
    registry=FeatureRegistry('m',tmp_path)
    registry.save_proposal('clé',name='démo',kind='custom_generic',code='def run(items,params=None): return items',test_code='',gap_signature='')
    registry.activate('clé',approval_id='local')
    assert registry.dispatch('démo',[1])==[1]
    assert registry.proposals()['clé']['kind']=='custom_generic'
