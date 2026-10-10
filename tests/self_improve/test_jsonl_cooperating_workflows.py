"""Real module logs, restarted objects and cooperating writers; synthetic paths."""
import json
import multiprocessing as mp
import os
import threading
import time

import pytest

from sugarcode.self_improve import engine as em, events as ev, jsonl_store as js
from sugarcode.self_improve.capped_readers import InputLimitExceeded
from sugarcode.self_improve.engine import SelfImprovementEngine
from sugarcode.self_improve.events import GapEvent, GapEventStore
from sugarcode.self_improve.state_lock import shared_state_lock


def objects(root, kind):
    if kind == 'ledger':
        obj = SelfImprovementEngine(module_id=1, module_slug='m', state_dir=root)
        return obj, obj._ledger_path, lambda: obj._log('next'), obj.ledger, em
    obj = GapEventStore(root)
    return obj, obj._path('m'), lambda: obj.append(GapEvent('m', 'next')), lambda: obj.all('m'), ev


@pytest.mark.parametrize('kind', ['events', 'ledger'])
@pytest.mark.parametrize('tail', [b'', b'\r', b'\n', b'\r\n'])
def test_restart_preserves_original_bytes_and_delimits_valid_final_row(tmp_path, kind, tail):
    _, path, append, read, _ = objects(tmp_path, kind)
    row = (b'{"module":"m","event":"old"}' if kind == 'ledger'
           else b'{"module_slug":"m","signature":"old"}')
    prior = b'\n' + row + tail
    path.write_bytes(prior)
    assert len(read()) == 1
    append()
    assert path.read_bytes().startswith(prior + (b'\n' if not prior.endswith(b'\n') else b''))
    _, _, _, restarted, _ = objects(tmp_path, kind)
    assert len(restarted()) == 2


@pytest.mark.parametrize('kind', ['events', 'ledger'])
@pytest.mark.parametrize('bad', ['partial', 'duplicate', 'foreign', 'nonfinite'])
def test_invalid_history_refuses_append_unchanged(tmp_path, kind, bad):
    _, path, append, _, _ = objects(tmp_path, kind)
    field = 'module' if kind == 'ledger' else 'module_slug'
    row = {field: 'm', 'signature': 'old'}
    if bad == 'partial': raw = b'{'
    elif bad == 'duplicate': raw = ('{"%s":"m","%s":"m"}' % (field, field)).encode()
    elif bad == 'foreign': row[field] = 'other'; raw = json.dumps(row).encode()
    else: row['value'] = float('nan'); raw = json.dumps(row).encode()
    path.write_bytes(raw)
    caught = None
    try: append()
    except ValueError as exc: caught = exc
    assert caught is not None, 'invalid history was admitted'
    assert path.read_bytes() == raw


@pytest.mark.parametrize('budget', ['file', 'line'])
@pytest.mark.parametrize('extra', [0, 1])
def test_delimiter_is_charged_at_exact_budget(tmp_path, budget, extra):
    path = tmp_path / 'boundary.jsonl';prior = b'{"x":0}';new = b'0\n'
    path.write_bytes(prior)
    file_cap = len(prior) + 1 + len(new) - extra if budget == 'file' else 100
    line_cap = len(prior) + 1 - extra if budget == 'line' else 100
    decode = lambda rows: [json.loads(row) for row in rows]
    if extra:
        caught = None
        try: js.append_jsonl(path, new, max_file_bytes=file_cap, max_line_bytes=line_cap, decode=decode)
        except InputLimitExceeded as exc: caught = exc
        assert caught is not None, 'delimiter escaped admission budget'
        assert caught.scope == budget and path.read_bytes() == prior
    else:
        js.append_jsonl(path, new, max_file_bytes=file_cap, max_line_bytes=line_cap, decode=decode)
        assert path.read_bytes() == prior+b'\n'+new


def test_record_gap_restart_detection_and_ledger_roundtrip(tmp_path):
    engine = SelfImprovementEngine(module_id=1, module_slug='m', state_dir=tmp_path)
    engine.record_gap('needs filter', detail='first', exemplar={'title':'grant'})
    engine.record_gap('needs filter', detail='second', exemplar='grant')
    restarted = SelfImprovementEngine(module_id=1, module_slug='m', state_dir=tmp_path)
    assert [r['event'] for r in restarted.ledger()] == ['gap_event_recorded']*2
    assert [e.detail for e in restarted.store.all('m')] == ['first', 'second']
    assert restarted.detect_gaps()[0].occurrences == 2
    assert restarted.ledger()[-1]['event'] == 'gap_detected'


@pytest.mark.parametrize('kind', ['events', 'ledger'])
def test_two_object_admission_serializes_forced_read_overlap(tmp_path, monkeypatch, kind):
    _, path, append1, read, module = objects(tmp_path, kind)
    _, _, append2, _, _ = objects(tmp_path, kind)
    # Measure one valid production record; reset history, then exactly one fits.
    append1();cap=path.stat().st_size;path.write_bytes(b'')
    monkeypatch.setattr(module, 'JSONL_FILE_BYTES', cap+8)
    real_read = js.read_capped_bytes
    first_read = threading.Event();second_started = threading.Event()
    calls=[]
    def delayed(*args, **kwargs):
        raw=real_read(*args, **kwargs);calls.append(len(raw))
        if len(calls)==1:
            first_read.set()
            assert second_started.wait(2)
            # Keep admission paused so an unlocked second writer gets stale bytes.
            time.sleep(.1)
        return raw
    monkeypatch.setattr(js, 'read_capped_bytes', delayed)
    receipts=[]
    def run(append, second=False):
        if second: second_started.set()
        try: append();receipts.append('admitted')
        except InputLimitExceeded: receipts.append('refused')
        except BaseException as exc: receipts.append(type(exc).__name__)
    a=threading.Thread(target=run,args=(append1,),daemon=True)
    b=threading.Thread(target=run,args=(append2,True),daemon=True)
    a.start();assert first_read.wait(2);b.start();a.join(3);b.join(3)
    assert not a.is_alive() and not b.is_alive()
    assert sorted(receipts)==['admitted','refused'], receipts
    assert path.stat().st_size<=cap+8 and len(read())==1
    assert calls[0]==0 and calls[1]>0, 'second admission read stale history'


def spawn_writer(root, kind, cap, pipe):
    try:
        _, _, append, _, module = objects(root, kind)
        module.JSONL_FILE_BYTES=cap
        pipe.send('ready');assert pipe.recv()=='go'
        try: append();pipe.send('admitted')
        except InputLimitExceeded: pipe.send('refused')
    except BaseException as exc: pipe.send(('error', type(exc).__name__, str(exc)))
    finally: pipe.close()


@pytest.mark.parametrize('kind', ['events', 'ledger'])
def test_spawned_writers_parent_held_path_lock_delays_admission(tmp_path, kind):
    _, path, append, read, _ = objects(tmp_path, kind)
    append();cap=path.stat().st_size+8;path.write_bytes(b'')
    ctx=mp.get_context('spawn');children=[]
    try:
        for _ in range(2):
            parent, child=ctx.Pipe();process=ctx.Process(target=spawn_writer,args=(tmp_path,kind,cap,child))
            process.start();child.close();children.append((process,parent))
            assert parent.poll(5) and parent.recv()=='ready'
        with shared_state_lock(path):
            for _,pipe in children:pipe.send('go')
            assert not any(pipe.poll(.15) for _,pipe in children), 'writer bypassed held sidecar'
            assert path.read_bytes()==b''
        receipts=[]
        for process,pipe in children:
            assert pipe.poll(5);receipts.append(pipe.recv());process.join(5)
            assert not process.is_alive() and process.exitcode==0
        assert sorted(receipts)==['admitted','refused'], receipts
        assert path.stat().st_size<=cap and len(read())==1
    finally:
        for process,pipe in children:
            if process.is_alive():process.terminate();process.join(3)
            pipe.close()


@pytest.mark.parametrize('failure', ['short', 'zero', 'partial_error'])
def test_append_short_write_or_error_outcome_is_not_atomic(tmp_path, monkeypatch, failure):
    path=tmp_path/'write.jsonl';new=b'{"x":1}\n';real_write=js.os.write;calls=[]
    def write(fd, data):
        calls.append(len(data))
        if failure=='zero':return 0
        if failure=='partial_error' and len(calls)>1:raise OSError('injected write error')
        return real_write(fd,data[:2])
    with monkeypatch.context() as patch:
        patch.setattr(js.os,'write',write)
        if failure=='short':js.append_jsonl(path,new,max_file_bytes=100,max_line_bytes=100,decode=lambda rows:None)
        else:
            with pytest.raises(OSError):js.append_jsonl(path,new,max_file_bytes=100,max_line_bytes=100,decode=lambda rows:None)
    assert path.read_bytes()==(new if failure=='short' else b'' if failure=='zero' else new[:2])
    if failure=='partial_error':
        before=path.read_bytes()
        with pytest.raises(ValueError):js.append_jsonl(path,new,max_file_bytes=100,max_line_bytes=100,
                                                   decode=lambda rows:[json.loads(row) for row in rows])
        assert path.read_bytes()==before
