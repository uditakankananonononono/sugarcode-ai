import copy
import numpy as np
import pytest
from sugarcode.modules.liquid_biopsy.multiomics import fit_multiomics_classifier as fit, predict_multiomics_classifier as predict, evaluate_multiomics_classifier as evaluate

def model(): return fit([[0,0],[1,1],[2,2],[3,3]],['a','a','b','b'])

@pytest.mark.parametrize('bad',[{'classes':[1,2]}, {'class_counts':{'a':-1,'b':0}}, {'class_counts':{'a':1}}, {'feature_names':['duplicate','duplicate']}])
def test_stored_model_contract_checked_before_prediction_or_baseline(bad):
    m=model();m.update(bad)
    with pytest.raises(ValueError): evaluate(m,[[1,1]],['a'])

def test_input_serialization_never_loses_feature_order():
    m=model()
    assert m['feature_names']==['feature_0','feature_1']
    result=predict(m,[[.1,.1]])
    assert result['feature_names']==m['feature_names']

def test_evaluation_does_not_mutate_fitted_parameters():
    m=model();saved=copy.deepcopy(m)
    evaluate(m,[[1,1]],['a'])
    assert m==saved
