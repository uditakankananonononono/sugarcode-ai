from collections import Counter
import random
import pytest
from sugarcode.extra_doc.ethnography1732 import tally


def test_independent_flattened_note_oracle():
    rng=random.Random(1732)
    for _ in range(100):
        rows=[(str(i),rng.choice('ab'),rng.sample(list('wxyz'),rng.randrange(5))) for i in range(20)];got=tally(rows)
        assert got['code_counts']==sorted(Counter(c for n,s,codes in rows for c in codes).items())
        assert got['setting_counts']==sorted(Counter(s for n,s,codes in rows).items())
        expected=[]
        for c in sorted({c for n,s,codes in rows for c in codes}):
            settings=sorted({s for n,s,codes in rows if c in codes})
            if len(settings)==1:expected.append((c,settings[0]))
        assert got['single_setting_codes']==expected and got['claim']=='PARTIAL' and got['interpretation_validated'] is False

class L(list):pass
class T(tuple):pass
class S(str):pass
@pytest.mark.parametrize('notes,message',[
 (L(),'notes must be an exact list with 0..100 entries'),
 ([(str(i),'a',[]) for i in range(101)],'notes must be an exact list with 0..100 entries'),
 ([T(('a','b',[]))],'note must be an id setting codes tuple'),
 ([('a','b',[],1)],'note must be an id setting codes tuple'),
 *[([(x,'b',[])],'note IDs must be unique valid labels') for x in (S('a'),'\t','\u00a0','\u3000','\u2003','\u0085','x'*81)],
 ([('a',S('b'),[])],'setting must be a valid label'),
 *[([('a','b',x)],'codes must be an exact list of 0..20 unique valid labels') for x in (L(),list(map(str,range(21))),[S('a')],['a','a'])],
])
def test_invalid(notes,message):
    with pytest.raises(ValueError) as exc:tally(notes)
    assert str(exc.value)==message


def test_caps_labels_and_empty():
    codes=list(map(str,range(20)));rows=[(str(i),'x'*80,codes[:]) for i in range(100)]
    assert tally(rows)['code_counts']==[(str(i),100) for i in sorted(range(20),key=str)]
    assert tally([('\u200b','x',[])])['setting_counts']==[('x',1)]
    assert tally([])['code_counts']==[]
