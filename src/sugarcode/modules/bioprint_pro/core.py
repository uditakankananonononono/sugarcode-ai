from __future__ import annotations
import math

INKS = {
    "alginate_2pct": {"eta0": 150.0, "eta_inf": 0.5, "lambda_s": 2.0, "n": 0.55,
                      "crosslink": "ionic (CaCl2)", "k_crosslink_s": 0.8, "E0_kPa": 5.0},
    "gelma_10pct": {"eta0": 45.0, "eta_inf": 0.2, "lambda_s": 1.0, "n": 0.65,
                    "crosslink": "photo (UV, LAP)", "k_crosslink_s": 1.5, "E0_kPa": 12.0},
    "collagen_1pct": {"eta0": 8.0, "eta_inf": 0.05, "lambda_s": 0.5, "n": 0.8,
                      "crosslink": "thermal (37C)", "k_crosslink_s": 0.05, "E0_kPa": 1.5},
}


def _viscosity(ink: dict, shear: float) -> float:
    """Cross model: eta = eta_inf + (eta0 - eta_inf) / (1 + (lambda*shear)^n)."""
    return ink["eta_inf"] + (ink["eta0"] - ink["eta_inf"]) / (1 + (ink["lambda_s"] * shear) ** ink["n"])


def calibrate(ink_name: str, nozzle_mm: float = 0.4, target_speed_mm_s: float = 8.0) -> dict:
    """Printability window + crosslinking schedule + structural prediction."""
    if ink_name not in INKS:
        raise KeyError(f"unknown ink; have {sorted(INKS)}")
    ink = INKS[ink_name]
    radius = nozzle_mm / 2
    # pressure requirement from Hagen-Poiseuille with Cross viscosity at wall shear
    window = []
    for speed in (2, 4, 8, 12, 20):
        q = math.pi * radius ** 2 * speed  # mm^3/s
        # SI: Hagen-Poiseuille through an L=10mm needle
        q_m3, r_m, L_m = q * 1e-9, radius * 1e-3, 0.010
        shear = 4 * q_m3 / (math.pi * r_m ** 3)
        eta = _viscosity(ink, shear)
        p_kPa = round(8 * eta * L_m * q_m3 / (math.pi * r_m ** 4) / 1000, 1)
        printable = 5 <= p_kPa <= 250 and 0.05 <= eta <= 100
        window.append({"speed_mm_s": speed, "wall_shear_s-1": round(shear, 1),
                       "viscosity_Pa_s": round(eta, 3), "pressure_kPa": p_kPa,
                       "printable": printable})
    best = min((w for w in window if w["printable"]),
               key=lambda w: abs(w["speed_mm_s"] - target_speed_mm_s), default=None)
    # crosslinking: first-order conversion x(t) = 1 - exp(-kt)
    k = ink["k_crosslink_s"]
    t95 = round(-math.log(0.05) / k, 2) if k > 0 else None
    # modulus grows with conversion: E(t) = E0 * (1 + 9*x)
    x_print = 1 - math.exp(-k * 10)  # 10 s post-deposition
    E_kPa = round(ink["E0_kPa"] * (1 + 9 * x_print), 1)
    fidelity = round(min(1.0, x_print * 1.2) * (1.0 if best else 0.5), 2)
    return {
        "ink": ink_name, "nozzle_mm": nozzle_mm,
        "crosslink_chemistry": ink["crosslink"],
        "printability_window": window,
        "recommended": best,
        "crosslinking": {"rate_s-1": k, "t95_s": t95,
                         "conversion_at_10s": round(x_print, 3)},
        "structural_integrity": {"modulus_kPa_at_10s": E_kPa,
                                 "predicted_shape_fidelity": fidelity,
                                 "layer_adhesion": "good" if x_print < 0.95 else "risk of over-curing"},
        "visualization": {"type": "ink_rheology_curve",
                          "viscosity_vs_shear": [(round(s, 1), round(_viscosity(ink, s), 3))
                                                for s in (0.1, 1, 10, 100, 1000)]},
    }
