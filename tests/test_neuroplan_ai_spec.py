import numpy as np
import pytest
from sugarcode.modules.neuroplan_ai import *

def tumor(): return {"center":[32,32,30],"radius_mm":6,"type":"glioma"}

def test_real_mri_segmentation_extracts_largest_3d_component():
 x=np.zeros((20,20,20)); x[7:13,7:13,7:13]=10; x[1,1,1]=20
 r=segment_mri(x,threshold=5)
 assert r["tumor_voxels"]>100 and r["connected_components"]>=1 and len(r["mask"])==20
 assert "mechanistic hermetic" in r["model_status"]

def test_tractography_clearance_and_intersection_are_computed():
 r=analyze_tractography([[[0,0,0],[10,10,10]],[[30,32,30],[35,32,30]]],[32,32,30],3)
 assert r["streamline_count"]==2 and r["intersecting_count"]==1 and r["at_risk_count"]>=1

def test_astar_is_real_path_solver():
 r=plan_path_astar(tumor(),entry=[32,32,50],image_size=(64,64,64),max_expand=200000)
 assert r["method"].startswith("A*") and r["path"][0]==[32,32,50] and r["path"][-1]==[32,32,30]
 assert r["nodes_expanded"]>0

def test_neurotwin_reports_function_specific_risks_and_actions():
 p=plan_surgery(tumor(),(64,64,64)); r=simulate_neurotwin(tumor(),p["recommended_corridor"],resection_fraction=.8)
 assert len(r["functional_risks"])==len(ELOQUENT_REGIONS) and r["residual_tumor_volume_mm3"]>0
 assert r["recommended_actions"] and "mechanistic hermetic" in r["model_status"]

def test_exactly_fifty_two_meaningful_diagnostics():
 p=plan_surgery(tumor(),(64,64,64)); f=enhancement_features(p)
 assert len(f)==52 and len(set(f))==52 and f["tumor_volume_mm3"]>0

def test_end_to_end_is_actionable_and_complete():
 r=analyze_neurosurgical_case(tumor(),image_size=(64,64,64),resection_fraction=.9)
 assert r["diagnostic_count"]==52 and r["review_packet"]["required_reviews"]
 assert r["diagnostics"]["requested_resection_fraction"]==.9
 assert {"segmentation","tractography","recommended_corridor","neurotwin_detailed"}<=set(r)

def test_invalid_inputs_raise_informative_errors():
 with pytest.raises(ValueError,match="center"): analyze_neurosurgical_case({"radius_mm":2})
 with pytest.raises(ValueError,match="positive"): analyze_neurosurgical_case({"center":[1,1,1],"radius_mm":0})
 with pytest.raises(ValueError,match="3-D"): segment_mri(np.zeros((4,4)))
