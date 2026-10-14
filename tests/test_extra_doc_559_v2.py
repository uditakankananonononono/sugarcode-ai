import pytest
from sugarcode.extra_doc.extractive_summary import summarize, STATUS_NOTE
class S(str):pass
class I(int):pass
def test_scalar_subclasses():
    with pytest.raises(ValueError,match='^text: string required$'):summarize(S('red.'))
    with pytest.raises(ValueError,match='^count: integer required$'):summarize('red.',I(1))
def test_full_frequency_distinct_token_tie_and_default():
    text='Red red! Blue? Red blue.'
    result=summarize(text,2)
    assert result=={'sentences':[{'index':0,'score':3,'text':'Red red!'},
                                {'index':2,'score':5,'text':'Red blue.'}],
                   'total_sentences':3,'status_note':'PARTIAL: extractive selection by word frequency only; no rewriting, no understanding of importance or meaning'}
    assert result['status_note']==STATUS_NOTE
    assert summarize(text)==summarize(text,1)
    assert summarize('a! b? c.',2)['sentences']==[{'index':0,'score':1,'text':'a!'}, {'index':1,'score':1,'text':'b?'}]
