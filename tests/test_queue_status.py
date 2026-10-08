import pytest
from sugarcode.runtime.job_queue import Queue

def test_actual_status_excludes_code_and_results(tmp_path):
 q=Queue(tmp_path/'q')
 q.submit('first','print("private script")');q.submit('second','print(2)');q.submit('cancel','print(3)');q.cancel('cancel')
 rows=q.status(limit=2)
 assert [x['id'] for x in rows]==['first','second']
 assert all('code' not in x and 'stdout' not in x and 'stderr' not in x for x in rows)
 assert [x['id'] for x in q.status(state='cancelled')]==['cancel']
 q.run_next();assert q.status(state='succeeded')[0]['id']=='first'
 assert q.status(state='failed')==[]

def test_invalid_status_controls(tmp_path):
 q=Queue(tmp_path/'q')
 for cap in [0,-1,True,1.5,1001]:
  with pytest.raises(ValueError):q.status(limit=cap)
 with pytest.raises(ValueError):q.status(state='other')

def test_real_cli_readonly_metadata(tmp_path):
 import subprocess,sys,os,json
 from pathlib import Path
 env=dict(os.environ,PYTHONPATH=str(Path(__file__).resolve().parents[1]/'src'))
 def call(path):return subprocess.run([sys.executable,'-m','sugarcode.cli','queue-status','--db',str(path)],capture_output=True,text=True,env=env)
 missing=tmp_path/'missing';assert call(missing).returncode==1 and not missing.exists()
 q=Queue(tmp_path/'q');q.submit('real','print("secret-code-marker")')
 before=q.path.read_bytes();p=call(q.path)
 assert p.returncode==0 and json.loads(p.stdout)['jobs'][0]['id']=='real'
 assert 'secret-code-marker' not in p.stdout and q.path.read_bytes()==before
