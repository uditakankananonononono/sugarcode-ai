import pytest
from sugarcode.modules.gene_tx_opt import (optimize_gene_therapy, rank_vector_promoter_pairs,
    simulate_delivery, design_gene_therapy_program, validate_program)

def test_canonical_tissue_vector_promoter_pairs():
    assert optimize_gene_therapy("liver",4.0)["selected"]["vector"]=="AAV8"
    assert optimize_gene_therapy("liver",4.0)["promoter_recommended"]=="TBG"
    assert optimize_gene_therapy("cns",4.0)["selected"]["vector"]=="AAV9"
    assert optimize_gene_therapy("retina",4.0)["selected"]["vector"]=="AAV2"

def test_oversized_transgene_selects_nothing():
    assert optimize_gene_therapy("liver",4.8)["selected"] is None
    assert rank_vector_promoter_pairs("liver",4.8)["selected"] is None

def test_score_and_expression_closed_form():
    rk=rank_vector_promoter_pairs("liver",4.0)
    r=rk["ranking"][0]
    exp=r["tropism"]*r["route_access"]*.95*1*(1-r["immune_risk"])
    assert r["predicted_expression"]==pytest.approx(exp,abs=1e-8)
    assert r["score"]==pytest.approx(.55*exp+.2*r["promoter_specificity"]+.15+.1*(1-r["immune_risk"]),abs=1e-8)

def test_immune_combined_risk():
    im=optimize_gene_therapy("liver",4.0)["immune_response"]
    assert im["combined_risk"]==pytest.approx(1-(1-.25)*(1-.3))

def test_nab_titer_lowers_scores():
    a=rank_vector_promoter_pairs("liver",4.0,nab_titer=0)["ranking"][0]["score"]
    b=rank_vector_promoter_pairs("liver",4.0,nab_titer=1)["ranking"][0]["score"]
    assert a>b

def test_delivery_mass_balance_declines():
    s=simulate_delivery("liver","AAV8","iv",hours=720)
    m=[x["plasma_vg_per_kg"]+x["tissue_vg_per_kg"]+x["intracellular_vg_per_kg"] for x in s["trajectory"]]
    assert all(m[i+1]<=m[i]+1e-3*m[i] for i in range(len(m)-1)) and m[-1]<m[0]

def test_diagnostics_exactly_53():
    assert design_gene_therapy_program("muscle",3.5)["diagnostic_count"]==53

def test_program_validation():
    with pytest.raises(ValueError): validate_program("brain",1,"iv",1e13)
    with pytest.raises(ValueError): validate_program("liver",25,"iv",1e13)
