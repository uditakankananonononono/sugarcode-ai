"""Security Architecture - exact layered-defense replay of integer attack strengths.

Pure function over caller data. No network, no clock, no floats, no randomness. Input: layers, an
exact list of 1..8 ints 0..100 (the strength of each defensive layer, outermost first); attacks, an
exact list of 1..10 ints 0..1000 (the strength of each attack). The data keys are exactly attacks,
layers.

An attack meets the layers in order with its current power. A layer with strength s blocks the
attack when power <= s; otherwise the attack passes and its power drops by s. Attacks do not affect
each other. The result gives "attacks": a list in input order of {"power", "blocked_at" (layer index
or None when it passed every layer), "residual" (the power it had on reaching the blocking layer, or
what was left after the last layer)}; "blocked_counts" (per layer, how many attacks it blocked);
"breached" (attacks that passed every layer); "blocked" (attacks stopped).

Scope: PARTIAL for the Security Architecture line. A subtraction model on plain numbers. No threat
model, no real controls, no real attacker.

Not claimed: that this designs defenses, that strength numbers measure real security, that the model
resembles real attacks, or anything about the real world. Every claim flag in the result is False.
"""
NOT_CLAIMED = (
    "this designs defenses",
    "strength numbers measure real security",
    "the model resembles real attacks",
    "real-world outcome",
)
CLAIMS = {"designs_defenses": False, "measures_security": False, "real_attacks": False, "real_world": False}


class DefenseError(ValueError):
    pass


def _ints(data, k, lo, hi, name, top):
    v = data[k]
    if type(v) is not list or not lo <= len(v) <= hi:
        raise DefenseError("%s must be a list of 1 to %d %s" % (k, hi, name))
    for e in v:
        if type(e) is not int:
            raise DefenseError("%s entry must be an int" % k)
        if not 0 <= e <= top:
            raise DefenseError("%s entry must be 0 to %d" % (k, top))
    return list(v)


def _validate(data):
    if type(data) is not dict or set(data) != {"attacks", "layers"}:
        raise DefenseError("data keys must be exactly attacks, layers")
    layers = _ints(data, "layers", 1, 8, "layers", 100)
    attacks = _ints(data, "attacks", 1, 10, "attacks", 1000)
    return layers, attacks


def layered_defense(data):
    layers, attacks = _validate(data)
    counts = [0] * len(layers)
    rows = []
    breached = 0
    for a in attacks:
        power = a
        at = None
        for i, s in enumerate(layers):
            if power <= s:
                at = i
                counts[i] += 1
                break
            power -= s
        if at is None:
            breached += 1
        rows.append({"power": a, "blocked_at": at, "residual": power})
    return {
        "status": "completed",
        "attacks": rows,
        "blocked_counts": counts,
        "breached": breached,
        "blocked": len(attacks) - breached,
        "claims": dict(CLAIMS),
        "not_claimed": list(NOT_CLAIMED),
    }
