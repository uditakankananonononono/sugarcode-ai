import sys; sys.path.insert(0,'src')
from sugarcode.extra_doc.text_profile import profile
import pytest

class TestAud:
    def test_audpin_mixed_554(self):
        got = profile('Hello, WORLD! 3.5 x9 x9 Ab.')
        assert got['words'] == 7 and got['distinct'] == 6
        assert got['sentences'] == 3
        assert got['longest'] == 'hello'
        assert got['top'] == [('x9',2),('3',1),('5',1)]
    def test_audpin_empty_554(self):
        assert profile('') == {'words':0,'distinct':0,'sentences':0,'longest':None,'top':[]}
    def test_audpin_trailing_no_terminator_554(self):
        got = profile('no terminator here')
        assert got['sentences'] == 1 and got['words'] == 3 and got['longest'] == 'terminator'
    def test_audpin_stops_only_no_words_554(self):
        got = profile('!?.')
        assert got['sentences'] == 0 and got['words'] == 0
    def test_audpin_cap_554(self):
        with pytest.raises(ValueError): profile('a'*2001)
        assert profile('a'*2000)['words'] == 1
