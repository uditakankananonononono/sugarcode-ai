import pytest
from sugarcode.self_improve.registry import FeatureRegistry, RegistryError
from sugarcode.self_improve.proposal_preflight_r01 import ProposalPreflightError
from sugarcode.self_improve import atomic_file as af


def propose(registry,key='x',**over):
    fields=dict(name='demo',kind='generic_custom',code='def run(items,params=None): return items',test_code='',gap_signature='')
    fields.update(over)
    return registry.save_proposal(key,**fields)


def test_corrupt_registry_before_any_candidate_write(tmp_path):
    registry=FeatureRegistry('m',tmp_path)
    registry._path.write_text('{bad');before=registry._path.read_bytes()
    with pytest.raises(RegistryError):propose(registry)
    assert registry._path.read_bytes()==before
    assert not (registry._dir/'candidates').exists()


def test_existing_key_retry_preserves_all_files(tmp_path):
    registry=FeatureRegistry('m',tmp_path);propose(registry)
    before={str(p):p.read_bytes() for p in registry._dir.rglob('*') if p.is_file()}
    with pytest.raises(ProposalPreflightError):propose(registry,code='replacement')
    assert before=={str(p):p.read_bytes() for p in registry._dir.rglob('*') if p.is_file()}


def test_orphan_destination_refuses_no_overwrite(tmp_path):
    registry=FeatureRegistry('m',tmp_path);directory=registry._dir/'candidates';directory.mkdir()
    path=directory/'x.py';path.write_text('orphan')
    with pytest.raises(ProposalPreflightError):propose(registry)
    assert path.read_text()=='orphan'
    assert not (directory/'x.test.py').exists()


def test_failed_registry_save_removes_only_new_candidate_files(tmp_path,monkeypatch):
    registry=FeatureRegistry('m',tmp_path);before=registry._path.read_bytes()
    def fail(*args):raise OSError('before replace')
    monkeypatch.setattr(af.ops,'replace',fail)
    with pytest.raises(OSError):propose(registry)
    assert registry._path.read_bytes()==before
    assert not list((registry._dir/'candidates').iterdir())


def test_postreplace_durability_error_keeps_referenced_files(tmp_path,monkeypatch):
    registry=FeatureRegistry('m',tmp_path)
    def fail(*args):raise OSError('after replace')
    monkeypatch.setattr(af,'_fsync_dir',fail)
    with pytest.raises(af.AtomicDurabilityError):propose(registry)
    assert registry.get_proposal('x')['status']=='proposed'
    assert (registry._dir/'candidates'/'x.py').exists()
    assert (registry._dir/'candidates'/'x.test.py').exists()


@pytest.mark.parametrize('value',['../escape','', 'a/b'])
def test_unsafe_identity_refuses_before_candidates(tmp_path,value):
    registry=FeatureRegistry('m',tmp_path)
    with pytest.raises(ProposalPreflightError):propose(registry,key=value)
    assert not (registry._dir/'candidates').exists()


def test_unicode_long_identifiers_generic_kind_compatible(tmp_path):
    registry=FeatureRegistry('m',tmp_path)
    record=propose(registry,key='a'*129,name='Démo_1')
    assert record['kind']=='generic_custom'


def test_multibyte_filename_limit_refuses_before_directory_creation(tmp_path):
    registry=FeatureRegistry('m',tmp_path)
    with pytest.raises(ProposalPreflightError,match='filesystem limit'):
        propose(registry,key='é'*129)
    assert not (registry._dir/'candidates').exists()
    assert registry.proposals()=={}
