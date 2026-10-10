import json
import pytest
from sugarcode.self_improve.registry import FeatureRegistry,RegistryError
from sugarcode.self_improve.registry_validation import RegistryValidationError
from sugarcode.self_improve.capped_readers import InputLimitExceeded
from sugarcode.self_improve import registry as module
from pathlib import Path


def propose(r):
 return r.save_proposal('new',name='demo',kind='generic',code='code',test_code='test',gap_signature='')


@pytest.mark.parametrize('actual_limit',[False,True])
def test_full_registry_refusal_before_any_mkdir_or_candidate_write(tmp_path,monkeypatch,actual_limit):
 r=FeatureRegistry('m',tmp_path)
 limit=16*1024*1024 if actual_limit else 512
 raw=json.dumps({'module':'m','features':{},'proposals':{},'extension':''},indent=2,sort_keys=True).encode()
 # Extension can make the admitted input exactly full without extraneous whitespace.
 data=json.loads(raw);data['extension']='x'*(limit-len(raw))
 encoded=json.dumps(data,indent=2,sort_keys=True).encode()
 assert len(encoded)==limit
 r._path.write_bytes(encoded);monkeypatch.setattr(module,'REGISTRY_FILE_BYTES',limit)
 original=Path.mkdir
 def forbid(self,*args,**kwargs):
  if self.name=='candidates':pytest.fail('mkdir preceded prospective admission')
  return original(self,*args,**kwargs)
 monkeypatch.setattr(Path,'mkdir',forbid)
 with pytest.raises(InputLimitExceeded):propose(r)
 assert r._path.read_bytes()==encoded
 assert not (r._dir/'candidates').exists()


@pytest.mark.parametrize('raw',[b'{bad',b'{"module":"m","features":[],"proposals":{}}',b'{"module":"m","module":"m"}'])
def test_preflight_corrupt_registry_normalized_with_original_cause(tmp_path,raw):
 r=FeatureRegistry('m',tmp_path);r._path.write_bytes(raw)
 with pytest.raises(RegistryError) as caught:propose(r)
 assert isinstance(caught.value.__cause__,RegistryValidationError)
 assert r._path.read_bytes()==raw and not (r._dir/'candidates').exists()


def test_prospective_schema_failure_before_candidate_io(tmp_path,monkeypatch):
 r=FeatureRegistry('m',tmp_path);before=r._path.read_bytes()
 original=module.validate_registry_state
 def refuse(data,**kwargs):
  if data['proposals']:raise RegistryValidationError('injected prospective refusal')
  return original(data,**kwargs)
 monkeypatch.setattr(module,'validate_registry_state',refuse)
 with pytest.raises(RegistryError):propose(r)
 assert r._path.read_bytes()==before and not (r._dir/'candidates').exists()


def test_success_full_proposal_remains_readable(tmp_path):
 r=FeatureRegistry('m',tmp_path);p=propose(r)
 assert Path(p['code_file']).read_bytes()==b'code'
 assert Path(p['test_file']).read_bytes()==b'test'
 assert r.get_proposal('new')==p
