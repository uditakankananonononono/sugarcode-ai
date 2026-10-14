import sys; sys.path.insert(0,'src')
from sugarcode.extra_doc.auxiliary_indirect_inference import compare as c58
from sugarcode.extra_doc.gaussian_synthetic_likelihood import compare as c57
from math import log
import pytest

class TestAud:
    def test_audpin_1058_tie_first_wins(self):
        got = c58({'observed':[1,2,3],'candidates':[['a',[1,2,3]],['b',[5,5,5]]],'weights':[1,1]})
        assert got['observed'] == {'mean':[2,1],'variance':[1,1]}
        assert got['fitted']['a'] == {'mean':[2,1],'variance':[1,1],'distance':[0,1]}
        assert got['fitted']['b']['variance'] == [0,1]
        assert got['best'] == 'a'
        assert got['claims'] == [False,False,False,False]
    def test_audpin_1058_weights_flip_best(self):
        d = {'observed':[0,2],'candidates':[['a',[1,-1]],['b',[2,2,0]]],'weights':[1,9]}
        assert c58(d)['best'] == 'a'
        assert c58(dict(d,weights=[9,1]))['best'] == 'b'
    def test_audpin_1057_score_and_best(self):
        got = c57({'observed':0,'candidates':[['a',[1,-1,0]],['b',[9,-9,0]]]})
        assert got['best'] == 'a'
        fa = got['fitted']['a']
        assert fa['mean'] == [0,1] and fa['variance'] == [1,1] and fa['discrepancy'] == [0,1]
        assert abs(fa['score'] - (log(1.0)+0.0)/2) < 1e-15
    def test_audpin_1057_zero_variance_refused(self):
        with pytest.raises(ValueError): c57({'observed':0,'candidates':[['a',[5,5]],['b',[1,-1]]]})
    def test_audpin_1058_zero_variance_allowed(self):
        got = c58({'observed':[3,3],'candidates':[['a',[3,3]],['b',[0,1]]],'weights':[1,1]})
        assert got['best'] == 'a'
