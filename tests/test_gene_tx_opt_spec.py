import pytest
from sugarcode.modules.gene_tx_opt import *

def test_vector_promoter_ranking_is_tissue_route_cargo_and_immunity_aware():
 a=rank_vector_promoter_pairs("liver",4,"iv",nab_titer=0); b=rank_vector_promoter_pairs("liver",4,"iv",nab_titer=.8)
 assert a["selected"]["vector"]=="AAV8" and a["selected"]["promoter"] in {"TBG","LP1"}
 assert b["selected"]["predicted_expression"]<a["selected"]["predicted_expression"]

def test_delivery_simulation_solves_real_compartment_odes():
 r=simulate_delivery("cns","AAV9","intrathecal",1e12,hours=48,sample_hours=4)
 assert r["solver"]["success"] and r["peak_expression"]>0 and r["trajectory"][-1]["tissue_vg_per_kg"]>0

def test_routes_change_delivery_to_target_tissue():
 a=simulate_delivery("cns","AAV9","intrathecal",1e12,hours=24); b=simulate_delivery("cns","AAV9","iv",1e12,hours=24)
 assert a["peak_expression"]>b["peak_expression"]

def test_exactly_fifty_three_case_derived_diagnostics():
 r=design_gene_therapy_program("liver",4,"iv",dose_vg_per_kg=1e12,hours=48)
 assert len(r["diagnostics"])==53 and len(set(r["diagnostics"]))==53
 assert r["diagnostics"]["selected_cargo_margin_kb"]>0

def test_end_to_end_output_is_actionable_for_lab():
 r=design_gene_therapy_program("retina",3,"subretinal",dose_vg_per_kg=1e11,hours=24)
 assert r["diagnostic_count"]==53 and r["selected_program"]["vector"]=="AAV2"
 assert r["visualization"]["coordinates"] and len(r["lab_plan"])>=4
 assert "mechanistic hermetic" in r["model_status"]

def test_legacy_optimizer_remains_available():
 assert optimize_gene_therapy("heart",3)["selected"] is not None

def test_validation_errors_are_informative():
 with pytest.raises(ValueError,match="unsupported tissue"): validate_program("kidney",3,"iv",1e12)
 with pytest.raises(ValueError,match="transgene_kb"): validate_program("liver",0,"iv",1e12)
 with pytest.raises(ValueError,match="nab_titer"): rank_vector_promoter_pairs("liver",3,nab_titer=2)
