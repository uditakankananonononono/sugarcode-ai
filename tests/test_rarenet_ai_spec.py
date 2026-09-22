import pytest
from sugarcode.modules.rarenet_ai import *

def test_phenotype_normalization_reports_unknowns():
 r=normalize_phenotypes(["Cough","Failure to thrive","novel sign"])
 assert r["recognized"]==["chronic_cough","poor_growth"] and r["unrecognized"]==["novel_sign"]

def test_bayesian_ranking_is_explainable_and_genomic_evidence_increases_cf():
 a=explainable_rank(["salty skin","chronic cough"]); b=explainable_rank(["salty skin","chronic cough"],[{"gene":"CFTR","classification":"pathogenic","allele_frequency":0.00001}])
 assert b["top"]["disease"]=="cystic_fibrosis" and b["top"]["posterior"]>a["top"]["posterior"]
 assert any(x["evidence"]=="genomic_variant" for x in b["top"]["evidence_ledger"])

def test_negative_phenotype_is_evidence_against_candidate():
 a=explainable_rank(["bone pain","anemia"]); b=explainable_rank(["bone pain","anemia"],negative_symptoms=["hepatosplenomegaly"])
 ga=next(x for x in a["candidates"] if x["disease"]=="gaucher"); gb=next(x for x in b["candidates"] if x["disease"]=="gaucher")
 assert gb["posterior"]<ga["posterior"] and gb["contradicted_phenotypes"]==["hepatosplenomegaly"]

def test_workup_is_directly_actionable_for_scientist():
 r=diagnostic_workup(["gower sign","calf hypertrophy"],[{"gene":"DMD","classification":"likely_pathogenic"}])
 assert r["candidate_diseases"][0]["disease"]=="duchenne_md" and "DMD" in r["associated_genes"]
 assert len(r["confirmatory_plan"])>=3 and r["treatment_insights"]

def test_exactly_fifty_four_meaningful_diagnostics():
 f=enhancement_features(["salty skin","chronic cough","poor growth","recurrent lung infection"],[{"gene":"CFTR","classification":"pathogenic","allele_frequency":1e-6,"hgvs":"c.1A>G"}],{"disrupted_genes":["CFTR"]})
 assert len(f)==54 and len(set(f))==54 and f["review_priority_high"]

def test_legacy_diagnosis_remains_available():
 r=diagnose(["chronic cough","salty skin"],[{"gene":"CFTR"}])
 assert r["top"]["disease"]=="cystic_fibrosis" and r["treatments"]

def test_invalid_inputs_have_informative_errors():
 with pytest.raises(ValueError,match="non-empty list"): normalize_phenotypes([])
 with pytest.raises(ValueError,match="inheritance"): explainable_rank(["cough"],inheritance="mitochondrial")
