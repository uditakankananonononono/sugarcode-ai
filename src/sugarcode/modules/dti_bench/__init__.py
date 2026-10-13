"""Target-conditioned drug-target interaction baselines and validation."""
from .core import DTIModel, protein_features, pair_features, fit_dti, predict_dti, validate_dti
from .chembl_pairs import ChEMBLPairClient, ChEMBLPairUnavailable
__all__=["DTIModel","protein_features","pair_features","fit_dti","predict_dti","validate_dti","ChEMBLPairClient","ChEMBLPairUnavailable"]

# Seed-checked entry point: replaces the raw core function at package level.
from .seed_checked import validate_dti  # noqa: E402,F401
