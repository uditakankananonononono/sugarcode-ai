"""Unit 43 v12b: tests-only pins for further core.py survivors of the AST sweep (INTERIM, PARTIAL).

fba / regulatory_state are stubbed so each test isolates one line; all oracles are hand literals.
 - L231 default conditions {"standard": {}, "glucose_limited": {"GLC_UP": (0, 2)}}
 - L257/258 coupling: steady state < 0.5 disables (0.5 itself stays enabled), bound is (0.0, 0.0)
 - L181/184/186 simulate_growth: uptake bound g/max(biomass,1e-9)/dt, GLC_UP default 0.0, glucose update 0.01
 - L294/295 expression defaults
"""
import types

import pytest

from sugarcode.modules.virtual_cell import core


def _fake_fba(log, objective=1.0, fluxes=None):
    def f(model, objective_=None, bounds_override=None):
        log.append(bounds_override)
        return {"status": "optimal", "objective": objective, "fluxes": fluxes if fluxes is not None else {}}
    return f


def test_environment_default_conditions(monkeypatch):
    log = []
    monkeypatch.setattr(core, "fba", _fake_fba(log))
    out = core.environment_response(types.SimpleNamespace())
    assert list(out["conditions"]) == ["standard", "glucose_limited"]
    assert log[0] is None
    assert log[1] == {} and log[2] == {"GLC_UP": (0, 2)}
    assert log[2]["GLC_UP"][0] == 0 and log[2]["GLC_UP"][1] == 2


def test_coupling_threshold_and_bound(monkeypatch):
    ss = {"g0": 0.0, "g1": 0.49, "g2": 0.5, "g3": 0.51, "g4": 1.0}
    monkeypatch.setattr(core, "regulatory_state", lambda *a, **k: {"steady_state": ss})
    log = []
    monkeypatch.setattr(core, "fba", _fake_fba(log))
    m = types.SimpleNamespace(reactions=["r0", "r1", "r2", "r3", "r4"])
    rules = {"r0": "g0", "r1": "g1", "r2": "g2", "r3": "g3", "r4": "g4"}
    out = core.couple_grn_metabolism(m, list(ss), [], rules)
    assert out["disabled_reactions"] == ["r0", "r1"]
    assert log[0] == {"r0": (0.0, 0.0), "r1": (0.0, 0.0)}


def test_growth_uptake_bound_and_glucose_update(monkeypatch):
    log = []
    # biomass starts 0.01; bound = min(10, 1.25 / 0.01 / 25) = 5.0
    monkeypatch.setattr(core, "fba", _fake_fba(log, objective=0.0, fluxes={"GLC_UP": 2.0}))
    out = core.simulate_growth(types.SimpleNamespace(objective="BIO"), hours=0.0001, dt=25.0, glucose0=1.25)
    assert log[0] == {"GLC_UP": (0, 5.0)}
    # mu 0 -> biomass stays 0.01; glucose = 1.25 - 2.0*0.01*0.01*25 = 1.245
    assert out["trajectory"][0]["glucose"] == 1.245
    assert out["trajectory"][0]["biomass"] == 0.01


def test_growth_missing_uptake_defaults_to_zero(monkeypatch):
    log = []
    monkeypatch.setattr(core, "fba", _fake_fba(log, objective=0.0, fluxes={}))
    out = core.simulate_growth(types.SimpleNamespace(objective="BIO"), hours=0.0001, dt=100.0, glucose0=2.0)
    assert out["trajectory"][0]["glucose"] == 2.0


def test_growth_biomass_floor_avoids_divzero(monkeypatch):
    log = []
    # negative objective drives biomass below zero on step 2; floor 1e-9 keeps the bound at the cap 10
    monkeypatch.setattr(core, "fba", _fake_fba(log, objective=-50.0, fluxes={"GLC_UP": 0.0}))
    out = core.simulate_growth(types.SimpleNamespace(objective="BIO"), hours=0.3, dt=0.25, glucose0=10.0)
    assert len(log) == 2
    assert log[1] == {"GLC_UP": (0, 10)}


def test_expression_defaults_literals():
    assert core._EXPR_DEFAULTS == {"basal": 0.05, "vmax": 1.0, "K": 50.0, "n": 2.0,
                                   "mrna_decay": 0.5, "translation": 5.0, "protein_decay": 0.1}
    p = core._expr_params(["a"], None)["a"]
    assert p == core._EXPR_DEFAULTS and p is not core._EXPR_DEFAULTS
