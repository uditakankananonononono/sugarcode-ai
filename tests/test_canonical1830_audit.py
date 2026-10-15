import unittest,itertools as it,random
from sugarcode.extra_doc import canonical1830 as m
import test_canonical1830_lane1 as builder

def oracle(a,b):
    best=max(len(a),len(b));ways=0
    def script(i,j,c):
        nonlocal best,ways
        if c>best:return
        if i==len(a) and j==len(b):
            if c<best:best=c;ways=0
            ways+=1;return
        if i<len(a):script(i+1,j,c+1)
        if j<len(b):script(i,j+1,c+1)
        if i<len(a) and j<len(b):script(i+1,j+1,c+(a[i]!=b[j]))
    script(0,0,0)
    return dict(edit_distance=best,optimal_alignment_paths=ways,digitization_validated=False)
def exact(a,b):
    assert type(a) is type(b)
    if type(b) is dict:
        assert list(a)==list(b)
        for k in b:exact(a[k],b[k])
    else:assert a==b

def check(a,b):
    old=(a,b);out=m.alignment(a,b);expect=oracle(a,b);exact(out,expect);assert (a,b)==old;out.clear();exact(m.alignment(a,b),expect)
class Quick(unittest.TestCase):
    def test_valid(self):
        exact(m.SCOPE,'PARTIAL: caller printable transcription edit distance and optimal alignment path count');assert type(m.NOT_CLAIMED) is tuple;assert m.NOT_CLAIMED==('actual digitization','OCR accuracy','historical authenticity')
        for a,b in (('aa','a'),('a','aa'),('ab','ba'),(' '*8,' '*8),('a'*8,'b'*8),('a'*8,'a'),('~',' '*8),('abababab','babababa')):check(a,b)
        assert m.alignment('aa','a')['optimal_alignment_paths']==2;assert m.alignment('ab','ba')['optimal_alignment_paths']==3
        for c in map(chr,range(32,127)):check(c,' ');check(' ',c)
    def test_validation(self):
        old=builder.m;builder.m=m
        try:builder.test_caps_slots_firstbad()
        finally:builder.m=old
        for side,key in enumerate(('left','right')):
            for v in (True,False,0.0,{},(),b'a'):
                args=['a','a'];args[side]=v
                try:m.alignment(*args)
                except ValueError as e:assert str(e)==key+' exact str1..8'
                else:raise AssertionError('accepted')
class Exhaustive(unittest.TestCase):
    def test_binary(self):
        seqs=[''.join(chars) for n in range(1,5) for chars in it.product('ab',repeat=n)]
        for a,b in it.product(seqs,repeat=2):check(a,b)
    def test_random(self):
        rng=random.Random(91830)
        for _ in range(150):check(*[''.join(chr(rng.randrange(32,127)) for _ in range(rng.randrange(1,9))) for _ in range(2)])
