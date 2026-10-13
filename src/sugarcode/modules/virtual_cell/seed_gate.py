"""Explicit-import seed gates only; legacy entry points remain unchanged."""
from . import core
from ...seed_check import check_seed

def simulate_expression(genes, interactions, *, inputs=None, params=None, hours=48.0, knockouts=(), overexpress=None, method='ode', seed=7, points=97):
    seed=check_seed(seed)
    return core.simulate_expression(genes,interactions,inputs=inputs,params=params,hours=hours,knockouts=knockouts,overexpress=overexpress,method=method,seed=seed,points=points)

def simulate_cell(model=None, grn=None, *, knockouts=(), overexpress=None, environment=None, inputs=None, params=None, hours=48.0, method='ode', seed=7, mu_per_flux=0.1):
    seed=check_seed(seed)
    return core.simulate_cell(model,grn,knockouts=knockouts,overexpress=overexpress,environment=environment,inputs=inputs,params=params,hours=hours,method=method,seed=seed,mu_per_flux=mu_per_flux)
