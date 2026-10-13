"""Explicit-import seed gates only; legacy entry points remain unchanged."""
from . import core
from ...seed_check import check_seed

def gillespie_expression(hours=24, transcription=1, translation=2, mrna_decay=0.5, protein_decay=0.1, seed=0):
    seed=check_seed(seed)
    return core.gillespie_expression(hours,transcription,translation,mrna_decay,protein_decay,seed)

def uncertainty_distribution(mean, model_cv=0.15, data_n=20, seed=0, samples=1000):
    seed=check_seed(seed)
    return core.uncertainty_distribution(mean,model_cv,data_n,seed,samples)
