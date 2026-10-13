"""Reproducible, dependency-light QSAR benchmarking."""
from .chemistry import descriptors, morgan_fingerprint, parse_smiles
from .model import QSARModel, fit_qsar, predict, validate_qsar
from .chembl_client import ChEMBLQSARClient, ChEMBLUnavailable

__all__ = ["descriptors", "morgan_fingerprint", "parse_smiles", "QSARModel",
           "fit_qsar", "predict", "validate_qsar", "ChEMBLQSARClient",
           "ChEMBLUnavailable"]

# Seed-checked entry point: replaces the raw core function at package level.
from .seed_gate import validate_qsar  # noqa: E402,F401
