"""Unit 43 v12c: tests-only pins for the tiny-glucose floor and the glucose clamp in simulate_growth (PARTIAL).

 - L181 floor max(biomass, 1e-9): tiny glucose so the bound is below the cap. glucose0=1e-10, dt=0.25, objective -50
   drives biomass negative after step 1, so step 2 bound = 1e-10 / 1e-9 / 0.25 = 0.4 (a 2e-9 floor gives 0.2).
 - L186 glucose clamp max(0.0, ...): glucose0=0.5, uptake 100, biomass 0.01, dt 100 -> 0.5 - 100*0.01*0.01*100 = -0.5 -> 0.0.
"""
import types

from sugarcode.modules.virtual_cell import core


def _fba(log, objective, fluxes):
    def f(model, objective_=None, bounds_override=None):
        log.append(bounds_override)
        return {"status": "optimal", "objective": objective, "fluxes": fluxes}
    return f


def test_growth_floor_tiny_glucose(monkeypatch):
    log = []
    monkeypatch.setattr(core, "fba", _fba(log, -50.0, {"GLC_UP": 0.0}))
    core.simulate_growth(types.SimpleNamespace(objective="B"), hours=0.3, dt=0.25, glucose0=1e-10)
    assert len(log) == 2
    assert log[0] == {"GLC_UP": (0, 1e-10 / 0.01 / 0.25)}
    assert log[1] == {"GLC_UP": (0, 1e-10 / 1e-9 / 0.25)}
    assert abs(log[1]["GLC_UP"][1] - 0.4) < 1e-12


def test_growth_glucose_clamps_at_zero(monkeypatch):
    log = []
    monkeypatch.setattr(core, "fba", _fba(log, 0.0, {"GLC_UP": 100.0}))
    out = core.simulate_growth(types.SimpleNamespace(objective="B"), hours=1.0, dt=100.0, glucose0=0.5)
    assert log == [{"GLC_UP": (0, 0.5 / 0.01 / 100.0)}]
    assert out["trajectory"][0]["glucose"] == 0.0
    assert out["glucose_exhausted"] is True and len(out["trajectory"]) == 1
