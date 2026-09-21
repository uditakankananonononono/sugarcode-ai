"""Neuro-Pipeline: train small numpy models with plasticity rules; lesion + RSA analysis."""
from .core import MLP, train, lesion_study, activation_trace, rsa
__all__ = ["MLP", "train", "lesion_study", "activation_trace", "rsa"]
