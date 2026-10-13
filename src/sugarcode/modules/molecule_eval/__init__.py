"""Auditable evaluation for generated molecular libraries."""
from .core import evaluate_library, compare_libraries, pareto_front
from .chembl_reference import ChEMBLReferenceClient, ChEMBLReferenceUnavailable
__all__=["evaluate_library","compare_libraries","pareto_front","ChEMBLReferenceClient","ChEMBLReferenceUnavailable"]

# Seed-checked entry point: replaces the raw core function at package level.
from .seed_gate import compare_libraries  # noqa: E402,F401

# Seed-checked entry point: replaces the raw core function at package level.
from .seed_gate import evaluate_library  # noqa: E402,F401
