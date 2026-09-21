from __future__ import annotations
import math

# Reference vehicle properties (literature-grounded defaults)
VEHICLES = {
    "LNP": {"cargo_kb": 6.0, "tissues": {"liver": 0.9, "spleen": 0.5, "lung": 0.4},
            "half_life_h": 12.0, "immunogenicity": 0.2, "repeat_dose": True},
    "AAV8": {"cargo_kb": 4.7, "tissues": {"liver": 0.85, "muscle": 0.6, "heart": 0.6},
             "half_life_h": 24 * 30.0, "immunogenicity": 0.5, "repeat_dose": False},
    "AAV9": {"cargo_kb": 4.7, "tissues": {"cns": 0.8, "heart": 0.7, "muscle": 0.65},
             "half_life_h": 24 * 30.0, "immunogenicity": 0.5, "repeat_dose": False},
    "AAV2": {"cargo_kb": 4.7, "tissues": {"retina": 0.9, "cns": 0.5},
             "half_life_h": 24 * 30.0, "immunogenicity": 0.4, "repeat_dose": False},
    "VLP-e": {"cargo_kb": 11.0, "tissues": {"liver": 0.6, "t_cell": 0.5, "eye": 0.4},
              "half_life_h": 24.0, "immunogenicity": 0.3, "repeat_dose": True},
    "PNP": {"cargo_kb": 20.0, "tissues": {"skin": 0.6, "tumor": 0.5, "lung": 0.5},
            "half_life_h": 48.0, "immunogenicity": 0.15, "repeat_dose": True},
}
PAYLOADS = {
    "SpCas9+gRNA": 5.5, "SaCas9+gRNA": 4.3, "base_editor+gRNA": 6.5,
    "prime_editor+pegRNA": 8.5, "Cas13+gRNA": 5.0, "gRNA_only": 0.2,
}


def recommend_vehicle(payload: str, tissue: str, repeat_dosing: bool = False) -> dict:
    """Rank delivery vehicles for a payload/tissue pair.

    Score = tropism * cargo_fit * (repeat-dose compatibility) - immunogenicity.
    """
    if payload not in PAYLOADS:
        raise KeyError(f"unknown payload {payload!r}; have {sorted(PAYLOADS)}")
    size = PAYLOADS[payload]
    ranked = []
    for name, v in VEHICLES.items():
        cargo_fit = 1.0 if size <= v["cargo_kb"] else max(0.0, 1 - (size - v["cargo_kb"]) / 5.0)
        tropism = v["tissues"].get(tissue, 0.1)
        dose_ok = 1.0 if (not repeat_dosing or v["repeat_dose"]) else 0.3
        score = (0.45 * tropism + 0.35 * cargo_fit + 0.2 * dose_ok) * (1 - 0.5 * v["immunogenicity"])
        ranked.append({"vehicle": name, "score": round(score, 4), "tropism": tropism,
                       "cargo_fit": round(cargo_fit, 3), "fits_cargo": size <= v["cargo_kb"],
                       "repeat_dose_ok": v["repeat_dose"],
                       "immunogenicity": v["immunogenicity"]})
    ranked.sort(key=lambda r: -r["score"])
    return {"payload": payload, "payload_kb": size, "tissue": tissue,
            "recommendation": ranked[0], "ranked": ranked}


def pk_model(vehicle: str, dose_ug: float = 100.0, hours: float = 96.0,
             dt: float = 1.0) -> dict:
    """One-compartment PK model: first-order elimination from plasma.

    C(t) = (D/Vd) * e^(-ke t); ke = ln2 / t_half. Returns concentration trace,
    Cmax, t_half and AUC (trapezoid).
    """
    if vehicle not in VEHICLES:
        raise KeyError(f"unknown vehicle {vehicle!r}")
    v = VEHICLES[vehicle]
    vd_l = 3.0  # plasma volume approximation (L, human-scaled per kg dose input)
    ke = math.log(2) / v["half_life_h"]
    c0 = dose_ug / vd_l
    ts, conc = [], []
    t = 0.0
    auc = 0.0
    prev = c0
    while t <= hours:
        c = c0 * math.exp(-ke * t)
        auc += (c + prev) / 2 * dt
        prev = c
        ts.append(round(t, 2))
        conc.append(round(c, 5))
        t += dt
    return {
        "vehicle": vehicle, "dose_ug": dose_ug,
        "half_life_h": v["half_life_h"], "elimination_ke": round(ke, 6),
        "cmax_ug_per_l": round(c0, 4),
        "auc_ug_h_per_l": round(auc, 3),
        "time_h": ts, "concentration_ug_per_l": conc,
    }


def delivery_blueprint(payload: str, tissue: str, dose_ug: float = 100.0) -> dict:
    """Full delivery blueprint: vehicle choice + PK trace + composition spec."""
    rec = recommend_vehicle(payload, tissue)
    veh = rec["recommendation"]["vehicle"]
    pk = pk_model(veh, dose_ug)
    return {
        **rec,
        "pk": pk,
        "composition": _composition(veh, payload, dose_ug),
        "dose_response": [
            {"dose_ug": d, "cmax": pk_model(veh, d, hours=4)["cmax_ug_per_l"]}
            for d in (25.0, 50.0, 100.0, 200.0, 400.0)
        ],
    }


def _composition(veh: str, payload: str, dose_ug: float) -> dict:
    if veh == "LNP":
        return {"ionizable_lipid": "SM-102-class, 50 mol%", "helper": "DSPC 10 mol%",
                "cholesterol": "38.5 mol%", "peg_lipid": "1.5 mol%",
                "n_p_ratio": 6.0, "payload": payload, "dose_ug": dose_ug}
    if veh.startswith("AAV"):
        return {"capsid": veh, "genome": f"ssDNA {payload} expression cassette",
                "vp_particles": "1e13 vg/kg typical", "dose_ug": dose_ug}
    return {"particle": veh, "payload": payload, "dose_ug": dose_ug}
