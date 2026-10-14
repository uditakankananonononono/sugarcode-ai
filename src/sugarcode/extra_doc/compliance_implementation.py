"""Row 530 compliance implementation (PARTIAL): requirement-to-control coverage bookkeeping.

Requirements are (rid, title) pairs and controls are (cid, title, rids) triples, where rids lists the requirement
ids the control addresses. Every id is a non-empty string up to 20 characters and unique within its own list;
every title is a non-empty string up to 80 characters. A control may list from 0 to 50 requirement ids, each of
which must exist. coverage(requirements, controls) reports, in input order, the controls addressing each
requirement, the requirements no control addresses, the controls addressing nothing, the exact covered share of
the requirements and the most controls on any one requirement. Whether the controls actually satisfy anything,
or which regulation applies, is not judged here."""
from fractions import Fraction

MAX_REQUIREMENTS = 100
MAX_CONTROLS = 200
MAX_ID = 20
MAX_TITLE = 80
MAX_REFS = 50
STATUS_NOTE = ("PARTIAL: coverage bookkeeping over supplied ids only; no judgment of whether any control "
               "satisfies any requirement or regulation")


def _entries(rows, label, n_max, with_refs):
    if not isinstance(rows, (list, tuple)):
        raise ValueError(f"{label}: list required")
    hi = 1 if label == "requirements" else 0
    if not hi <= len(rows) <= n_max:
        raise ValueError(f"{label}: {hi} to {n_max} entries required")
    want = 3 if with_refs else 2
    shape = "(cid, title, rids)" if with_refs else "(rid, title)"
    out, seen = [], set()
    for i, r in enumerate(rows):
        if not isinstance(r, (list, tuple)):
            raise ValueError(f"{label}[{i}]: {shape} required")
        if len(r) != want:
            raise ValueError(f"{label}[{i}]: {want} entries required")
        rid, title = r[0], r[1]
        if not isinstance(rid, str) or not rid or len(rid) > MAX_ID:
            raise ValueError(f"{label}[{i}] id: non-empty string up to {MAX_ID} characters required")
        if rid in seen:
            raise ValueError(f"{label}[{i}]: duplicate id {rid}")
        seen.add(rid)
        if not isinstance(title, str) or not title.strip() or len(title) > MAX_TITLE:
            raise ValueError(f"{label}[{i}] title: non-empty string up to {MAX_TITLE} characters required")
        refs = None
        if with_refs:
            refs = r[2]
            if not isinstance(refs, (list, tuple)):
                raise ValueError(f"{label}[{i}] rids: list required")
            if len(refs) > MAX_REFS:
                raise ValueError(f"{label}[{i}] rids: at most {MAX_REFS} entries allowed")
            for j, x in enumerate(refs):
                if not isinstance(x, str) or not x or len(x) > MAX_ID:
                    raise ValueError(f"{label}[{i}] rids[{j}]: non-empty string up to {MAX_ID} characters required")
            if len(set(refs)) != len(refs):
                raise ValueError(f"{label}[{i}] rids: duplicates not allowed")
            refs = list(refs)
        out.append((rid, title, refs))
    return out


def coverage(requirements, controls):
    reqs = _entries(requirements, "requirements", MAX_REQUIREMENTS, False)
    ctls = _entries(controls, "controls", MAX_CONTROLS, True)
    known = {r[0] for r in reqs}
    for i, (_, _, refs) in enumerate(ctls):
        for x in refs:
            if x not in known:
                raise ValueError(f"controls[{i}] rids: unknown requirement {x}")
    per_req = []
    for rid, title, _ in reqs:
        hits = [cid for cid, _, refs in ctls if rid in refs]
        per_req.append({"rid": rid, "title": title, "controls": hits})
    uncovered = [r["rid"] for r in per_req if not r["controls"]]
    orphan = [cid for cid, _, refs in ctls if not refs]
    covered = len(reqs) - len(uncovered)
    return {"requirements": per_req, "uncovered": uncovered, "orphan_controls": orphan,
            "covered_share": Fraction(covered, len(reqs)),
            "max_controls_per_requirement": max(len(r["controls"]) for r in per_req),
            "status_note": STATUS_NOTE}
