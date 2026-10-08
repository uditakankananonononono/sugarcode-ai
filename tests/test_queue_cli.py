import json,subprocess,sys,os
from pathlib import Path

def invoke(tmp_path,*args):
 env=dict(os.environ,PYTHONPATH=str(Path(__file__).resolve().parents[1]/'src'))
 return subprocess.run([sys.executable,'-m','sugarcode.cli','queue','--db',str(tmp_path/'q'),*args],capture_output=True,text=True,env=env)

def test_real_product_submit_run_receipt_verify(tmp_path):
 script=tmp_path/'script.py';script.write_text('print(6*7)')
 for args in [('submit','real','--script',str(script)),('run',),('show','real'),('receipt','real','--out',str(tmp_path/'r')),('verify','--receipt',str(tmp_path/'r'))]:
  p=invoke(tmp_path,*args);assert p.returncode==0,p.stderr+p.stdout
  result=json.loads(p.stdout)
  if args[0]=='show':assert result['state']=='succeeded' and result['stdout']=='42\n'
 assert json.loads((tmp_path/'r').read_text())['stdout']=='42\n'

def test_cancel_and_failure(tmp_path):
 script=tmp_path/'s';script.write_text('raise RuntimeError()')
 assert invoke(tmp_path,'submit','cancel','--script',str(script)).returncode==0
 assert invoke(tmp_path,'cancel','cancel').returncode==0
 assert json.loads(invoke(tmp_path,'show','cancel').stdout)['state']=='cancelled'
 assert invoke(tmp_path,'show','missing').returncode!=0

def test_invalid_script_and_db_are_structured_failures(tmp_path):
 script=tmp_path/'invalid';script.write_bytes(b'\xff')
 p=invoke(tmp_path,'submit','bad','--script',str(script))
 assert p.returncode==1 and json.loads(p.stdout)['status']=='failed' and 'Traceback' not in p.stderr
 (tmp_path/'q').write_text('not SQLite')
 p=invoke(tmp_path,'show','bad')
 assert p.returncode==1 and json.loads(p.stdout)['status']=='failed' and 'Traceback' not in p.stderr
