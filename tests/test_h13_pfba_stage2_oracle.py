"""AUTHORED, NOT RUN. H13: virtual_cell.pfba stage 2 must use the UNROUNDED stage-1 optimum. Base 465d7684db06c866646feb0f3036912f26b8c5e4.
Written BEFORE the source edit. Fixtures tests/fixtures/h13_virtual_cell/{model-input.json,oracle.json}: byte-identical copies of the
peer-supplied frozen H13 artifact (COBRApy 0.30.0 textbook model, 72 x 95); sha256 pinned below and checked before use.
DELIBERATE INTERNALS TESTING: a pass-through spy on virtual_cell.core.linprog (the real scipy solver still runs). pfba makes exactly two
linprog calls: call 1 = stage 1 (inside fba), call 2 = stage 2. Primary checks use RAW values from the spy:
call 1 raw res.fun (rel 1e-9 vs the oracle stage-1 objective); call 2 actual lower bound on the objective reaction (must be raw optimum - 1e-9,
NOT derived from the 6 dp rounded public objective); call 2 raw res.fun (rel 1e-6 vs the oracle total absolute flux).
Public checks: method 'pFBA', status 'optimal', no fallback key, and each public objective, biomass flux and total_flux EXACTLY equal to round(the candidate's own raw internal value, 6), raw values from the spy, never a pre-rounded oracle constant. Rounding is presentation only. Degenerate flux vectors are not compared."""
import hashlib
import json
from pathlib import Path

import numpy as np
import pytest

import sugarcode.modules.virtual_cell.core as core
from sugarcode.modules.virtual_cell.core import MetabolicModel, pfba

FIX = Path(__file__).resolve().parent / "fixtures" / "h13_virtual_cell"
SHA = {"model-input.json": "3fbb889a94dfcedcb9fe63cdd9386394d6c8fae8b713e0577c2ceaa4fb488a9e",
       "oracle.json": "8a0da147c38c2fc3e0a57cb426d0f1dd2f1ed2bd9aace809b58322aa251d7306"}
OBJ = "Biomass_Ecoli_core"


@pytest.fixture(scope="module")
def oracle():
    for name, want in SHA.items():
        assert hashlib.sha256((FIX / name).read_bytes()).hexdigest() == want
    return json.loads((FIX / "oracle.json").read_text())


@pytest.fixture(scope="module")
def model():
    m = json.loads((FIX / "model-input.json").read_text())
    rxns = m["reactions"]
    lb = np.array([m["bounds"][r][0] for r in rxns], dtype=float)
    ub = np.array([m["bounds"][r][1] for r in rxns], dtype=float)
    assert np.array(m["S"]).shape == (72, 95) and m["objective_coefficients"] == {OBJ: 1.0}
    return MetabolicModel(m["metabolites"], rxns, np.array(m["S"], dtype=float), lb, ub, objective=OBJ)


def _run(model, overrides, monkeypatch):
    real = core.linprog
    calls = []

    def spy(*args, **kwargs):
        res = real(*args, **kwargs)
        fun = getattr(res, "fun", None)  # a failed solve may carry fun None: check BEFORE any float coercion
        x = getattr(res, "x", None)
        calls.append({"kwargs": kwargs, "fun": None if fun is None else float(fun), "success": bool(res.success),
                      "x": None if x is None else np.array(x, copy=True)})
        return res

    monkeypatch.setattr(core, "linprog", spy)
    out = pfba(model, bounds_override=overrides)
    return out, calls


CONDITIONS = [("WT", {}), ("zero_oxygen", {"EX_o2_e": (0.0, 0.0)})]


@pytest.mark.parametrize("name,overrides", CONDITIONS)
def test_primary_raw_stage_values_vs_frozen_oracle(name, overrides, model, oracle, monkeypatch):
    cond = next(c for c in oracle["conditions"] if c["condition"] == name)
    out, calls = _run(model, overrides, monkeypatch)
    assert len(calls) == 2  # stage 1 then stage 2 (the spy never raises, so a wrong call count fails HERE)
    assert calls[0]["success"] and calls[0]["fun"] is not None
    raw_opt = -calls[0]["fun"]
    assert abs(raw_opt - cond["unrounded_stage1_FBA_objective"]) <= 1e-9 * abs(cond["unrounded_stage1_FBA_objective"])
    # call 2: the ACTUAL lower bound passed on the objective reaction (read from the call kwargs, independent of solver success)
    j = model.rxn_index(OBJ)
    floor = calls[1]["kwargs"]["bounds"][j][0]
    assert floor <= raw_opt, "stage-2 floor must not exceed the true unrounded optimum"
    assert abs(floor - (raw_opt - 1e-9)) <= 1e-15
    assert floor != round(raw_opt, 6) - 1e-9  # not derived from the 6 dp public objective (old behaviour)
    # explicit solver-success assertion for stage 2, then its raw objective: total absolute flux
    assert calls[1]["success"], "stage-2 linprog must succeed (no pFBA fallback)"
    assert calls[1]["fun"] is not None
    assert abs(calls[1]["fun"] - cond["pfba_total_absolute_flux"]) <= 1e-6 * cond["pfba_total_absolute_flux"]


# PUBLIC predicate (peer-ruled, final): the public objective, biomass flux and total_flux each EQUAL round(the CANDIDATE'S OWN RAW
# internal value, 6) EXACTLY. The raw values come from the spy (stage-1 res.fun; stage-2 res.x split as pfba does), never from a
# pre-rounded oracle constant. Raw values are still tied to the frozen oracle by the primary test above (rel 1e-9 / rel 1e-6).
@pytest.mark.parametrize("name,overrides", CONDITIONS)
def test_public_result_equals_round_of_own_raw_internal_values(name, overrides, model, oracle, monkeypatch):
    out, calls = _run(model, overrides, monkeypatch)
    assert len(calls) == 2 and calls[0]["success"] and calls[1]["success"]
    assert calls[0]["fun"] is not None and calls[1]["x"] is not None
    n = len(model.reactions)
    j = model.rxn_index(OBJ)
    v = calls[1]["x"][:n] - calls[1]["x"][n:]  # same split as pfba: v = vp - vn
    raw_objective = float(-calls[0]["fun"])
    raw_biomass = float(v[j])
    raw_total = float(np.abs(v).sum())
    assert out["method"] == "pFBA" and out["status"] == "optimal" and "pfba_stage" not in out
    assert out["objective_reaction"] == OBJ
    assert out["objective"] == round(raw_objective, 6)      # EXACT
    assert out["fluxes"][OBJ] == round(raw_biomass, 6)      # EXACT
    assert out["total_flux"] == round(raw_total, 6)         # EXACT
