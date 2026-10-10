import hashlib
import os
from pathlib import Path
import pytest
from sugarcode.self_improve.registry import FeatureRegistry,RegistryError
from sugarcode.self_improve.source_admission import InputLimitExceeded,SOURCE_CODE_BYTES
from sugarcode.self_improve.plans import Candidate,FeaturePlan
from sugarcode.self_improve.sandbox import SandboxRunner
from sugarcode.self_improve.isolation import IsolatedRunner
from sugarcode.self_improve.engine import SelfImprovementEngine


def seed(tmp_path,code='def run(items,params=None): return {"items":items}'):
 r=FeatureRegistry('m',tmp_path)
 p=r.save_proposal('key',name='demo',kind='generic',code=code,test_code='',gap_signature='gap')
 return r,p


@pytest.mark.parametrize('which',['code','test_code'])
def test_proposal_oversize_before_dir_or_files(tmp_path,which):
 r=FeatureRegistry('m',tmp_path);before=r._path.read_bytes()
 fields=dict(name='demo',kind='generic',code='code',test_code='test',gap_signature='gap');fields[which]='x'*(SOURCE_CODE_BYTES+1)
 with pytest.raises(InputLimitExceeded):r.save_proposal('key',**fields)
 assert r._path.read_bytes()==before and not (r._dir/'candidates').exists()


def test_crlf_raw_digest_and_activation_roundtrip(tmp_path):
 code='def run(items,params=None):\r\n return {"items":items}\r\n'
 r,p=seed(tmp_path,code);entry=r.activate('key',approval_id='local')
 assert Path(entry['file']).read_bytes()==code.encode()
 assert entry['sha256']==p['code_sha256']==hashlib.sha256(code.encode()).hexdigest()
 assert r.dispatch('demo',[1])=={'items':[1]}


@pytest.mark.parametrize('stage',['activation','dispatch','isolated'])
@pytest.mark.parametrize('defect',['oversize','symlink','fifo'])
def test_source_refusal_before_state_or_execution(tmp_path,stage,defect):
 r,p=seed(tmp_path)
 if stage=='activation':path=Path(p['code_file']);call=lambda:r.activate('key',approval_id='local')
 else:
  e=r.activate('key',approval_id='local');path=Path(e['file'])
  if stage=='dispatch':call=lambda:r.dispatch('demo',[])
  else:
   from sugarcode.self_improve.isolated_dispatch import dispatch
   call=lambda:dispatch(r,'demo',[])
 before=r._path.read_bytes()
 if defect=='oversize':path.write_bytes(b'x'*(SOURCE_CODE_BYTES+1))
 elif defect=='symlink':
  target=path.with_name('other.py');target.write_bytes(path.read_bytes());path.unlink();path.symlink_to(target)
 else:path.unlink();os.mkfifo(path)
 with pytest.raises((RegistryError,ValueError,OSError)):call()
 assert r._path.read_bytes()==before


@pytest.mark.parametrize('runner',[SandboxRunner,IsolatedRunner])
@pytest.mark.parametrize('which',['code','test_code'])
def test_evaluation_source_caps_before_workspace_creation(tmp_path,monkeypatch,runner,which):
 import tempfile
 def forbid(*a,**kw):pytest.fail('workspace created before source admission')
 monkeypatch.setattr(tempfile,'mkdtemp',forbid)
 fields=dict(code='def run(items,params=None):return items',test_code='def test_ok():assert True')
 fields[which]='x'*(SOURCE_CODE_BYTES+1)
 c=Candidate(FeaturePlan('m','demo','keyword_filter','d','g'),**fields)
 with pytest.raises(InputLimitExceeded):runner().run(c)


def test_engine_custom_evaluator_cannot_skip_source_admission(tmp_path):
 class Never:
  def run(self,c):pytest.fail('custom evaluator called before refusal')
 e=SelfImprovementEngine(module_id=1,module_slug='m',state_dir=tmp_path,sandbox=Never())
 c=Candidate(FeaturePlan('m','demo','keyword_filter','d','g'),'x'*(SOURCE_CODE_BYTES+1),'')
 e._candidates['key']=c
 with pytest.raises(InputLimitExceeded):e.evaluate('key')


@pytest.mark.parametrize('stage',['activation','dispatch'])
def test_path_replacement_after_read_does_not_reload(tmp_path,monkeypatch,stage):
 from sugarcode.self_improve import registry
 r,p=seed(tmp_path)
 if stage=='activation':path=Path(p['code_file'])
 else:entry=r.activate('key',approval_id='local');path=Path(entry['file'])
 original=registry.read_source_snapshot
 def replace(*a,**kw):
  snapshot=original(*a,**kw);path.write_text('raise RuntimeError("reloaded")');return snapshot
 monkeypatch.setattr(registry,'read_source_snapshot',replace)
 if stage=='activation':
  entry=r.activate('key',approval_id='local')
  assert b'reloaded' not in Path(entry['file']).read_bytes()
  assert r.dispatch('demo',[1])=={'items':[1]}
 else:assert r.dispatch('demo',[1])=={'items':[1]}


def test_exact_code_cap_admitted_real_activation_dispatch(tmp_path):
 base='def run(items,params=None): return {"items":items}\n#'
 code=base+'x'*(SOURCE_CODE_BYTES-len(base))
 r,p=seed(tmp_path,code);r.activate('key',approval_id='local')
 assert r.dispatch('demo',[2])=={'items':[2]}


def test_both_invalid_utf8_and_surrogate_source_refuse(tmp_path):
 r,p=seed(tmp_path);before=r._path.read_bytes()
 Path(p['code_file']).write_bytes(b'\xff')
 with pytest.raises(RegistryError):r.activate('key',approval_id='local')
 assert r._path.read_bytes()==before
 with pytest.raises(ValueError):r.save_proposal('other',name='demo',kind='generic',code='\ud800',test_code='',gap_signature='gap')
 assert not (r._dir/'candidates'/'other.py').exists()


def test_utf8_bom_preserved_and_executed(tmp_path):
 r,p=seed(tmp_path,'\ufeffdef run(items,params=None): return {"items":items}')
 e=r.activate('key',approval_id='local')
 assert Path(e['file']).read_bytes().startswith(b'\xef\xbb\xbf')
 assert r.dispatch('demo',[3])=={'items':[3]}
