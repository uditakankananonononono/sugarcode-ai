import hashlib,json
from pathlib import Path
import pytest
from sugarcode.self_improve.registry import FeatureRegistry

def registry(tmp_path):
 r=FeatureRegistry('tools',tmp_path/'state')
 r.save_proposal('identity',name='identity',kind='text_transform',code='def run(items,params=None): return list(reversed(items))\n',test_code='def test_canary(): pass',gap_signature='reverse')
 r.activate('identity',approval_id='local-canary')
 return r

def test_actual_checkpoint_verified_restore_plan_no_mutation(tmp_path):
 from sugarcode.self_improve.registry_snapshot import checkpoint,inspect_snapshot,recovery_plan
 r=registry(tmp_path);out=tmp_path/'snapshot.json';before=r._path.read_bytes()
 assert r.dispatch('identity',['a','b'])==['b','a'];before=r._path.read_bytes()
 checkpoint(r,out);assert inspect_snapshot(out)['active_features_verified']==1
 r._path.write_text('{broken');bad=r._path.read_bytes()
 plan=recovery_plan(out);assert plan['action']=='operator_review' and plan['registry']==json.loads(before)
 assert r._path.read_bytes()==bad and not plan['applied']
 with pytest.raises(FileExistsError):checkpoint(r,out)

def test_tampered_active_file_and_snapshot_refuse(tmp_path):
 from sugarcode.self_improve.registry_snapshot import checkpoint,inspect_snapshot
 r=registry(tmp_path);out=tmp_path/'snapshot.json';checkpoint(r,out)
 m=json.loads(out.read_text());m['registry']['module']='forged';out.write_text(json.dumps(m))
 with pytest.raises(ValueError):inspect_snapshot(out)
 entry=r._active_entry('identity');Path(entry['file']).write_text('tampered')
 with pytest.raises(ValueError):checkpoint(r,tmp_path/'bad.json')
 assert not (tmp_path/'bad.json').exists()

def test_publication_failure_leaves_no_checkpoint(tmp_path,monkeypatch):
 from sugarcode.self_improve import registry_snapshot as module
 r=registry(tmp_path);out=tmp_path/'snapshot.json'
 def fail(*a):raise OSError('ordinary publication failure')
 monkeypatch.setattr(module.os,'link',fail)
 with pytest.raises(OSError):module.checkpoint(r,out)
 assert not out.exists() and not list(tmp_path.glob('.registry-stage-*'))
