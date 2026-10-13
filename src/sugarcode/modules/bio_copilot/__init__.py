"""Bio-Copilot: mutation-to-phenotype reasoning DAG + structured outputs."""
from .core import (answer, compile_research_artifact, design_crispr_guides, live_gene_context,
                   mutation_to_phenotype, propagate_uncertainty, select_editing_strategy,
                   to_fasta, to_pdb, update_from_experiment)
__all__ = ["answer", "compile_research_artifact", "design_crispr_guides", "live_gene_context",
           "mutation_to_phenotype", "propagate_uncertainty", "select_editing_strategy",
           "to_fasta", "to_pdb", "update_from_experiment"]

# Seed-checked entry point: replaces the raw core function at package level.
from .seed_checked import propagate_uncertainty  # noqa: E402,F401
