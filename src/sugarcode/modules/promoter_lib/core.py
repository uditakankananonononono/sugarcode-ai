from __future__ import annotations
import random
from ...bio.sequence import clean_dna, gc_content

# E. coli sigma70 consensus elements
CONS_35 = "TTGACA"
CONS_10 = "TATAAT"
UP_ELEMENT = "AAAATATTT"  # A/T-rich UP element boosts rrn-type strength


def _mutate(base: str, rng: random.Random) -> str:
    return rng.choice([b for b in "ACGT" if b != base])


def score_promoter(seq: str) -> dict:
    """Score a promoter against sigma70 consensus.

    Strength 0..1 from -35/-10 identity, spacer length optimality (17 +/- 1),
    and UP-element A/T richness.
    """
    s = clean_dna(seq)
    best = None
    # scan for the -10 box, then check -35 upstream with spacer 15-19
    for i in range(len(s) - 6):
        box10 = s[i:i + 6]
        id10 = sum(a == b for a, b in zip(box10, CONS_10)) / 6
        for spacer in (15, 16, 17, 18, 19):
            j = i - spacer - 6
            if j < 0:
                continue
            box35 = s[j:j + 6]
            id35 = sum(a == b for a, b in zip(box35, CONS_35)) / 6
            spacer_score = 1.0 - abs(spacer - 17) / 4.0
            up = s[max(0, j - 9):j]
            up_score = (up.count("A") + up.count("T")) / max(1, len(up)) if up else 0.5
            total = 0.40 * id35 + 0.40 * id10 + 0.12 * spacer_score + 0.08 * up_score
            if best is None or total > best["strength"]:
                best = {"strength": round(total, 4), "minus10": box10,
                        "minus10_pos": i, "minus35": box35, "minus35_pos": j,
                        "spacer": spacer, "identity_35": round(id35, 3),
                        "identity_10": round(id10, 3), "up_element_at": round(up_score, 3)}
    if best is None:
        return {"strength": 0.0, "error": "sequence too short for promoter elements"}
    return best


def design_promoter(target_strength: float = 0.7, tfbs: list[str] | None = None,
                    seed: int = 42, length: int = 80) -> dict:
    """Generate a synthetic promoter tuned near target_strength (0..1).

    Starts from consensus and mutates away until within tolerance; optional
    TF binding sites are embedded upstream for compatibility.
    """
    rng = random.Random(seed)
    core = CONS_35 + "".join(rng.choice("ACGT") for _ in range(17)) + CONS_10
    flank5 = UP_ELEMENT + "".join(rng.choice("ACGT") for _ in range(6))
    flank3 = "".join(rng.choice("ACGT") for _ in range(12))
    seq = flank5 + core + flank3
    # degrade toward target by mutating consensus positions
    n_mut35 = round((1 - target_strength) * 6)
    n_mut10 = round((1 - target_strength) * 6)
    s = list(seq)
    base35 = len(flank5)
    base10 = base35 + 6 + 17
    for k in range(n_mut35):
        p = base35 + rng.randrange(6)
        s[p] = _mutate(s[p], rng)
    for k in range(n_mut10):
        p = base10 + rng.randrange(6)
        s[p] = _mutate(s[p], rng)
    seq = "".join(s)
    if tfbs:
        seq = "".join(tfbs) + seq
    sc = score_promoter(seq)
    return {
        "sequence": seq,
        "target_strength": target_strength,
        "achieved": sc,
        "gc": round(gc_content(seq), 3),
        "tfbs_embedded": tfbs or [],
        "host_prediction": _host_activity(sc["strength"]),
    }


def _host_activity(strength: float) -> dict:
    return {
        "e_coli": round(strength, 3),
        "b_subtilis": round(max(0.0, strength - 0.1), 3),
        "yeast_estimated": round(strength * 0.4, 3),
    }


def generate_library(n: int = 12, tfbs: list[str] | None = None,
                     strength_min: float = 0.2, strength_max: float = 0.95,
                     seed: int = 7) -> dict:
    """A promoter library spanning a predictable strength range."""
    rng = random.Random(seed)
    members = []
    for i in range(n):
        t = strength_min + (strength_max - strength_min) * (i / max(1, n - 1))
        d = design_promoter(target_strength=t, tfbs=tfbs, seed=rng.randrange(10**6))
        members.append({"id": f"pSC-{i + 1:03d}", "sequence": d["sequence"],
                        "predicted_strength": d["achieved"]["strength"]})
    members.sort(key=lambda m: m["predicted_strength"])
    heatmap = _motif_heatmap(members)
    return {"size": len(members), "members": members, "motif_heatmap": heatmap,
            "strength_range": [members[0]["predicted_strength"], members[-1]["predicted_strength"]]}


def _motif_heatmap(members: list[dict]) -> list[list[int]]:
    """Per-position A/C/G/T counts across aligned member cores (last 80 nt)."""
    rows = [[] for _ in range(4)]
    for b_i, base in enumerate("ACGT"):
        rows[b_i] = []
    cores = [m["sequence"][-80:] for m in members]
    for pos in range(80):
        col = [c[pos] for c in cores if len(c) > pos]
        for b_i, base in enumerate("ACGT"):
            rows[b_i].append(col.count(base))
    return rows
