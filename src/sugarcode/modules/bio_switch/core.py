from __future__ import annotations

BINDING_DOMAINS = {
    "tetracycline": {"domain": "TetR", "kd_uM": 0.01, "mechanism": "repressor release"},
    "lactose": {"domain": "LacI", "kd_uM": 1.0, "mechanism": "repressor release (IPTG/allo)"},
    "arabinose": {"domain": "AraC", "kd_uM": 50.0, "mechanism": "activator induction"},
    "theophylline": {"domain": "riboswitch (theo aptamer)", "kd_uM": 0.3, "mechanism": "RNA conformational switch"},
    "fluoride": {"domain": "fluoride riboswitch (crcB)", "kd_uM": 60.0, "mechanism": "RNA conformational switch"},
    "copper": {"domain": "CueR", "kd_uM": 0.001, "mechanism": "metalloregulatory activation"},
    "arsenic": {"domain": "ArsR", "kd_uM": 5.0, "mechanism": "repressor release"},
    "mercury": {"domain": "MerR", "kd_uM": 0.1, "mechanism": "DNA-distortion activation"},
    "cadmium": {"domain": "CadR", "kd_uM": 2.0, "mechanism": "repressor release"},
    "benzene": {"domain": "XylR", "kd_uM": 10.0, "mechanism": "activator induction"},
}
REPORTERS = {"GFP": {"maturation_min": 14, "brightness": 1.0},
             "RFP": {"maturation_min": 45, "brightness": 0.7},
             "Luciferase": {"maturation_min": 2, "brightness": 3.0},
             "lacZ": {"maturation_min": 5, "brightness": 0.5}}


def design_biosensor(analyte: str, reporter: str = "GFP",
                     dynamic_range: tuple[float, float] | None = None) -> dict:
    """Couple a binding domain to a reporter; model dose-response curve."""
    key = analyte.lower()
    if key not in BINDING_DOMAINS:
        raise KeyError(f"no binding domain for {analyte!r}; have {sorted(BINDING_DOMAINS)}")
    bd = BINDING_DOMAINS[key]
    rep = REPORTERS[reporter]
    kd = bd["kd_uM"]
    lo, hi = dynamic_range or (kd / 10, kd * 10)
    import math
    concs = [lo * (hi / lo) ** (i / 20) for i in range(21)]
    response = [round(1 / (1 + (kd / c) ** 1.2), 3) for c in concs]  # Hill n=1.2
    lod = round(kd / 10, 4)
    return {
        "analyte": analyte,
        "binding_domain": bd,
        "reporter": reporter,
        "architecture": f"{bd['domain']} -> promoter control -> {reporter}",
        "dose_response": {"concentration_uM": [round(c, 5) for c in concs],
                          "response": response, "hill_n": 1.2},
        "limit_of_detection_uM": lod,
        "dynamic_range_uM": [round(lo, 4), round(hi, 4)],
        "sensitivity_class": ("ultra-high" if kd < 0.01 else "high" if kd < 1 else "moderate"),
        "response_time_min": rep["maturation_min"] + 20,
        "applications": _applications(key),
    }


def _applications(key: str) -> list[str]:
    if key in ("copper", "arsenic", "mercury", "cadmium"):
        return ["environmental heavy-metal monitoring", "field water testing"]
    if key in ("theophylline", "tetracycline"):
        return ["therapeutic drug monitoring", "fermentation process control"]
    return ["metabolite sensing", "biomarker detection"]
