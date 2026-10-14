"""Row 451: Vendor Selection - Chooses suppliers.

PARTIAL: this module only filters vendor scores against a minimum
score and reports which positions qualify, in the order given. It
makes no claim that the scores measure anything real or that the
qualifying vendors are good suppliers.

Caps (2 to 15 vendors, scores 0 to 100, minimum 0 to 100) are this
module's own choices, not a domain standard.
"""
from __future__ import annotations

MAX_VENDORS = 15
MAX_SCORE = 100

NOT_CLAIMED = ("score_validity", "supplier_quality", "selection_advice")


def shortlist(scores, minimum):
    if type(scores) is not tuple or not 2 <= len(scores) <= MAX_VENDORS:
        raise ValueError(f"scores: tuple of 2 to {MAX_VENDORS} entries required")
    for i, s in enumerate(scores):
        if type(s) is not int or not 0 <= s <= MAX_SCORE:
            raise ValueError(f"scores[{i}]: whole number 0 to {MAX_SCORE} required")
    if type(minimum) is not int or not 0 <= minimum <= MAX_SCORE:
        raise ValueError(f"minimum: whole number 0 to {MAX_SCORE} required")
    qualified = tuple(i for i in range(len(scores)) if scores[i] >= minimum)
    best = scores[max(range(len(scores)), key=lambda i: scores[i])]
    best_positions = tuple(i for i in range(len(scores)) if scores[i] == best)
    return {"vendor_shortlist_validated": False, "not_claimed": NOT_CLAIMED,
            "qualified_positions": qualified, "qualified_count": len(qualified),
            "any_qualified": len(qualified) > 0, "best_score": best,
            "best_positions": best_positions}
