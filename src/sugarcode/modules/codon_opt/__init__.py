"""Codon Opt laboratory-grade translational systems design."""
from .core import optimize,tasep_simulate,metabolic_load,sequence_attention,folding_accessibility,evolutionary_robustness,design_expression_construct
__all__=["optimize","tasep_simulate","metabolic_load","sequence_attention","folding_accessibility","evolutionary_robustness","design_expression_construct"]

# Seed-checked entry point: replaces the raw core function at package level.
from .seed_checked import evolutionary_robustness  # noqa: E402,F401
