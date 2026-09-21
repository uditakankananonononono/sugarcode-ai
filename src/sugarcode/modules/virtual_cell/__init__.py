"""Virtual Cell: constraint-based metabolic simulation + GRN coupling."""
from .core import MetabolicModel, fba, gene_knockout, simulate_growth, demo_model
__all__ = ["MetabolicModel", "fba", "gene_knockout", "simulate_growth", "demo_model"]
