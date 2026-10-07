import numpy as np
import pytest
from sugarcode.modules.liquid_biopsy import core as lb

def test_no_cancer_or_tissue_prediction_without_fitted_model():
    result=lb.integrate_multiomics([.1,.2],[.7],[1.2,.8],[.4])
    assert result['cancer_probability'] is None and result['tissue_of_origin'] is None
    assert result['tissue_probabilities']=={}
    assert result['model_status']=='Missing fitted model; supplied modality summaries only'

def test_fitted_multimodal_classifier_learns_and_evaluates_unseen_samples():
    assert hasattr(lb,'fit_multiomics_classifier')
    rng=np.random.default_rng(12)
    X=rng.normal(0,1,(160,4)); labels=np.where(X[:,0]+X[:,1]>0,'case','control').tolist()
    model=lb.fit_multiomics_classifier(X[:120],labels[:120],feature_names=['ctDNA','methylation','proteomics','metabolomics'])
    metrics=lb.evaluate_multiomics_classifier(model,X[120:],labels[120:])
    assert metrics['accuracy']>.85 and metrics['sample_count']==40
    assert metrics['accuracy']>metrics['majority_baseline_accuracy']+.15
    p=lb.predict_multiomics_classifier(model,X[120:])
    assert np.allclose(np.sum(p['probabilities'],axis=1),1)
    assert model['trained'] is True and model['sample_count']==120
    assert metrics['scope']=='Supplied labeled evaluation set; independence and assay validity not verified'

@pytest.mark.parametrize('X,y', [([[1,2],[3,4]],['case','case']), ([[1,np.nan],[2,3]],['a','b']), ([[1,2]],['a','b']), ([[1,2],[3,4]],['a',None])])
def test_training_requires_valid_labeled_matrix(X,y):
    assert hasattr(lb,'fit_multiomics_classifier')
    with pytest.raises(ValueError): lb.fit_multiomics_classifier(X,y)

def test_consensus_is_an_uncalibrated_score_not_somatic_probability():
    r=lb.consensus_denoise(np.ones((2,4,4))*.1)
    assert 'somatic_probability' not in r and 'evidence_score' in r
    assert r['calibrated'] is False

def test_model_training_api_exported_from_package():
    import sugarcode.modules.liquid_biopsy as package
    assert callable(package.fit_multiomics_classifier)

@pytest.mark.parametrize('features,error_prior',[(np.ones((0,3,4)),.001),(np.full((2,3,4),np.nan),.001),(np.ones((2,3,4))*2,.001),(np.ones((2,3,4)),-1)])
def test_consensus_rejects_nonphysical_fragments(features,error_prior):
    with pytest.raises(ValueError): lb.consensus_denoise(features,error_prior=error_prior)

def test_fitted_four_modality_model_drives_integration_not_invented_tissue_signature():
    names=['ctDNA','methylation','proteomics','metabolomics']
    model=lb.fit_multiomics_classifier([[0,0,0,0],[.1,.1,.1,.1],[.9,.9,.9,.9],[1,1,1,1]],['low','low','high','high'],feature_names=names)
    result=lb.integrate_multiomics([1],[1],[1],[1],model=model)
    assert result['fitted_classification']['predicted_labels']==['high']
    assert result['cancer_probability'] is None
