import numpy as np
import pytest
from sugarcode.modules.bioimage_ai.core import morphology_table, analyze_microscopy, count_cells, analyze_image, validate_image

def image():
    y,x=np.mgrid[:32,:32]
    return 1+80*np.exp(-((x-16)**2+(y-16)**2)/20)

def test_sparse_label_ids_do_not_generate_nan_phantom_cells():
    labels=np.zeros((32,32),int); labels[8:16,8:16]=7
    cells=morphology_table(image(),{'labels':labels,'pixel_size_um':1})
    assert len(cells)==1 and cells[0]['cell_id']==7
    assert all(np.isfinite(v) for k,v in cells[0].items() if k!='edge_touching')

@pytest.mark.parametrize('label',[-1,1.5,np.nan])
def test_segmentation_labels_must_be_nonnegative_finite_integers(label):
    labels=np.zeros((32,32)); labels[8:16,8:16]=label
    with pytest.raises(ValueError):
        morphology_table(image(),{'labels':labels,'pixel_size_um':1})

@pytest.mark.parametrize('pixel_size',[np.nan,np.inf,True])
def test_pixel_size_is_finite_real_scale(pixel_size):
    with pytest.raises(ValueError):
        validate_image(image(),pixel_size_um=pixel_size)

def test_morphology_is_not_a_health_or_passage_diagnosis():
    result=analyze_microscopy(image())
    assert result['culture_health']['health_score'] is None
    assert result['culture_health']['decision']=='not assessed'
    assert 'not viability' in result['culture_health']['status']

def test_constant_image_reports_zero_detected_objects_not_crash():
    result=analyze_microscopy(np.zeros((32,32)))
    assert result['cells']==[]
    assert result['segmentation']['cell_count']==0
    assert result['culture_health']['decision']=='not assessed'
    assert all(np.isfinite(v) for v in result['diagnostics'].values())

@pytest.mark.parametrize('api',[count_cells,analyze_image])
def test_legacy_entrypoints_validate_finite_image(api):
    img=image(); img[0,0]=np.nan
    with pytest.raises(ValueError):
        api(img)
