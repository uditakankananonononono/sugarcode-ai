import math, os
import numpy as np
import pytest
from sugarcode.modules.cellpainter_4d import simulate_population_4d, segment_nuclei, state_from_nuclei_image

S={"area_um2":200,"circularity":.85,"aspect_ratio":1.2,"intensity":100,"cell_count":300}

def _at(r,h): return [f for f in r["frames"] if f["time_h"]==h][0]

def test_bug64_state_at_fixed_hour_is_independent_of_observation_window():
    got=[_at(simulate_population_4d("apoptosis",S,duration_h=D,heterogeneity=0),12) for D in (24,72,144)]
    assert len({round(g["area_um2"],6) for g in got})==1 and len({g["phase"] for g in got})==1

def test_closed_form_relaxation_and_death():
    r=simulate_population_4d("apoptosis",S,duration_h=24,heterogeneity=0); f=_at(r,12); tau=72/5
    assert f["area_um2"]==pytest.approx(200*.3+200*.7*math.exp(-12/tau),rel=1e-6)
    assert f["cell_count"]==round(300*math.exp(-.04*12))

def test_unobserved_events_are_flagged():
    ev=simulate_population_4d("emt",S,duration_h=24)["event_timeline"]
    assert [e["observed"] for e in ev]==[True,True,False,False,False] and ev[2]["nearest_frame"] is None

def _disks():
    y,x=np.mgrid[0:100,0:100]; img=np.zeros((100,100))
    for cy,cx in [(25,25),(25,70),(70,40)]: img[(x-cx)**2+(y-cy)**2<=36]=200
    return img

def test_watershed_does_not_leak_between_separate_nuclei():
    o=segment_nuclei(_disks())["objects"]
    assert len(o)==3 and all(x["area_px"]==121 for x in o)

def test_ellipse_aspect_ratio():
    y,x=np.mgrid[0:100,0:100]; img=np.zeros((100,100)); img[((x-50)/12)**2+((y-50)/6)**2<=1]=200
    o=segment_nuclei(img)["objects"]; assert len(o)==1 and o[0]["aspect_ratio"]==pytest.approx(2.0,abs=.1)

def test_state_requires_real_pixel_size():
    with pytest.raises(ValueError,match="pixel_size_um"): state_from_nuclei_image(_disks(),pixel_size_um=None)
    st=state_from_nuclei_image(_disks(),pixel_size_um=.5)["initial_state"]
    assert st["area_um2"]==pytest.approx(121*.25) and st["cell_count"]==3

D="/tmp/bbbc001"
@pytest.mark.skipif(not os.path.exists(D+"/counts.txt"),reason="BBBC001 not cached")
def test_bbbc001_counts_within_inter_human_spread():
    from PIL import Image
    rows=[l.split("\t") for l in open(D+"/counts.txt").read().strip().split("\n")[1:]]
    dev=[]
    for f,a,b in rows:
        n=segment_nuclei(np.array(Image.open(D+"/human_ht29_colon_cancer_1_images/"+f)))["cell_count"]; gt=(int(a)+int(b))/2
        dev.append(abs(n-gt)/gt)
    assert np.mean(dev)<.11
