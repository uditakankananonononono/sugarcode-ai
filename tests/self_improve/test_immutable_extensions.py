import json
import multiprocessing as mp
import os
from pathlib import Path
import threading
import pytest
from sugarcode.self_improve.registry import FeatureRegistry
from sugarcode.self_improve.immutable_source import publish_source,SourcePublicationError
from sugarcode.self_improve import immutable_source as source,atomic_file as af


def seed(root):
 r=FeatureRegistry('m',root);r.save_proposal('key',name='demo',kind='generic',code='def run(items,params=None):return items',test_code='',gap_signature='g');return r


def test_preexisting_orphan_never_overwritten(tmp_path):
 r=seed(tmp_path);dest=r._ext_dir/'demo_v1.py';dest.write_bytes(b'orphan');before=r._path.read_bytes()
 with pytest.raises(SourcePublicationError) as caught:r.activate('key',approval_id='a')
 assert not caught.value.published and caught.value.candidate_key=='key'
 assert dest.read_bytes()==b'orphan' and r._path.read_bytes()==before
 assert r.reconcile_extensions()['entries'][0]['classification']=='unreferenced'


def test_reader_during_forced_partial_temp_write_sees_no_final(tmp_path,monkeypatch):
 dest=tmp_path/'published.py';entered=threading.Event();release=threading.Event();errors=[];original=source.ops.write
 def short(fd,data):
  n=original(fd,data[:3]);entered.set();assert release.wait(5);return n
 monkeypatch.setattr(source.ops,'write',short)
 def writer():
  try:publish_source(dest,b'complete-source')
  except BaseException as exc:errors.append(exc)
 t=threading.Thread(target=writer);t.start();assert entered.wait(5)
 assert not dest.exists()
 assert list(tmp_path.glob('.*.tmp'))
 release.set();t.join(10);assert not t.is_alive() and not errors
 assert dest.read_bytes()==b'complete-source'


@pytest.mark.parametrize('stage',['write','file_sync','link','dir_sync'])
def test_publication_failures_typed_and_artifacts_retained(tmp_path,monkeypatch,stage):
 dest=tmp_path/'final';original=source.ops.fsync
 def fail(*args):raise OSError('injected')
 if stage=='write':monkeypatch.setattr(source.ops,'write',fail)
 elif stage=='link':monkeypatch.setattr(source.ops,'link',fail)
 elif stage=='dir_sync':monkeypatch.setattr(source,'_sync_directory',fail)
 else:monkeypatch.setattr(source.ops,'fsync',fail)
 with pytest.raises(SourcePublicationError) as caught:publish_source(dest,b'complete',candidate_key='key')
 assert caught.value.published==(stage=='dir_sync')
 if dest.exists():assert dest.read_bytes()==b'complete'
 assert list(tmp_path.glob('.*.tmp'))


@pytest.mark.parametrize('after',[False,True])
def test_registry_commit_failure_report_not_delete_published(tmp_path,monkeypatch,after):
 r=seed(tmp_path)
 def fail(*a):raise OSError('injected')
 if after:monkeypatch.setattr(af,'_fsync_dir',fail)
 else:monkeypatch.setattr(af.ops,'replace',fail)
 with pytest.raises(SourcePublicationError) as caught:r.activate('key',approval_id='a')
 assert caught.value.published and caught.value.registry_committed==(True if after else None)
 assert (r._ext_dir/'demo_v1.py').read_bytes().startswith(b'def run')
 report=r.reconcile_extensions()
 assert report['entries'][0]['classification']==('referenced' if after else 'unreferenced')


def crash_worker(root,cut,ready):
 r=FeatureRegistry('m',Path(root))
 def pause(stage):
  if stage==cut:ready.set();__import__('time').sleep(30)
 source.checkpoint=pause
 from sugarcode.self_improve import registry
 registry.checkpoint=pause
 r.activate('key',approval_id='a')


@pytest.mark.parametrize('cut',['temp_fsynced','name_published','published_dir_fsynced','temp_removed_fsynced','before_registry_commit','registry_committed'])
def test_real_kill_stage_restart_evidence(tmp_path,cut):
 r=seed(tmp_path);ctx=mp.get_context('spawn');ready=ctx.Event()
 p=ctx.Process(target=crash_worker,args=(str(tmp_path),cut,ready));p.start();assert ready.wait(10)
 p.kill();p.join(10);assert p.exitcode<0
 fresh=FeatureRegistry('m',tmp_path);report=fresh.reconcile_extensions()
 dest=fresh._ext_dir/'demo_v1.py'
 if cut=='temp_fsynced':assert not dest.exists()
 else:assert dest.read_bytes()==b'def run(items,params=None):return items'
 assert bool(fresh.features())==(cut=='registry_committed')
 assert all(row.get('classification')!='referenced_mismatch' for row in report['entries'])


def test_reconciliation_readonly_inactive_missing_mismatch_temp_and_cap(tmp_path):
 r=seed(tmp_path);entry=r.activate('key',approval_id='a');r.rollback('demo',approval_id='r')
 dest=Path(entry['file']);assert r.reconcile_extensions()['entries'][0]['classification']=='referenced'
 dest.write_bytes(b'changed');assert r.reconcile_extensions()['entries'][0]['classification']=='referenced_mismatch'
 temp=r._ext_dir/'.x.publish-test.tmp';temp.write_bytes(b'partial')
 before={str(p):p.read_bytes() for p in r._dir.rglob('*') if p.is_file()}
 r.reconcile_extensions()
 assert before=={str(p):p.read_bytes() for p in r._dir.rglob('*') if p.is_file()}
 with pytest.raises(ValueError):r.reconcile_extensions(max_entries=1)
 assert before=={str(p):p.read_bytes() for p in r._dir.rglob('*') if p.is_file()}
 dest.unlink();report=r.reconcile_extensions();assert any(x['classification']=='referenced_missing' for x in report['entries'])


@pytest.mark.parametrize('kind',['symlink','directory','fifo'])
def test_existing_nonregular_destination_refused(tmp_path,kind):
 dest=tmp_path/'dest'
 if kind=='symlink':target=tmp_path/'target';target.write_bytes(b'old');dest.symlink_to(target)
 elif kind=='directory':dest.mkdir()
 else:os.mkfifo(dest)
 with pytest.raises(SourcePublicationError):publish_source(dest,b'new')
 assert dest.lstat()


def test_reconciliation_overlimit_and_symlink_read_refusal(tmp_path):
 r=seed(tmp_path);large=r._ext_dir/'large.py';large.write_bytes(b'x'*(1048576+1))
 link=r._ext_dir/'link.py';link.symlink_to(large)
 report=r.reconcile_extensions();rows={Path(x['path']).name:x for x in report['entries']}
 assert rows['large.py']['classification']=='read_refused'
 assert rows['link.py']['classification']=='nonregular'
 assert large.stat().st_size==1048577 and link.is_symlink()


def test_file_fsync_precedes_exclusive_link(tmp_path,monkeypatch):
 order=[];sync=source.ops.fsync;link=source.ops.link
 def synced(fd):order.append('sync');return sync(fd)
 def linked(*a):assert 'sync' in order;order.append('link');return link(*a)
 monkeypatch.setattr(source.ops,'fsync',synced);monkeypatch.setattr(source.ops,'link',linked)
 publish_source(tmp_path/'file',b'complete')
 assert order[0]=='sync'


def test_actual_report_10000_entry_bound_refuses_10001(tmp_path):
 r=seed(tmp_path)
 for i in range(10001):(r._ext_dir/f'orphan{i}.py').touch()
 with pytest.raises(ValueError,match='entry cap'):r.reconcile_extensions()
 assert len(list(r._ext_dir.iterdir()))==10001
