import random
import re
import pytest
from sugarcode.extra_doc.discourse1743 import audit_markers


def test_independent_regex_histogram_oracle():
    rng=random.Random(1743);markers=['but','and','However']
    for _ in range(100):
        texts=['\u2003'.join(rng.choices(['but','and','However','BUT','but,','other'],k=rng.randrange(30))) for i in range(20)]
        histograms=[]
        for t in texts:
            hist={}
            for token in re.findall(r'\S+',t):hist[token]=hist.get(token,0)+1
            histograms.append(hist)
        expected=[[h.get(m,0) for m in markers] for h in histograms]
        got=audit_markers(markers,texts);assert got=={'counts':expected,'totals':[(m,sum(h.get(m,0) for h in histograms)) for m in markers],'claim':'PARTIAL','discourse_validated':False}

class L(list):pass
class S(str):pass
@pytest.mark.parametrize('markers',[
 None,L(['a']),('a',),[],list(map(str,range(21))),['a','a'],
 *[[x] for x in (None,True,1,1.5,S('a'),'','\t','\u00a0','\u3000','\u2003','\u0085','a b','a\tb','x'*81)]
])
def test_bad_markers(markers):
    with pytest.raises(ValueError) as exc:audit_markers(markers,[''])
    assert str(exc.value)=='markers must be an exact list of 1..20 unique nonwhitespace tokens of 1..80 characters'

@pytest.mark.parametrize('texts',[
 None,L(['a']),('a',),[],['']*101,
 *[[x] for x in (None,True,1,1.5,S('a'),'x'*1001)]
])
def test_bad_texts(texts):
    with pytest.raises(ValueError) as exc:audit_markers(['a'],texts)
    assert str(exc.value)=='texts must be an exact list of 1..100 exact strings of 0..1000 characters'


def test_caps_and_literal_case_punctuation_zero_width():
    markers=['x'*80]+list(map(str,range(19)));assert len(audit_markers(markers,['x'*1000]*100)['counts'])==100
    assert audit_markers(['x'*80],['x'*80])['totals']==[('x'*80,1)]
    assert audit_markers(['\u200b','but'],['\u200b\tbut but, BUT'])['counts']==[[1,1]]
    assert audit_markers(['a'],[''])['counts']==[[0]]
