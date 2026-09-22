import numpy as np
from sugarcode.modules.neohunter import *
REF="MKTIIALSYIFCLVFADYKDDDDKAAAAAAAAAALQLRLFGKGGGGGGGGGGGG"

def variants(): return [{"id":"v1","type":"snv","position":35,"alt":"Y","expression":2,"clonal_fraction":.9}]
def test_variant_translation_supports_snv_indel_fusion():
 ref={"a":REF,"b":REF[::-1]}; r=translate_variants(ref,[{"type":"snv","transcript":"a","position":5,"alt":"W"},{"type":"insertion","transcript":"a","position":6,"alt":"YY"},{"type":"fusion","left_transcript":"a","left_position":20,"right_transcript":"b","right_position":20}]); assert {x["type"] for x in r}=={"snv","insertion","fusion"}
def test_processing_components_are_bounded():
 r=proteasomal_processing("YLQLRLFGK"); assert all(0<=r[k]<=1 for k in ("proteasomal_cleavage","TAP_transport","ER_trimming","presentation_probability"))
def test_structural_binding_is_honestly_untrained():
 r=structural_mhc_binding("YLQLRLFGK","A*02:01"); assert r["predicted_ic50_nM"]>0 and "no trained" in r["method"]
def test_escape_is_seeded_and_normalized():
 a=simulate_immune_escape([{"immunogenicity":.5}],seed=2); b=simulate_immune_escape([{"immunogenicity":.5}],seed=2); assert a==b and np.isclose(sum(a["final"].values()),1)
def test_pipeline_has_50_meaningful_diagnostics_and_panel_limit():
 r=neoantigen_pipeline(REF,variants(),["A*02:01","B*07:02"],max_peptides=4); assert len(r["diagnostics"])>=50 and len(r["vaccine"]["panel"])<=4; assert {"processing_bottleneck","escape_risk","panel_clone_coverage","requires_normal_tissue_validation"}<=set(r["diagnostics"]); assert "no trained deep model" in r["model_status"]
def test_panel_optimizer_uses_milp():
 c=[{"peptide":"AAAAAAAAA","hla":"A*02:01","variant_id":"v1","immunogenicity":.4,"clonal_fraction":1,"escape_risk":.1}]; r=optimize_vaccine_panel(c,1); assert "mixed-integer" in r["solver"] and len(r["panel"])==1
