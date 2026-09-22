import json, pytest
from sugarcode.modules.bio_copilot import *

SEQ="ACGTACGTACGTACGTACGTAGGTTTTCCCCAAAAGGGGCGG"
def test_mutation_graph_links_variant_structure_pathway_and_phenotype():
 r=mutation_to_phenotype("TP53","R",175,"H"); assert [x["node"] for x in r["computation_graph"]]==["variant_annotation","structural_perturbation","pathway_effect","phenotype_inference"] and r["computation_graph"][0]["hotspot"] and r["suggested_experiments"]

def test_crispr_search_enumerates_scores_and_honest_limits():
 r=design_crispr_guides(SEQ); assert r["candidate_count"]>=2 and all(len(x["guide"])==20 for x in r["candidates"]) and r["candidates"]==sorted(r["candidates"],key=lambda x:(-x["composite_score"],x["start"])) and "not a genome-wide alignment" in r["limitations"][0]

def test_edit_strategy_uses_transition_distance_and_bystanders():
 assert select_editing_strategy("C","T",5)["method"]=="base editing" and select_editing_strategy("C","A",10)["method"]=="prime editing" and select_editing_strategy("C","A",40)["method"]=="HDR"

def test_uncertainty_is_seeded_and_returns_interval():
 a=propagate_uncertainty({"structure":(.8,.1),"pathway":(.7,.05)},seed=4); b=propagate_uncertainty({"structure":(.8,.1),"pathway":(.7,.05)},seed=4); assert a==b and a["ci95"][0]<a["mean"]<a["ci95"][1]

def test_experimental_feedback_updates_posterior():
 r=update_from_experiment(.5,10,9,10); assert r["posterior_mean"]>.5 and r["alpha"]==14 and r["beta"]==6

def test_structured_outputs_and_reproducible_artifact():
 assert to_fasta("x","A"*61).splitlines()==[">x","A"*60,"A"] and to_pdb("AC").endswith("END\n")
 a=compile_research_artifact("TP53 R175H",mutation_to_phenotype("TP53","R",175,"H")); assert json.loads(a["json"])["schema_version"]=="1.0" and len(a["payload"]["limitations"])==2

def test_answer_routes_grounded_tasks_without_claiming_missing_literature():
 assert answer("analyze a mutation")["route"]=="variant_pipeline" and "no grounded local hit" in answer("unknown biology")["answer"]

def test_validation_errors_are_informative():
 with pytest.raises(ValueError,match="A/C/G/T"): design_crispr_guides("BAD")
 with pytest.raises(ValueError,match="distinct DNA bases"): select_editing_strategy("A","A")
 with pytest.raises(ValueError,match="samples"): propagate_uncertainty({"x":(1,.1)},10)
