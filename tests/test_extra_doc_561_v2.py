import pytest
from sugarcode.extra_doc.fact_extraction import extract, STATUS_NOTE
class S(str):pass
def test_text_subclass():
    with pytest.raises(ValueError,match='^text: string required$'):extract(S('2024-02-29'))
def test_full_calendar_and_percentage_contract():
    text='2024-02-29 2023-02-29 1900-02-29 2000-02-29 5% 1234% 001%'
    result=extract(text)
    assert result=={'dates':[(0,'2024-02-29',2024,2,29),(33,'2000-02-29',2000,2,29)],
                   'percentages':[(44,5),(53,1)],
                   'status_note':'PARTIAL: fixed YYYY-MM-DD and N% patterns only; no other formats, no relative dates and no understanding of what the numbers refer to'}
    assert result['status_note']==STATUS_NOTE
