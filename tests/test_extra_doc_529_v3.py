import copy
import hashlib
import re
import pytest
from sugarcode.extra_doc.audit_logging import chain, verify

class L(list): pass
class T(tuple): pass
class S(str): pass
class I(int): pass
class LyingInt(int):
    def __lt__(self, other): return False

EV = [(1, 5, 'a'), (2, 5, 'b')]

def with_digests(events):
    prev = '0'*64; out = []
    for seq, ts, action in events:
        prev = hashlib.sha256('|'.join([prev, str(seq), str(ts), action]).encode()).hexdigest()
        out.append((seq, ts, action, prev))
    return out

ROWS = with_digests(EV)

def refused(fn, rows, message):
    with pytest.raises(ValueError, match='^' + re.escape(message) + '$'):
        fn(rows)

@pytest.mark.parametrize('fn,label,rows', [(chain,'events',EV), (verify,'rows',ROWS)])
@pytest.mark.parametrize('container', [L, T])
def test_container_subclasses(fn, label, rows, container):
    refused(fn, container(rows), label + ': list required')
    suffix = ', digest' if fn is verify else ''
    refused(fn, [rows[0], container(rows[1])], label+'[1]: (seq, ts, action'+suffix+') required')

@pytest.mark.parametrize('fn,label,rows', [(chain,'events',EV), (verify,'rows',ROWS)])
@pytest.mark.parametrize('slot', range(4))
def test_scalar_subclasses_nonfirst(fn, label, rows, slot):
    if slot == 3 and fn is chain: return
    row = list(rows[1]); row[slot] = I(row[slot]) if slot < 2 else S(row[slot])
    messages = ['seq: integer required', 'ts: integer required',
                'action: non-empty string up to 60 characters required',
                'digest: 64 lowercase hex characters required']
    refused(fn, [rows[0], tuple(row)], label+'[1] '+messages[slot])

@pytest.mark.parametrize('fn,label,rows', [(chain,'events',EV), (verify,'rows',ROWS)])
def test_lying_timestamp_subclass(fn, label, rows):
    row = list(rows[1]); row[1] = LyingInt(4)
    refused(fn, [rows[0], tuple(row)], label+'[1] ts: integer required')

@pytest.mark.parametrize('fn,label,rows', [(chain,'events',EV), (verify,'rows',ROWS)])
def test_full_errors_nonfirst(fn, label, rows):
    refused(fn, None, label+': list required')
    refused(fn, [], label+': 1 to 1000 entries required')
    refused(fn, [None]*1001, label+': 1 to 1000 entries required')
    count = 4 if fn is verify else 3
    for bad in ((), rows[1][:-1], rows[1]+(0,)):
        refused(fn, [rows[0], bad], label+'[1]: '+str(count)+' entries required')
    cases = [(0,0,'seq: must be within 1 to 1000'),
             (0,1001,'seq: must be within 1 to 1000'), (0,3,'seq: must be 2'),
             (1,-1,'ts: must be within 0 to 1000000000000'),
             (1,10**12+1,'ts: must be within 0 to 1000000000000'),
             (1,4,'ts: must not decrease'),
             (2,'','action: non-empty string up to 60 characters required'),
             (2,'x'*61,'action: non-empty string up to 60 characters required'),
             (2,'a\ud800b','action: lone surrogate characters are not allowed')]
    if fn is verify:
        cases += [(3,d,'digest: 64 lowercase hex characters required')
                  for d in ('0'*63,'0'*65,'A'*64,'g'*64,None)]
    for slot, value, message in cases:
        row = list(rows[1]); row[slot] = value
        refused(fn, [rows[0], tuple(row)], label+'[1] '+message)

@pytest.mark.parametrize('outer', [list, tuple])
@pytest.mark.parametrize('row_type', [list, tuple])
def test_plain_container_support_boundaries_and_unchanged(outer, row_type):
    events = outer([row_type((1,0,'x'*60)), row_type((2,10**12,'y'))])
    before = copy.deepcopy(events)
    out = chain(events); expected = with_digests(events)
    assert [(r['seq'],r['ts'],r['action'],r['digest']) for r in out['events']] == expected
    rows = outer(row_type(r) for r in expected); row_before = copy.deepcopy(rows)
    assert verify(rows)['ok'] is True
    assert events == before and rows == row_before


def test_recomputed_rewrite_is_not_authenticated():
    original = with_digests(EV)
    rewritten = with_digests([(1,5,'different'),(2,5,'b')])
    assert original[-1][3] != rewritten[-1][3]
    assert verify(rewritten)['ok'] is True
    altered = [original[0], (2,5,'different',original[1][3])]
    assert verify(altered)['first_bad'] == 1
