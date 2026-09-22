import numpy as np
import pytest
from sugarcode.modules.bioimage_ai import *
def image():
 y,x=np.mgrid[:64,:64]; return (10+80*np.exp(-((x-20)**2+(y-20)**2)/40)+90*np.exp(-((x-43)**2+(y-42)**2)/55)).tolist()
def test_corrected_segmentation_finds_cells_and_is_honest():
 r=corrected_segmentation(image(),min_area_um2=8); assert r["cell_count"]>=2 and len(r["labels"])==64 and "no trained model claim" in r["model_status"]
def test_morphology_table_has_quantitative_per_cell_outputs():
 s=corrected_segmentation(image(),min_area_um2=8); r=morphology_table(image(),s); assert len(r)==s["cell_count"] and all(x["area_um2"]>0 and x["perimeter_um"]>0 for x in r)
def test_segmentation_changes_with_real_image():
 a=analyze_microscopy(image(),min_area_um2=8); z=np.asarray(image()); z+=60*np.exp(-((np.mgrid[:64,:64][1]-32)**2+(np.mgrid[:64,:64][0]-12)**2)/20); b=analyze_microscopy(z,min_area_um2=8); assert a["cells"]!=b["cells"]
def test_exactly_fifty_image_derived_diagnostics():
 r=analyze_microscopy(image(),min_area_um2=8); assert len(r["diagnostics"])==50 and len(set(r["diagnostics"]))==50
def test_actionable_screen_report():
 r=analyze_microscopy(image(),pixel_size_um=.5,min_area_um2=2); assert r["diagnostic_count"]==50 and r["culture_health"]["decision"] and r["recommended_actions"]
def test_legacy_apis_remain_available(): assert count_cells(image())["cell_count"]>=1 and analyze_image(image())["cells"]
def test_validation_errors_are_informative():
 with pytest.raises(ValueError,match="2-D"): validate_image([1,2,3])
 with pytest.raises(ValueError,match="contrast"): validate_image(np.ones((8,8)))
 with pytest.raises(ValueError,match="threshold_method"): corrected_segmentation(image(),threshold_method="ai")
