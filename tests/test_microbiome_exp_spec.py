import pytest
from sugarcode.modules.microbiome_exp import *
def table(): return {"a1":{"Faecalibacterium":40,"Bacteroides":20,"Escherichia":5},"a2":{"Faecalibacterium":35,"Bacteroides":25,"Escherichia":5},"b1":{"Faecalibacterium":5,"Bacteroides":20,"Escherichia":40},"b2":{"Faecalibacterium":4,"Bacteroides":25,"Escherichia":42}}
def meta(): return {"a1":{"state":"healthy"},"a2":{"state":"healthy"},"b1":{"state":"disease"},"b2":{"state":"disease"}}
def test_cohort_diversity_and_pcoa():
 r=cohort_analysis(table(),meta()); assert len(r["alpha_diversity"])==4 and len(r["bray_curtis"])==4 and len(r["ordination"]["coordinates"])==4 and "not diagnoses" in r["model_status"]
def test_permutation_differential_detects_direction():
 r=differential_abundance(table(),meta(),"state"); e=next(x for x in r["results"] if x["taxon"]=="Escherichia"); assert e["log2_fold_change"]>0 and r["permutations"]==500
 assert e["group_comparison"]=="disease" and e["group_reference"]=="healthy"
def test_exactly_fifty_case_derived_diagnostics():
 r=analyze_16s_cohort(table(),meta(),"state"); assert len(r["diagnostics"])==50 and len(set(r["diagnostics"]))==50
def test_actionable_end_to_end():
 r=analyze_16s_cohort(table(),meta(),"state"); assert r["diagnostic_count"]==50 and len(r["actions"])==4 and r["cohort"]["functional_potential"]
def test_legacy_single_sample_remains(): assert analyze_16s(table()["a1"])["alpha_diversity"]["richness"]==3
def test_validation_errors():
 with pytest.raises(ValueError,match="two samples"): validate_count_table({"one":{"A":1}})
 with pytest.raises(ValueError,match="two groups"): differential_abundance(table(),{},"state")
def test_disease_profiles_change_outputs():
 r=analyze_16s_cohort(table(),meta(),"state"); assert r["cohort"]["relative_abundance"]["a1"]!=r["cohort"]["relative_abundance"]["b1"]
