"""Verified named functions; other entries excluded by scope.

Explicit-import seed gates only; legacy entry points remain unchanged.
"""
from . import core
from ...seed_check import check_seed

def train(n_in=6, n_hidden=12, epochs=300, lr=0.5, stdp_mod=0.0, seed=42):
    seed=check_seed(seed)
    return core.train(n_in,n_hidden,epochs,lr,stdp_mod,seed)

def lesion_study(model, n_in=None, seed=42, X=None, y=None):
    seed=check_seed(seed)
    return core.lesion_study(model,n_in,seed,X,y)

def rsa(model, n_in=None, n_stimuli=40, seed=7, X=None):
    seed=check_seed(seed)
    return core.rsa(model,n_in,n_stimuli,seed,X)

def predictive_coding_hierarchy(X, latent_dims=(4, 2), steps=30, infer_lr=0.1, learn_lr=0.01, epochs=60, seed=0):
    seed=check_seed(seed)
    return core.predictive_coding_hierarchy(X,latent_dims,steps,infer_lr,learn_lr,epochs,seed)

def pipeline_report(seed=42):
    seed=check_seed(seed)
    return core.pipeline_report(seed)

def neuro_diagnostics(seed=42):
    seed=check_seed(seed)
    return core.neuro_diagnostics(seed)


class MLP(core.MLP):
    """Seed-checked numerical network constructor; no sequence generation."""
    def __init__(self,n_in,n_hidden,n_out,seed=42):
        seed=check_seed(seed)
        super().__init__(n_in,n_hidden,n_out,seed=seed)
