from functools import lru_cache
from itertools import product
from copy import deepcopy
import random
import pytest
from sugarcode.extra_doc import canonical1830 as m


@pytest.fixture(autouse=True)
def pure(monkeypatch):
    orig=m.alignment
    def checked(*a):
        before=deepcopy(a)
        try:return orig(*a)
        finally:assert a==before
    monkeypatch.setattr(m,'alignment',checked)


def exact(a,b):
    assert type(a) is type(b)
    if type(b) is dict:
        assert list(a)==list(b)
        for k in b:exact(a[k],b[k])
    elif type(b) is bool:assert a is b
    else:assert a==b


def oracle(a,b):
    @lru_cache(None)
    def walk(x,y):
        if not x and not y:return (0,1)
        options=[]
        if x:
            c,k=walk(x[1:],y);options.append((c+1,k))
        if y:
            c,k=walk(x,y[1:]);options.append((c+1,k))
        if x and y:
            c,k=walk(x[1:],y[1:]);options.append((c+int(x[0]!=y[0]),k))
        best=min(c for c,k in options);return best,sum(k for c,k in options if c==best)
    c,k=walk(a,b)
    return dict(edit_distance=c,optimal_alignment_paths=k,digitization_validated=False)


def test_recursive_suffix_alignment_oracle():
    seqs=[''.join(s) for n in range(1,5) for s in product('ab',repeat=n)]
    for a,b in product(seqs,repeat=2):exact(m.alignment(a,b),oracle(a,b))
    rng=random.Random(1830)
    for _ in range(150):
        a=''.join(chr(rng.randint(32,126)) for i in range(rng.randint(1,8)));b=''.join(chr(rng.randint(32,126)) for i in range(rng.randint(1,8)));exact(m.alignment(a,b),oracle(a,b))
    for a,b in ((' '*8,' '*8),('a'*8,'b'*8),('a'*8,'a')):exact(m.alignment(a,b),oracle(a,b))
    assert m.alignment('aa','a')['optimal_alignment_paths']==2
    for c in map(chr,range(32,127)):
        for a,b in ((c,' '),(' ',c)):exact(m.alignment(a,b),oracle(a,b))


class S(str):pass


def test_caps_slots_firstbad():
    for side,name in enumerate(('left','right')):
        for v in (None,[],1,S('a'),'','a'*9):
            a=['a','a'];a[side]=v
            with pytest.raises(ValueError) as e:m.alignment(*a)
            assert str(e.value)==name+' exact str1..8'
        for pos in range(8):
            for c in (chr(31),chr(127),'é'):
                text=list(' '*8);text[pos]=c;a=['a','a'];a[side]=''.join(text)
                with pytest.raises(ValueError) as e:m.alignment(*a)
                assert str(e.value)==name+' printable ASCII32..126'
    with pytest.raises(ValueError,match='left exact'):m.alignment(None,None)
    with pytest.raises(ValueError,match='left printable'):m.alignment(chr(31),None)
    assert m.SCOPE=='PARTIAL: caller printable transcription edit distance and optimal alignment path count'
    assert m.NOT_CLAIMED==('actual digitization','OCR accuracy','historical authenticity')
