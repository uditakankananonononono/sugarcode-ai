"""Phage-Tx: exact cocktail optimization and host-phage coevolution."""
from .core import (PHAGE_LIBRARY, design_phage_therapy, enhancement_features,
 evolve_cocktail, match_phages, optimize_cocktail, simulate_coevolution,
 validate_phage_parameters)
__all__=["PHAGE_LIBRARY","design_phage_therapy","enhancement_features","evolve_cocktail","match_phages","optimize_cocktail","simulate_coevolution","validate_phage_parameters"]

# Seed-checked entry point: replaces the raw core function at package level.
from .seed_checked import evolve_cocktail  # noqa: E402,F401
