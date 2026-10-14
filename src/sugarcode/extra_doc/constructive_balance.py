"""Row 724 Feedback Delivery : interleave strength and improvement notes under a one-to-one rule.

strengths and improvements are tuples of 0..20 notes; each note is a str of 1..60 characters. This module's own
rule: deliver a strength first, then alternate improvement, strength, improvement, strength while both remain;
once improvements run out, the remaining strengths follow; improvements with no strength left to pair with are
held back, not delivered. The result is the delivery sequence as (kind, position, note) triples with kind
"strength" or "improvement", the held improvement positions, and both counts. The ranges and the pairing rule
are this module's own choices. It is sequence bookkeeping only: it does not know whether any note is true,
kind, well written or worth saying."""

MAX_NOTES = 20
MAX_NOTE = 60
NOT_CLAIMED = ("whether any note is true", "whether any note is kind", "writing quality of any note",
               "whether the feedback should be given at all", "how anyone will receive it")


def sequence(strengths, improvements):
    if type(strengths) is not tuple or len(strengths) > MAX_NOTES:
        raise ValueError(f"strengths: tuple of 0 to {MAX_NOTES} notes required")
    if type(improvements) is not tuple or len(improvements) > MAX_NOTES:
        raise ValueError(f"improvements: tuple of 0 to {MAX_NOTES} notes required")
    for i, n in enumerate(strengths):
        if type(n) is not str or not 1 <= len(n) <= MAX_NOTE:
            raise ValueError(f"strengths[{i}]: note of 1 to {MAX_NOTE} characters required")
    for i, n in enumerate(improvements):
        if type(n) is not str or not 1 <= len(n) <= MAX_NOTE:
            raise ValueError(f"improvements[{i}]: note of 1 to {MAX_NOTE} characters required")
    out = []
    n = min(len(strengths), len(improvements))
    for k in range(n):
        out.append(("strength", k, strengths[k]))
        out.append(("improvement", k, improvements[k]))
    for k in range(n, len(strengths)):
        out.append(("strength", k, strengths[k]))
    return {"sequence": tuple(out), "held": tuple(range(n, len(improvements))),
            "strength_count": len(strengths), "improvement_count": len(improvements),
            "constructive_balance_validated": False, "not_claimed": NOT_CLAIMED}
