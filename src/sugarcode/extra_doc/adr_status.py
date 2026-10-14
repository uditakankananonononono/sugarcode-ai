"""Row 705 Architecture Decision Records : checking status and supersession links across a record list.

records is a list of 1..64 (id, status, supersedes) tuples. id is a whole number 1..9999, distinct across the
list. status is exactly "proposed", "accepted", "rejected", "deprecated" or "superseded". supersedes is None or
the id of an earlier record (smaller than this id) that is present in the list. Issues, listed as (id, kind)
sorted by id then kind, are:
  superseder_status_invalid      a record that supersedes another is neither "accepted" nor "superseded";
  target_not_marked_superseded   a record that is superseded has a status other than "superseded";
  superseded_without_successor   a record is "superseded" but no record names it in supersedes;
  target_superseded_twice        a record is named in supersedes by more than one record (reported on it).
These ranges and these four rules are this module's own choices. It checks supplied tuples. It reads no
documents and says nothing about whether any decision is right or well recorded."""
MAX_RECORDS, MAX_ID = 64, 9999
STATUSES = ("proposed", "accepted", "rejected", "deprecated", "superseded")
NOT_CLAIMED = ("quality of any decision", "content of the records", "completeness of the log",
               "who approved what", "runtime behaviour")


def check(records):
    if type(records) is not list or not 1 <= len(records) <= MAX_RECORDS:
        raise ValueError(f"records: list of 1 to {MAX_RECORDS} required")
    for i, r in enumerate(records):
        if type(r) is not tuple or len(r) != 3:
            raise ValueError(f"records[{i}]: (id, status, supersedes) tuple required")
        if type(r[0]) is not int or not 1 <= r[0] <= MAX_ID:
            raise ValueError(f"records[{i}] id: whole number 1 to {MAX_ID} required")
        if type(r[1]) is not str or r[1] not in STATUSES:
            raise ValueError(f"records[{i}] status: one of {', '.join(STATUSES)} required")
    ids = [r[0] for r in records]
    if len(set(ids)) != len(ids):
        raise ValueError("records: ids must be distinct")
    for i, (rid, _, sup) in enumerate(records):
        if sup is not None and (type(sup) is not int or sup not in ids or sup >= rid):
            raise ValueError(f"records[{i}] supersedes: None or the id of an earlier record in the list required")
    status = {r[0]: r[1] for r in records}
    named = [r[2] for r in records if r[2] is not None]
    issues = []
    for rid, st, sup in records:
        if sup is not None:
            if st not in ("accepted", "superseded"):
                issues.append((rid, "superseder_status_invalid"))
            if status[sup] != "superseded":
                issues.append((sup, "target_not_marked_superseded"))
        if st == "superseded" and rid not in named:
            issues.append((rid, "superseded_without_successor"))
    issues.extend((t, "target_superseded_twice") for t in sorted(set(named)) if named.count(t) > 1)
    return {"issues": sorted(set(issues)), "links_consistent": not issues,
            "adr_validated": False, "not_claimed": NOT_CLAIMED}
