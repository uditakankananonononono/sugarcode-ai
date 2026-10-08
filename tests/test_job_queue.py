import sqlite3,time
from pathlib import Path
import pytest

def test_actual_job_result_and_cancel(tmp_path):
 from sugarcode.runtime.job_queue import Queue
 q=Queue(tmp_path/'queue.sqlite');jid=q.submit('result',"print(6*7)")
 assert q.run_next()=='result';r=q.get(jid);assert r['state']=='succeeded' and r['stdout'].strip()=='42'
 q.submit('cancel','raise RuntimeError()');assert q.cancel('cancel')
 assert q.get('cancel')['state']=='cancelled' and q.run_next() is None
 with pytest.raises(ValueError):q.submit('result','print(99)')

def test_claim_recovery_uncertain_never_auto_retry(tmp_path):
 from sugarcode.runtime.job_queue import Queue
 q=Queue(tmp_path/'q');q.submit('effect','print(1)');claimed=q.claim();assert claimed['state']=='running'
 assert q.reconcile(stale_before=time.time()+1)==1
 assert q.get('effect')['state']=='uncertain' and q.run_next() is None

def test_failure_timeout_and_competing_claims(tmp_path):
 from sugarcode.runtime.job_queue import Queue
 q=Queue(tmp_path/'q');q.submit('failure','raise RuntimeError("actual")');q.run_next();assert q.get('failure')['state']=='failed'
 q.submit('timeout','import time;time.sleep(10)',timeout=.2);q.run_next();assert q.get('timeout')['state']=='timed_out'
 q.submit('single','print(1)');other=Queue(tmp_path/'q');assert q.claim()['id']=='single' and other.claim() is None

def test_actual_crashed_worker_reconciles_uncertain(tmp_path):
 from sugarcode.runtime.job_queue import Queue
 import subprocess,sys,os
 q=Queue(tmp_path/'q');q.submit('crash','print(1)')
 code='from sugarcode.runtime.job_queue import Queue;import os;Queue('+repr(str(tmp_path/'q'))+').claim();os._exit(7)'
 p=subprocess.run([sys.executable,'-c',code],env=dict(os.environ,PYTHONPATH=str(Path(__file__).resolve().parents[1]/'src')))
 assert p.returncode==7 and q.get('crash')['state']=='running'
 assert q.reconcile(stale_before=time.time()+1)==1 and q.get('crash')['state']=='uncertain'
 assert q.run_next() is None

@pytest.mark.parametrize('timeout',[float('nan'),float('inf'),True,'bad'])
def test_invalid_timeout_refuses(tmp_path,timeout):
 from sugarcode.runtime.job_queue import Queue
 q=Queue(tmp_path/'q')
 with pytest.raises(ValueError):q.submit('invalid','print(1)',timeout=timeout)

@pytest.mark.parametrize('field,value',[('timeout','invalid'),('timeout',float('inf')),('timeout',None),('sha256','bad'),('sha256',None),('code',None),('code',b'not text'),('code',123)])
def test_corrupt_persisted_job_never_launches(tmp_path,monkeypatch,field,value):
 from sugarcode.runtime import job_queue as module
 q=module.Queue(tmp_path/'q');q.submit('corrupt','print(1)')
 with sqlite3.connect(q.path) as db:db.execute('UPDATE jobs SET '+field+'=? WHERE id=?',(value,'corrupt'))
 calls=[]
 monkeypatch.setattr(module.subprocess,'Popen',lambda *a,**kw:calls.append(a) or pytest.fail('launched corrupted job'))
 assert q.run_next()=='corrupt'
 result=q.get('corrupt');assert result['state']=='failed' and len(result['stderr'])<=160 and not calls
 assert q.run_next() is None
