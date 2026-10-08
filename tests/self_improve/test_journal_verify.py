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
