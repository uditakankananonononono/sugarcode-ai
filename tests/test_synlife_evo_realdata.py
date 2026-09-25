"""Module 124 synlife_evo: endpoint honesty in evolve(), parameter validation,
environment-schedule coverage, mutation-model capacity, and censored-event
diagnostics. Catalog anchors: evolutionary stability of engineered circuits
(PMID 37260076 overlapping-gene stabilization; PMID 36357387 integrase
differentiation circuits for burdensome functions)."""
import json
import random
import pytest
from sugarcode.modules.synlife_evo import (evolve, simulate_evolution_experiment,
    optimize_stability, simulate_competition)


def test_evolve_reports_true_endpoint_not_last_sample():
    r = evolve(generations=150, sample_every=100, burden_cost=0.25,
               mutation_rate=5e-5, seed=1)
    assert r["history"][-1]["gen"] == 150  # was: gen 100 reported as the final state
    # measured: knockout fraction 0.084 at gen 100 -> 0.864 at gen 150
    assert r["pathway_silenced"] is True  # was: False, with "genetically stable" advice
    assert r["silencing_onset_gen"] == 150


def test_evolve_short_run_no_index_error():
    r = evolve(generations=50, sample_every=100)  # was: IndexError on history[-1]
    assert [h["gen"] for h in r["history"]] == [50]


def test_evolve_informative_validation():
    with pytest.raises(ValueError, match="pop_size"):
        evolve(pop_size=0)  # was: ZeroDivisionError
    with pytest.raises(ValueError, match="non-negative"):
        evolve(mutation_rate=-1.0)  # was: mutation silently disabled
    with pytest.raises(ValueError, match="single-mutation"):
        evolve(mutation_rate=5.0)  # was: gate saturated, model silently invalid
    with pytest.raises(ValueError, match="generations"):
        evolve(generations=0)  # was: IndexError
    with pytest.raises(ValueError, match="unique"):
        evolve(["A", "A"])


def test_selection_clamp_survives_float_undershoot(monkeypatch):
    # cumulative fitness sum can undershoot 1.0; a draw above it must not crash
    # or silently reuse the previously selected parent
    monkeypatch.setattr(random.Random, "random", lambda self: 0.9999999999999999)
    r = evolve(generations=5, pop_size=10, sample_every=1)
    assert r["history"][-1]["gen"] == 5


def test_environment_schedule_must_cover_every_generation():
    partial = [{"start": 0, "end": 50, "name": "growth", "product_selection": 0.0}]
    with pytest.raises(ValueError, match="uncovered"):
        simulate_evolution_experiment(["A", "B"], generations=200, population=500,
                                      sample_every=50, environment_schedule=partial)
    gapped = [{"start": 0, "end": 50, "name": "growth"},
              {"start": 100, "end": 201, "name": "production"}]
    with pytest.raises(ValueError, match="uncovered"):
        simulate_competition(["A"], generations=200, population=500,
                             sample_every=50, environment_schedule=gapped)
    # was: uncovered generations silently inherited the last-listed environment
    # and were mislabeled with its name in the trajectory


def test_mutation_capacity_bound_is_explicit():
    with pytest.raises(ValueError, match="model capacity"):
        simulate_evolution_experiment(["g%d" % i for i in range(30)], generations=50,
                                      population=200, sample_every=10, mutation_rate=0.01)
    # was: per-class mutation flux 0.30 silently capped at 0.20


def test_censored_event_diagnostics_are_none_not_final_generation():
    r = simulate_evolution_experiment(["A", "B"], generations=100, population=500,
                                      sample_every=10)
    d = r["diagnostics"]
    assert d["failure_observed"] is False
    assert d["failure_onset_generation"] is None  # was: 100, contradicting top-level None
    assert d["intact_half_life_generation"] is None  # intact never < 0.5 (0.994 measured)
    assert d["knockout_detection_generation"] is None
    assert d["failure_onset_generation"] == r["failure_onset_generation"]


def test_observed_failure_still_reports_real_generation():
    r = simulate_evolution_experiment(["A"], generations=200, population=500,
                                      sample_every=10, burden=0.3,
                                      yield_selection=0.0, mutation_rate=0.005)
    d = r["diagnostics"]
    assert d["failure_observed"] is True and isinstance(d["failure_onset_generation"], int)
    assert d["knockout_detection_generation"] is not None


def test_results_json_serializable():
    json.dumps(evolve(generations=20, sample_every=7))
    json.dumps(simulate_evolution_experiment(["A"], generations=50, population=200, sample_every=10))
    json.dumps(simulate_competition(["A"], generations=50, population=200, sample_every=10))
    json.dumps(optimize_stability(["A"], generations=50, population=200))


def test_pubmed_evolutionary_stability_anchors_live():
    from sugarcode.bio.entrez import esummary
    try:
        s = esummary("pubmed", ["37260076", "36357387"])
    except Exception as e:
        pytest.skip("entrez unavailable: %s" % e)
    assert "genetic circuit stability" in s["37260076"]["title"].lower()
    assert "evolutionary stability" in s["36357387"]["title"].lower()
