"""Row 710 Persuasive Writing (PARTIAL): structure check on a supplied outline of labelled paragraphs.

outline is a list of 1..50 labels, each exactly "claim", "evidence", "counter", "rebuttal" or "call". Issues
are (index, kind) sorted by index then kind:
  opening_not_claim            index 0 is not "claim";
  closing_not_call             the last label is not "call";
  call_before_end              a "call" that is not the last label;
  claim_without_evidence       a "claim" with no "evidence" after it before the next "claim" or the end;
  counter_without_rebuttal     a "counter" whose next label is not "rebuttal" (or that is last);
  rebuttal_without_counter     a "rebuttal" whose previous label is not "counter" (or that is first).
These six rules and the range are this module's own choices about outline shape, not a rule of writing. It
checks a list of labels. It reads no text and says nothing about whether any writing is convincing, true or
fair, or whether it would change anyone's mind."""
MAX_LABELS = 50
LABELS = ("claim", "evidence", "counter", "rebuttal", "call")
NOT_CLAIMED = ("persuasive effect", "truth or fairness of the content", "quality of the writing",
               "audience response", "runtime behaviour")


def check(outline):
    if type(outline) is not list or not 1 <= len(outline) <= MAX_LABELS:
        raise ValueError(f"outline: list of 1 to {MAX_LABELS} required")
    for i, label in enumerate(outline):
        if type(label) is not str or label not in LABELS:
            raise ValueError(f"outline[{i}]: one of {', '.join(LABELS)} required")
    n = len(outline)
    issues = []
    if outline[0] != "claim":
        issues.append((0, "opening_not_claim"))
    if outline[-1] != "call":
        issues.append((n - 1, "closing_not_call"))
    for i, label in enumerate(outline):
        if label == "call" and i != n - 1:
            issues.append((i, "call_before_end"))
        elif label == "claim":
            tail = outline[i + 1:]
            stop = tail.index("claim") if "claim" in tail else len(tail)
            if "evidence" not in tail[:stop]:
                issues.append((i, "claim_without_evidence"))
        elif label == "counter" and outline[i + 1:i + 2] != ["rebuttal"]:
            issues.append((i, "counter_without_rebuttal"))
        elif label == "rebuttal" and (i == 0 or outline[i - 1] != "counter"):
            issues.append((i, "rebuttal_without_counter"))
    return {"issues": sorted(issues), "structure_complete": not issues,
            "writing_validated": False, "not_claimed": NOT_CLAIMED}
