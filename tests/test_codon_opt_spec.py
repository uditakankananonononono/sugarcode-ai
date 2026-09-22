import numpy as np
import pytest
from sugarcode.modules.codon_opt import *
def test_product_design_is_actionable_and_synthesis_ready():
 r=design_expression_construct("MKTLLV",tasep_steps=200); assert r["optimized_dna"].startswith("ATG") and r["artifacts"]["fasta"].startswith(">") and "<sbml" in r["artifacts"]["sbml"]
def test_context_attention_normalized_and_untrained():
 r=sequence_attention("ATG"+"GCT"*5); a=np.array(r["attention"]); assert np.allclose(a.sum(1),1) and "untrained" in r["method"]
def test_folding_and_evolution_are_seeded():
 f=folding_accessibility("ATG"+"GCT"*8); a=evolutionary_robustness("ATG"+"GCT"*8,seed=2); b=evolutionary_robustness("ATG"+"GCT"*8,seed=2); assert 0<=f["initiation_accessibility"]<=1 and a==b
def test_50_computed_diagnostics_and_separate_honesty():
 r=design_expression_construct("MKTLLV",tasep_steps=200); assert len(r["diagnostics"])>=50 and "model_status" not in r["diagnostics"] and "untrained" in r["model_status"]
def test_informative_validation():
 with pytest.raises(ValueError,match="unsupported residues"): design_expression_construct("MX")
 with pytest.raises(ValueError,match="GC bounds"): design_expression_construct("MK",gc_min=.8,gc_max=.2)
 with pytest.raises(ValueError,match="copies"): design_expression_construct("MK",copies=0)
def test_scientist_next_steps_and_quality_flags_exist():
 r=design_expression_construct("M"+"K"*10,tasep_steps=200); assert len(r["recommended_next_steps"])>=3 and isinstance(r["quality_flags"],list)
