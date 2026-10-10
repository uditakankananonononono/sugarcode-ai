import json
import threading
from pathlib import Path
import pytest
from sugarcode.self_improve.engine import SelfImprovementEngine
from sugarcode.self_improve.gate import ManualApprovalGate,APPROVED,REJECTED
from sugarcode.self_improve.registry import FeatureRegistry,RegistryError
from sugarcode.self_improve.plans import Candidate,FeaturePlan
from sugarcode.self_improve.approval_consumption import CONSUMED_KEY
from sugarcode.self_improve import atomic_file as af


def seed(root,gate=None):
 gate=gate or ManualApprovalGate(root/'gate.json',auto_approve=True)
 e=SelfImprovementEngine(module_id=1,module_slug='m',state_dir=root,gate=gate)
 add_version(e,1)
 return e,gate


def add_version(e,n):
 key=f'key{n}'
 e.registry.save_proposal(key,name='demo',kind='generic',code=f'# {n}\ndef run(items,params=None): return items',test_code='',gap_signature='gap')
 e.registry.activate(key,approval_id='seed')


def activation(e):
 c=Candidate(FeaturePlan('m','activated','keyword_filter','d','gap',{}),'def run(items,params=None):return items','')
 e._candidates[c.key]=c
 return c.key,e.propose(c.key)


def test_restore_version_cannot_replay_consumed_rollback(tmp_path):
 e,g=seed(tmp_path);aid=e.request_rollback('demo');e.rollback('demo',approval_id=aid)
 state=e.registry._load();state['features']['demo']['active_version']=1;e.registry._save(state)
 before=e.registry._path.read_bytes()
 with pytest.raises(PermissionError):e.rollback('demo',approval_id=aid)
 assert e.registry._path.read_bytes()==before


def test_activation_approval_consumed_once(tmp_path):
 e,g=seed(tmp_path);key,aid=activation(e);e.activate(key,approval_id=aid)
 before=e.registry._path.read_bytes()
 with pytest.raises(PermissionError):e.activate(key,approval_id=aid)
 assert e.registry._path.read_bytes()==before


def test_consumed_survives_new_objects_and_unused_request_still_works(tmp_path):
 e,g=seed(tmp_path);add_version(e,2);aid=e.request_rollback('demo');e.rollback('demo',approval_id=aid)
 fresh=SelfImprovementEngine(module_id=1,module_slug='m',state_dir=tmp_path,gate=ManualApprovalGate(g._path,auto_approve=True))
 state=fresh.registry._load();state['features']['demo']['active_version']=2;fresh.registry._save(state)
 with pytest.raises(PermissionError):fresh.rollback('demo',approval_id=aid)
 new=fresh.request_rollback('demo');assert fresh.rollback('demo',approval_id=new)['active_version']==1


def test_two_engine_same_approval_barrier_exactly_one_commit(tmp_path):
 e,g=seed(tmp_path);add_version(e,2);aid=e.request_rollback('demo')
 other=SelfImprovementEngine(module_id=1,module_slug='m',state_dir=tmp_path,gate=ManualApprovalGate(g._path,auto_approve=True))
 start=threading.Barrier(3);out=[]
 def run(engine):
  start.wait()
  try:engine.rollback('demo',approval_id=aid);out.append('committed')
  except PermissionError:out.append('refused')
 threads=[threading.Thread(target=run,args=(x,)) for x in (e,other)]
 for t in threads:t.start()
 start.wait()
 for t in threads:t.join(10);assert not t.is_alive()
 assert sorted(out)==['committed','refused']
 assert len(e.registry._load()[CONSUMED_KEY])==1


def test_revoke_before_lock_winner_refuses_then_reapprove_unused(tmp_path):
 e,g=seed(tmp_path);aid=e.request_rollback('demo')
 other=ManualApprovalGate(g._path,auto_approve=True)
 with other._lock:
  other.decide(aid,REJECTED)
 with pytest.raises(PermissionError):e.rollback('demo',approval_id=aid)
 assert CONSUMED_KEY not in e.registry._load()
 other.decide(aid,APPROVED)
 assert e.rollback('demo',approval_id=aid)['rolled_back_from']==1


def test_commit_winning_holds_gate_against_revoke(tmp_path,monkeypatch):
 e,g=seed(tmp_path);aid=e.request_rollback('demo');other=ManualApprovalGate(g._path,auto_approve=True)
 entered=threading.Event();release=threading.Event();revoke_started=threading.Event();revoked=threading.Event();errors=[]
 original=e.registry.rollback
 def pause(*a,**kw):
  entered.set()
  assert g._lock._thread_lock._is_owned(), 'gate lock released before registry commit'
  assert release.wait(5)
  return original(*a,**kw)
 monkeypatch.setattr(e.registry,'rollback',pause)
 def commit():
  try:e.rollback('demo',approval_id=aid)
  except BaseException as exc:errors.append(exc)
 def revoke():revoke_started.set();other.decide(aid,REJECTED);revoked.set()
 t=threading.Thread(target=commit);t.start();assert entered.wait(5)
 r=threading.Thread(target=revoke);r.start();assert revoke_started.wait(5)
 # Shared lock must be held by committing thread; nonblocking acquire is deterministic.
 assert not other._lock._thread_lock.acquire(blocking=False)
 assert not revoked.is_set();release.set();t.join(10);r.join(10)
 assert not errors and revoked.is_set()
 assert e.registry.features()['demo']['active_version'] is None
 assert g.decision(aid)==REJECTED


@pytest.mark.parametrize('value',[None,[],{'bad':{}},True])
def test_corrupt_consumption_metadata_refuses_without_write(tmp_path,value):
 e,g=seed(tmp_path);aid=e.request_rollback('demo');data=e.registry._load();data[CONSUMED_KEY]=value
 raw=json.dumps(data).encode();e.registry._path.write_bytes(raw)
 with pytest.raises(RegistryError):e.rollback('demo',approval_id=aid)
 assert e.registry._path.read_bytes()==raw


@pytest.mark.parametrize('failure',['before','after'])
def test_consumption_atomic_registry_failure_reconciles(tmp_path,monkeypatch,failure):
 e,g=seed(tmp_path);aid=e.request_rollback('demo');before=e.registry._path.read_bytes()
 if failure=='before':
  def fail(*a):raise OSError('before replace')
  monkeypatch.setattr(af.ops,'replace',fail)
 else:
  def fail(*a):raise OSError('after replace')
  monkeypatch.setattr(af,'_fsync_dir',fail)
 with pytest.raises(OSError):e.rollback('demo',approval_id=aid)
 if failure=='before':assert e.registry._path.read_bytes()==before and CONSUMED_KEY not in e.registry._load()
 else:assert e.registry.features()['demo']['active_version'] is None and len(e.registry._load()[CONSUMED_KEY])==1


def test_full_consumption_admission_refuses_unchanged(tmp_path,monkeypatch):
 from sugarcode.self_improve import registry
 e,g=seed(tmp_path);aid=e.request_rollback('demo');before=e.registry._path.read_bytes()
 monkeypatch.setattr(registry,'REGISTRY_FILE_BYTES',len(before)+5)
 with pytest.raises(ValueError):e.rollback('demo',approval_id=aid)
 assert e.registry._path.read_bytes()==before


def test_record_only_custom_gate_explicitly_fails_closed(tmp_path):
 e,g=seed(tmp_path);aid=e.request_rollback('demo')
 class RecordOnly:
  def record(self,id):return g.record(id)
 e.gate=RecordOnly()
 with pytest.raises(PermissionError,match='coordinated'):e.rollback('demo',approval_id=aid)


def test_two_engine_activation_barrier_exactly_one_version(tmp_path):
 e,g=seed(tmp_path);key,aid=activation(e)
 other=SelfImprovementEngine(module_id=1,module_slug='m',state_dir=tmp_path,gate=ManualApprovalGate(g._path,auto_approve=True))
 barrier=threading.Barrier(3);out=[]
 def run(engine):
  barrier.wait()
  try:engine.activate(key,approval_id=aid);out.append('committed')
  except PermissionError:out.append('refused')
 threads=[threading.Thread(target=run,args=(engine,)) for engine in (e,other)]
 for t in threads:t.start()
 barrier.wait()
 for t in threads:t.join(10);assert not t.is_alive()
 assert sorted(out)==['committed','refused']
 assert len(e.registry.features()['activated']['versions'])==1


def test_gate_engine_fixed_lock_order_and_fresh_revoke(tmp_path):
 e,g=seed(tmp_path);aid=e.request_rollback('demo')
 ready=threading.Event();release=threading.Event();results=[]
 def holder():
  with g._lock:
   ready.set();assert release.wait(5);g.decide(aid,REJECTED)
 def commit():
  try:e.rollback('demo',approval_id=aid);results.append('committed')
  except PermissionError:results.append('refused')
 owner=threading.Thread(target=holder);owner.start();assert ready.wait(5)
 t=threading.Thread(target=commit);t.start();release.set();owner.join(10);t.join(10)
 assert results==['refused'] and CONSUMED_KEY not in e.registry._load()


def test_custom_coordinated_gate_interface_with_real_lock_works(tmp_path):
 e,g=seed(tmp_path);aid=e.request_rollback('demo');g.decide(aid,APPROVED)
 class Coordinated:
  def coordinated_record(self,id):return g.coordinated_record(id)
 e.gate=Coordinated()
 assert e.rollback('demo',approval_id=aid)['rolled_back_from']==1


def test_legacy_generic_minimal_decision_survives_coordinated_lock(tmp_path):
 g=ManualApprovalGate(tmp_path/'gate');g._save({'legacy':{'status':'pending'}})
 g.decide('legacy',APPROVED)
 assert g.decision('legacy')==APPROVED


def test_activation_capacity_refusal_leaves_no_extension_or_consumption(tmp_path,monkeypatch):
 from sugarcode.self_improve import registry
 e,g=seed(tmp_path);key,aid=activation(e);before=e.registry._path.read_bytes()
 monkeypatch.setattr(registry,'REGISTRY_FILE_BYTES',len(before)+5)
 with pytest.raises(ValueError):e.activate(key,approval_id=aid)
 assert e.registry._path.read_bytes()==before
 assert not (e.registry._ext_dir/'activated_v1.py').exists()


def test_persistent_consumption_refuses_in_fresh_python_process(tmp_path):
 import subprocess,sys,os
 e,g=seed(tmp_path);aid=e.request_rollback('demo');e.rollback('demo',approval_id=aid)
 data=e.registry._load();data['features']['demo']['active_version']=1;e.registry._save(data)
 script='''import sys
from pathlib import Path
from sugarcode.self_improve.engine import SelfImprovementEngine
from sugarcode.self_improve.gate import ManualApprovalGate
root=Path(sys.argv[1]);e=SelfImprovementEngine(module_id=1,module_slug='m',state_dir=root,gate=ManualApprovalGate(root/'gate.json',auto_approve=True))
try:e.rollback('demo',approval_id=sys.argv[2])
except PermissionError:sys.exit(0)
sys.exit(7)
'''
 env=dict(os.environ,PYTHONPATH=str(Path(__file__).resolve().parents[2]/'src'))
 result=subprocess.run([sys.executable,'-c',script,str(tmp_path),aid],env=env,capture_output=True,timeout=10)
 assert result.returncode==0,result.stderr.decode()


def engine_process(root,aid,barrier,queue):
 try:
  e=SelfImprovementEngine(module_id=1,module_slug='m',state_dir=Path(root),gate=ManualApprovalGate(Path(root)/'gate.json',auto_approve=True))
  barrier.wait(10)
  try:e.rollback('demo',approval_id=aid);queue.put('committed')
  except PermissionError:queue.put('refused')
 except BaseException as exc:queue.put(type(exc).__name__+':'+str(exc))


def test_two_posix_engines_one_approval_commit(tmp_path):
 import multiprocessing as mp
 e,g=seed(tmp_path);add_version(e,2);aid=e.request_rollback('demo')
 ctx=mp.get_context('spawn');barrier=ctx.Barrier(2);queue=ctx.Queue()
 processes=[ctx.Process(target=engine_process,args=(str(tmp_path),aid,barrier,queue)) for _ in range(2)]
 for p in processes:p.start()
 results=[queue.get(timeout=20) for _ in processes]
 for p in processes:p.join(20);assert p.exitcode==0
 assert sorted(results)==['committed','refused']
 assert len(e.registry._load()[CONSUMED_KEY])==1
