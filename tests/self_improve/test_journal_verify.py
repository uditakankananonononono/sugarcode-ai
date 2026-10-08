import pytest
import hashlib,json
from sugarcode.self_improve.events import GapEvent,GapEventStore

def test_actual_prefix_partial_tail_and_no_mutation(tmp_path):
 from sugarcode.self_improve.journal_verify import inspect_journal
 store=GapEventStore(tmp_path);store.append(GapEvent('tools','identity'))
 p=next(tmp_path.glob('*.jsonl'));prefix=p.read_bytes();p.write_bytes(prefix+b'{"partial":');before=p.read_bytes()
 r=inspect_journal(p)
 assert r['status']=='partial_tail' and r['verified_prefix_events']==1
 assert r['verified_prefix_bytes']==len(prefix) and r['prefix_sha256']==hashlib.sha256(prefix).hexdigest()
 assert r['error_line']==2 and p.read_bytes()==before

def test_complete_malformed_or_wrong_event_is_corrupt(tmp_path):
 from sugarcode.self_improve.journal_verify import inspect_journal
 p=tmp_path/'tools.gap-events.jsonl'
 for data in [b'{broken}\n',b'{"module_slug":"tools","signature":"x","kind":"invented"}\n',b'{"module_slug":"other","signature":"x"}\n']:
  p.write_bytes(data);r=inspect_journal(p);assert r['status']=='corrupt' and r['verified_prefix_events']==0

def test_complete_final_event_and_limits(tmp_path):
 from sugarcode.self_improve.journal_verify import inspect_journal
 p=tmp_path/'tools.gap-events.jsonl';p.write_text(json.dumps({'module_slug':'tools','signature':'x','event_id':'one','at':1}))
 assert inspect_journal(p)['status']=='verified'
 assert inspect_journal(p,max_line_bytes=10)['status']=='limit_exceeded'
 p.write_text(p.read_text()+'\n'+p.read_text()+'\n');assert inspect_journal(p)['status']=='corrupt'

@pytest.mark.parametrize('depth',[10000,100000,524000])
@pytest.mark.parametrize('terminated',[True,False])
def test_real_deep_json_status(tmp_path,depth,terminated):
 from sugarcode.self_improve.journal_verify import inspect_journal
 p=tmp_path/'tools.gap-events.jsonl';prefix=b'{"module_slug":"tools","signature":"x"}\n'
 p.write_bytes(prefix+b'['*depth+b']'*depth+(b'\n' if terminated else b''))
 r=inspect_journal(p)
 assert r['status'] in {'corrupt','depth_exceeded'} and r['verified_prefix_events']==1 and r['error_line']==2

@pytest.mark.parametrize('payload',[b'['*50000+b']'*50000+b'\n',b'['*50000],ids=['complete-50000','unterminated-50000'])
def test_reviewer_exact_deep_payload(tmp_path,payload):
 from sugarcode.self_improve.journal_verify import inspect_journal
 p=tmp_path/'tools.gap-events.jsonl';p.write_bytes(b'{"module_slug":"tools","signature":"x"}\n'+payload)
 r=inspect_journal(p);assert r['status']=='depth_exceeded' and r['verified_prefix_events']==1 and r['error_line']==2

@pytest.mark.parametrize('error,status',[(MemoryError,'resource_exceeded'),(OSError,'io_error'),(UnicodeDecodeError,'corrupt')])
def test_faults_have_inspection_status(tmp_path,monkeypatch,error,status):
 from sugarcode.self_improve import journal_verify as module
 p=tmp_path/'tools.gap-events.jsonl';p.write_text('{"module_slug":"tools","signature":"x"}\n')
 def fail(*args):
  if error is UnicodeDecodeError:raise error('utf8',b'x',0,1,'invalid')
  raise error('instrumented fault')
 monkeypatch.setattr(module.json,'loads',fail)
 r=module.inspect_journal(p);assert r['status']==status and r['error_line']==1

def test_read_io_error_status(tmp_path,monkeypatch):
 from sugarcode.self_improve.journal_verify import inspect_journal
 p=tmp_path/'tools.gap-events.jsonl';p.write_text('{}')
 def fail(*args,**kwargs):raise OSError('instrumented read fault')
 monkeypatch.setattr(type(p),'open',fail)
 assert inspect_journal(p)['status']=='io_error'
