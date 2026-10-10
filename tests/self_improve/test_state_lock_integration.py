import multiprocessing as mp
import os
from pathlib import Path
import threading
import pytest
from sugarcode.self_improve.state_lock import shared_state_lock,StateLockTimeout,StateLockUnavailable
from sugarcode.self_improve.gate import ManualApprovalGate,APPROVED
from sugarcode.self_improve.registry import FeatureRegistry


def gate_worker(path,barrier,queue):
 try:
  gate=ManualApprovalGate(Path(path));barrier.wait(10)
  ids=[]
  for i in range(10):
   aid=gate.request(module_id=1,module_slug='m',action_type='generic',summary='test',payload={})
   gate.decide(aid,APPROVED);ids.append(aid)
  queue.put(('ok',ids))
 except BaseException as e:queue.put(('error',str(e)))


def registry_worker(path,prefix,barrier,queue):
 try:
  r=FeatureRegistry('m',Path(path));barrier.wait(10)
  for i in range(10):r.save_proposal(f'{prefix}{i}',name='demo',kind='generic',code='code',test_code='',gap_signature='')
  queue.put('ok')
 except BaseException as e:queue.put(str(e))


def hold_worker(path,ready,release):
 with shared_state_lock(path,timeout=.2):
  ready.set();release.wait(10)


@pytest.mark.parametrize('kind',['gate','registry'])
def test_two_posix_processes_barrier_no_lost_state(tmp_path,kind):
 ctx=mp.get_context('spawn');barrier=ctx.Barrier(2);queue=ctx.Queue()
 if kind=='gate':
  path=tmp_path/'gate';ManualApprovalGate(path)
  processes=[ctx.Process(target=gate_worker,args=(str(path),barrier,queue)) for _ in range(2)]
 else:
  path=tmp_path;FeatureRegistry('m',path)
  processes=[ctx.Process(target=registry_worker,args=(str(path),p,barrier,queue)) for p in ('a','b')]
 for p in processes:p.start()
 results=[queue.get(timeout=20) for _ in processes]
 for p in processes:p.join(20);assert p.exitcode==0
 if kind=='gate':
  assert all(x[0]=='ok' for x in results)
  g=ManualApprovalGate(path);assert len(g._load())==20
  assert all(x['status']==APPROVED for x in g._load().values())
 else:assert results==['ok','ok'] and len(FeatureRegistry('m',path).proposals())==20


@pytest.mark.parametrize('kind',['gate','registry'])
def test_two_objects_share_same_reentrant_lock(tmp_path,kind):
 if kind=='gate':a=ManualApprovalGate(tmp_path/'gate');b=ManualApprovalGate(tmp_path/'gate')
 else:a=FeatureRegistry('m',tmp_path);b=FeatureRegistry('m',tmp_path)
 assert a._lock is b._lock
 with a._lock:
  with b._lock:assert b._lock._depth==2


def test_other_process_timeout_then_crash_releases_lock(tmp_path):
 ctx=mp.get_context('spawn');ready=ctx.Event();release=ctx.Event();path=tmp_path/'state'
 p=ctx.Process(target=hold_worker,args=(str(path),ready,release));p.start();assert ready.wait(10)
 lock=shared_state_lock(path,timeout=.2)
 with pytest.raises(StateLockTimeout):
  with lock:pass
 p.terminate();p.join(10)
 with lock:assert lock._depth==1


@pytest.mark.parametrize('kind',['symlink','fifo','directory'])
def test_nonregular_sidecar_refused(tmp_path,kind):
 path=tmp_path/'state';side=Path(str(path)+'.lock')
 if kind=='symlink':target=tmp_path/'target';target.write_text('');side.symlink_to(target)
 elif kind=='fifo':os.mkfifo(side)
 else:side.mkdir()
 with pytest.raises((OSError,StateLockUnavailable)):
  with shared_state_lock(path):pytest.fail('acquired unsafe sidecar')


def test_unavailable_posix_lock_fails_closed(tmp_path,monkeypatch):
 from sugarcode.self_improve import state_lock
 monkeypatch.setattr(state_lock,'fcntl',None)
 with pytest.raises(StateLockUnavailable):
  with shared_state_lock(tmp_path/'state'):pass


def test_two_object_gate_requests_barrier_no_lost_updates(tmp_path):
 a=ManualApprovalGate(tmp_path/'gate');b=ManualApprovalGate(tmp_path/'gate');barrier=threading.Barrier(2);errors=[]
 def run(gate):
  try:
   barrier.wait(5)
   for i in range(10):gate.request(module_id=1,module_slug='m',action_type='generic',summary='t',payload={})
  except BaseException as e:errors.append(e)
 threads=[threading.Thread(target=run,args=(g,)) for g in (a,b)]
 for t in threads:t.start()
 for t in threads:t.join(10);assert not t.is_alive()
 assert not errors and len(a._load())==20


def test_constructor_initialization_serialized_between_processes(tmp_path):
 ctx=mp.get_context('spawn');barrier=ctx.Barrier(2);queue=ctx.Queue();path=tmp_path/'new-gate'
 processes=[ctx.Process(target=gate_worker,args=(str(path),barrier,queue)) for _ in range(2)]
 for p in processes:p.start()
 results=[queue.get(timeout=20) for _ in processes]
 for p in processes:p.join(20);assert p.exitcode==0
 assert all(x[0]=='ok' for x in results)
 assert len(ManualApprovalGate(path)._load())==20


def test_two_object_registry_barrier_no_lost_updates(tmp_path):
 a=FeatureRegistry('m',tmp_path);b=FeatureRegistry('m',tmp_path);barrier=threading.Barrier(2);errors=[]
 def run(r,prefix):
  try:
   barrier.wait(5)
   for i in range(10):r.save_proposal(f'{prefix}{i}',name='demo',kind='generic',code='code',test_code='',gap_signature='')
  except BaseException as e:errors.append(e)
 threads=[threading.Thread(target=run,args=(r,p)) for r,p in ((a,'a'),(b,'b'))]
 for t in threads:t.start()
 for t in threads:t.join(10);assert not t.is_alive()
 assert not errors and len(a.proposals())==20
