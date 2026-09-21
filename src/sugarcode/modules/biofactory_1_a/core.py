from __future__ import annotations

WORKFLOWS = {
    "golden_gate": {
        "steps": [
            {"op": "dispense", "reagent": "DNA parts (equimolar 40 fmol)", "plate": "PCR-96"},
            {"op": "dispense", "reagent": "BsaI-HFv2 1 uL", "plate": "PCR-96"},
            {"op": "dispense", "reagent": "T4 ligase + buffer", "plate": "PCR-96"},
            {"op": "thermocycle", "program": "30x(37C 5min, 16C 5min), 50C 10min, 80C 10min"},
            {"op": "transform", "cells": "DH5-alpha competent", "method": "heat shock 42C 45s"},
            {"op": "plate", "media": "LB + selection", "incubate_h": 16},
            {"op": "pick_colonies", "n": 8, "into": "deepwell-96 + media"},
            {"op": "screen", "method": "colony PCR + gel"},
        ],
        "equipment": ["liquid handler", "thermocycler", "colony picker", "plate reader"],
    },
    "gibson": {
        "steps": [
            {"op": "dispense", "reagent": "PCR fragments (0.03 pmol each)", "plate": "PCR-96"},
            {"op": "dispense", "reagent": "Gibson mastermix 2x", "plate": "PCR-96"},
            {"op": "incubate", "temp_c": 50, "min": 60},
            {"op": "transform", "cells": "NEB-stable competent"},
            {"op": "plate", "media": "LB + selection"},
        ],
        "equipment": ["liquid handler", "incubator", "colony picker"],
    },
    "pcr_screen": {
        "steps": [
            {"op": "dispense", "reagent": "template + primers + polymerase mix"},
            {"op": "thermocycle", "program": "98C 30s; 30x(98C 10s, 60C 20s, 72C 30s/kb); 72C 5min"},
            {"op": "gel", "agarose_pct": 1.0},
        ],
        "equipment": ["liquid handler", "thermocycler", "gel rig"],
    },
}


def generate_protocol(workflow: str, n_constructs: int = 8,
                      optimization: bool = True) -> dict:
    """Generate a biofoundry-ready robotic protocol with optimization tips."""
    if workflow not in WORKFLOWS:
        raise KeyError(f"unknown workflow {workflow!r}; have {sorted(WORKFLOWS)}")
    wf = WORKFLOWS[workflow]
    plates = (n_constructs + 95) // 96
    est_min = sum(_step_minutes(s) for s in wf["steps"]) * plates
    return {
        "workflow": workflow,
        "n_constructs": n_constructs,
        "plates": plates,
        "steps": wf["steps"],
        "equipment_required": wf["equipment"],
        "estimated_runtime_min": est_min,
        "optimization_tips": _tips(workflow) if optimization else [],
        "screening": {"candidates": n_constructs * 8,
                      "recommended_controls": ["no-DNA negative", "known-good positive",
                                               "assembly-vector-only"]},
    }


def _step_minutes(step: dict) -> int:
    return {"dispense": 8, "thermocycle": 120, "transform": 45, "plate": 5,
            "pick_colonies": 20, "screen": 60, "incubate": 60, "gel": 45}.get(step["op"], 15)


def _tips(workflow: str) -> list[str]:
    common = ["pre-wet tips for viscous enzyme mixes",
              "keep ligase on cold block; freeze-thaw kills activity",
              "run Bayesian optimization over annealing temp if success < 80%"]
    if workflow == "golden_gate":
        common.append("check parts for internal BsaI sites; domesticate silently first")
    return common
