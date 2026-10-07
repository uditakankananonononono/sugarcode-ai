import numpy as np
from sugarcode.modules.liquid_biopsy.core import analyze_liquid_biopsy

def test_report_calls_are_positions_not_duplicate_fragment_rows():
    x=np.zeros((3,8,4));x[:,:,1:]=.9;x[:,3,0]=.12
    result=analyze_liquid_biopsy(x,[[0,1],[0,1],[1,0]],[])
    calls=result['position_evidence']
    assert len({c['position_index'] for c in calls})==len(calls)
    hit=next(c for c in calls if c['position_index']==3)
    assert hit['fragments_total']==3 and hit['fragments_supporting']==3
    assert hit['mean_allele_support']==.12
    assert 'not variant allele counts' in hit['status']
    assert result['enhancement_features']['variant_count']==len(calls)

def test_classifier_inference_connected_to_end_to_end_path():
    from sugarcode.modules.liquid_biopsy import fit_multiomics_classifier
    model=fit_multiomics_classifier([[0,0,0,0],[.1,.1,.1,.1],[.9,.9,.9,.9],[1,1,1,1]],['low','low','high','high'],feature_names=['ctDNA','methylation','proteomics','metabolomics'])
    x=np.ones((2,8,4))*.95
    result=analyze_liquid_biopsy(x,[[0],[1]],[],methylation=[1],proteins=[1],metabolites=[1],multiomics_model=model)
    assert result['multiomics']['fitted_classification']['predicted_labels']==['high']
    assert result['report']['cancer_probability'] is None
