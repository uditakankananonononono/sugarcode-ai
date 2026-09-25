import math
import pytest
from sugarcode.modules.crispr_cargo import pk_model, VEHICLES, PAYLOADS, compartment_pk

@pytest.mark.parametrize("v",["LNP","AAV8","PNP"])
def test_bug65_auc_matches_closed_form(v):
    ke=math.log(2)/VEHICLES[v]["half_life_h"]; an=100/3/ke*(1-math.exp(-ke*96))
    assert pk_model(v,dt=0.01)["auc_ug_h_per_l"]==pytest.approx(an,rel=1e-6)

def test_bug65_no_extra_interval_at_zero_hours():
    assert pk_model("LNP",hours=0)["auc_ug_h_per_l"]==0

def test_time_grid_is_exact():
    p=pk_model("LNP",hours=96,dt=0.1); assert len(p["time_h"])==961 and p["time_h"][-1]==96.0

def test_invalid_dt_rejected():
    with pytest.raises(ValueError): pk_model("LNP",dt=0)

def test_payload_sizes_cover_uniprot_cds():
    # UniProt Q99ZW2 SpCas9 1368 aa, J7RUA5 SaCas9 1053 aa: CDS = 3*aa+3 bp
    assert PAYLOADS["SpCas9+gRNA"]*1000 > 3*1368+3 and PAYLOADS["SaCas9+gRNA"]*1000 > 3*1053+3
    assert (3*1368+3)/1000 > VEHICLES["AAV8"]["cargo_kb"]-0.7  # SpCas9 alone leaves <0.6 kb in AAV

def test_compartment_mass_balance():
    assert compartment_pk("AAV9",tissue="cns")["mass_balance_error"]<1e-6
