"""SynDroid mechanistic minimal-cell design and simulation."""
from .core import (simulate_minimal_cell,optimize_minimal_genome,stochastic_gene_expression,
 mechanistic_cell_program,evolutionary_stability,design_syndroid)
__all__=["simulate_minimal_cell","optimize_minimal_genome","stochastic_gene_expression",
 "mechanistic_cell_program","evolutionary_stability","design_syndroid"]

# Seed-checked entry point: replaces the raw core function at package level.
from .seed_guard import design_syndroid  # noqa: E402,F401

# Seed-checked entry point: replaces the raw core function at package level.
from .seed_checked import evolutionary_stability  # noqa: E402,F401

# Seed-checked entry point: replaces the raw core function at package level.
from .seed_guard import mechanistic_cell_program  # noqa: E402,F401

# Seed-checked entry point: replaces the raw core function at package level.
from .seed_checked import stochastic_gene_expression  # noqa: E402,F401
