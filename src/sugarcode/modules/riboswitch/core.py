from __future__ import annotations
import random

APTAMERS = {
    "theophylline": ("AUACUACCCUGGUGAGGAUUGAGGG", 0.32),  # seq, Kd uM
    "tetracycline": ("GGGAAUUCGGUACCGGUUCAGUAGCUG", 0.77),
    "adenine": ("UAUAAUCGCGUGGAUAUGGCACGCAAGUUUCUACC", 0.30),
    "SAM": ("UCUAUCAAGAGCUGGUGGAGGGACUGGCCCGCGAAACUC", 0.02),
}


def _fold_hairpin(stem5: str, loop: str, stem3: str) -> float:
    """Crude stability: GC-weighted stem pairing minus loop penalty."""
    gc = sum(1 for a, b in zip(stem5, stem3) if
             (a + b) in ("GC", "CG", "AU", "UA", "GU", "UG"))
    return round(gc * 1.8 - 0.5 * len(loop), 2)


def design_riboswitch(ligand: str, mode: str = "on", spacer: str = "AAGGAG",
                      seed: int = 42) -> dict:
    """Design a synthetic riboswitch: known aptamer + tuned expression platform.

    mode 'on': ligand binding exposes RBS (anti-sequester stem breaks).
    mode 'off': ligand binding stabilizes RBS-sequestering stem.
    Returns predicted dynamic range from stem energetics.
    """
    if ligand not in APTAMERS:
        raise KeyError(f"no aptamer for {ligand}; have {sorted(APTAMERS)}")
    if mode not in ("on", "off"):
        raise ValueError("mode must be 'on' or 'off'")
    rng = random.Random(seed)
    aptamer, kd = APTAMERS[ligand]
    apt_3p = aptamer[-6:]  # 3' end of aptamer participates in switching stem
    comp = {"A": "U", "U": "A", "G": "C", "C": "G"}
    antisense = "".join(comp[b] for b in apt_3p)
    if mode == "on":
        # sequester RBS in a stem broken by aptamer-ligand complex
        stem5 = antisense[:4] + spacer[-4:]
        stem3 = apt_3p[:4] + "".join(comp[b] for b in spacer[-4:])
        loop = "AAAU"
    else:
        stem5 = antisense
        stem3 = apt_3p
        loop = "UUUU"
    dG = _fold_hairpin(stem5, loop, stem3)
    kd_factor = max(0.5, 2.0 - kd)
    dyn_range = round((8.0 - 0.5 * dG) * kd_factor, 1) if mode == "on" \
        else round((5.0 + 0.4 * dG) * kd_factor, 1)
    dyn_range = max(1.2, min(50.0, dyn_range))
    seq = aptamer + loop.join(["", ""])[0:0] + stem5 + loop + stem3 + spacer
    return {
        "ligand": ligand, "mode": mode, "aptamer_Kd_uM": kd,
        "sequence": aptamer + stem5 + loop + stem3 + spacer,
        "components": {"aptamer": aptamer, "switching_stem5": stem5,
                       "loop": loop, "switching_stem3": stem3, "rbs_spacer": spacer},
        "stem_stability": dG,
        "predicted_dynamic_range_fold": dyn_range,
        "leakiness": round(1.0 / dyn_range, 3),
        "validation": ["in vitro transcription + ligand titration (Kd check)",
                       "cell-free TX-TL dose-response (dynamic range)",
                       "in vivo reporter curve in E. coli"],
    }
