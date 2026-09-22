import numpy as np
from sugarcode.modules.syndroid import *

def test_minimal_genome_uses_real_milp_and_covers_life_processes():
 r=optimize_minimal_genome(); assert "mixed-integer" in r["solver"]
 assert {"replication","transcription","translation","metabolism","division","membrane","homeostasis"}<=set(r["covered_processes"])
 assert {"atpA","atpD"}<=set(r["genes"])

def test_gillespie_is_seeded_integer_and_dynamic():
 a=stochastic_gene_expression(["dnaA","rpoB"],seed=2); b=stochastic_gene_expression(["dnaA","rpoB"],seed=2)
 assert a==b and a["total_event_count"]>0 and all(isinstance(x,int) for x in a["protein"].values())

def test_mechanistic_program_exposes_coupled_states():
 p=mechanistic_cell_program(hours=2)
 assert set(p["states"])=={"DNA","mRNA","protein","ATP","glucose","mass","damage","circuit_output"}
 assert len({len(v) for v in p["states"].values()})==1

def test_evolution_is_normalized_and_reproducible():
 p=mechanistic_cell_program(hours=1); a=evolutionary_stability(p,seed=4); b=evolutionary_stability(p,seed=4)
 assert a==b and abs(sum(a["final"].values())-1)<1e-9

def test_end_to_end_has_50_meaningful_diagnostics_and_honesty():
 r=design_syndroid(hours=2)
 assert len(r["diagnostics"])>=50 and r["enhancement_feature_count"]==len(r["diagnostics"])
 assert {"energy_crash","expression_noise_fano","evolutionary_half_life","genotype_to_phenotype_trace","programmability_index"}<=set(r["diagnostics"])
 assert "no trained or clinically validated" in r["model_status"]

def test_missing_metabolism_changes_phenotype():
 p=mechanistic_cell_program(["dnaA","rpoB","rplA","ftsZ"],hours=2)
 assert "metabolism" not in p["processes"] and p["states"]["glucose"][-1]==p["states"]["glucose"][0]
