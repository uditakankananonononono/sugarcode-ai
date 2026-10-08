import sqlite3,json
import pytest
from sugarcode.runtime.job_queue import Queue

def test_real_42_capture_reproducible_export_and_tamper(tmp_path):
 from sugarcode.runtime.job_receipt import capture,verify,export_json
 q=Queue(tmp_path/'q');q.submit('real','print(6*7)');q.run_next();out=tmp_path/'receipt.json'
 receipt=capture(q,'real',out);assert receipt['stdout']=='42\n' and receipt['exit_code']==0
 assert verify(q,out)['status']=='verified' and export_json(out)==out.read_text()
 with pytest.raises(FileExistsError):capture(q,'real',out)
 with sqlite3.connect(q.path) as db:db.execute("UPDATE jobs SET stdout='tampered' WHERE id='real'")
 with pytest.raises(ValueError):verify(q,out)

def test_pending_uncertain_and_failed_semantics(tmp_path):
 from sugarcode.runtime.job_receipt import capture
 q=Queue(tmp_path/'q');q.submit('pending','print(1)')
 with pytest.raises(ValueError):capture(q,'pending',tmp_path/'p')
 q.claim();q.reconcile(stale_before=1e20)
 with pytest.raises(ValueError):capture(q,'pending',tmp_path/'u')
 q.submit('failed','raise RuntimeError("real")');q.run_next()
 assert capture(q,'failed',tmp_path/'f')['state']=='failed'

def test_receipt_corruption_refused(tmp_path):
 from sugarcode.runtime.job_receipt import capture,verify
 q=Queue(tmp_path/'q');q.submit('real','print(42)');q.run_next();out=tmp_path/'receipt'
 capture(q,'real',out);r=json.loads(out.read_text());r['stdout']='altered';out.write_text(json.dumps(r))
 with pytest.raises(ValueError):verify(q,out)
