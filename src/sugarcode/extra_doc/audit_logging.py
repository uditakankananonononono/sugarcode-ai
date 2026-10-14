"""Row 529 audit logging: a tamper-evident hash chain over event rows.

Each event is (seq, ts, action): seq the whole-number position starting at 1 with no gaps, ts a whole-number
timestamp from 0 to 1e12 that never decreases, and action a non-empty string up to 60 characters. The chain
digest of an event is sha256 of "PREV|SEQ|TS|ACTION" in UTF-8, where PREV is the previous event's digest as
lowercase hex and the first event's PREV is 64 zero characters; the digest is the lowercase hex of that hash.
chain(events) returns the events with their digests. verify(rows) checks the digest format, the seq positions,
the timestamp order and every recomputed digest. Only a digest mismatch is reported as first_bad (the index of the
first row whose digest does not recompute, None when all do); a row with a malformed shape, seq, ts, action or
digest raises ValueError for the whole call, even if an earlier row was tampered with. An action may not contain a
lone surrogate character (U+D800 to U+DFFF), which cannot be hashed as UTF-8.
A digest mismatch detects an inconsistent supplied chain. A writer able to replace
all rows and recompute hashes can produce a chain that verifies: this helper has
no trusted external head/checkpoint, authentication, persistence or append-only
enforcement. It does not say whether the events were worth logging."""
import hashlib

GENESIS = "0" * 64
MAX_ENTRIES = 1000
MAX_ACTION = 60
MAX_TS = 10**12
STATUS_NOTE = ("PARTIAL: hash-chain arithmetic over supplied rows only; no judgment of whether the right "
               "events were logged")


def _int(v, name, lo, hi):
    if type(v) is not int:
        raise ValueError(f"{name}: integer required")
    if not lo <= v <= hi:
        raise ValueError(f"{name}: must be within {lo} to {hi}")
    return v


def _digest(prev, seq, ts, action):
    return hashlib.sha256(f"{prev}|{seq}|{ts}|{action}".encode("utf-8")).hexdigest()


def _shape(events, with_digests):
    label = "rows" if with_digests else "events"
    if type(events) not in (list, tuple):
        raise ValueError(f"{label}: list required")
    if not 1 <= len(events) <= MAX_ENTRIES:
        raise ValueError(f"{label}: 1 to {MAX_ENTRIES} entries required")
    want = 4 if with_digests else 3
    out = []
    for i, e in enumerate(events):
        if type(e) not in (list, tuple):
            raise ValueError(f"{label}[{i}]: (seq, ts, action{', digest' if with_digests else ''}) required")
        if len(e) != want:
            raise ValueError(f"{label}[{i}]: {want} entries required")
        seq, ts, action = e[0], e[1], e[2]
        seq = _int(seq, f"{label}[{i}] seq", 1, MAX_ENTRIES)
        if seq != i + 1:
            raise ValueError(f"{label}[{i}] seq: must be {i + 1}")
        ts = _int(ts, f"{label}[{i}] ts", 0, MAX_TS)
        if out and ts < out[-1][1]:
            raise ValueError(f"{label}[{i}] ts: must not decrease")
        if type(action) is not str or not action or len(action) > MAX_ACTION:
            raise ValueError(f"{label}[{i}] action: non-empty string up to {MAX_ACTION} characters required")
        if any("\ud800" <= ch <= "\udfff" for ch in action):
            raise ValueError(f"{label}[{i}] action: lone surrogate characters are not allowed")
        row = [seq, ts, action]
        if with_digests:
            d = e[3]
            if type(d) is not str or len(d) != 64 or any(c not in "0123456789abcdef" for c in d):
                raise ValueError(f"{label}[{i}] digest: 64 lowercase hex characters required")
            row.append(d)
        out.append(row)
    return out


def chain(events):
    rows = _shape(events, False)
    prev = GENESIS
    out = []
    for seq, ts, action in rows:
        d = _digest(prev, seq, ts, action)
        out.append({"seq": seq, "ts": ts, "action": action, "digest": d})
        prev = d
    return {"events": out, "head": prev, "status_note": STATUS_NOTE}


def verify(rows):
    rows = _shape(rows, True)
    prev = GENESIS
    first_bad = None
    for i, (seq, ts, action, d) in enumerate(rows):
        if _digest(prev, seq, ts, action) != d:
            first_bad = i
            break
        prev = d
    return {"ok": first_bad is None, "checked": len(rows), "first_bad": first_bad, "status_note": STATUS_NOTE}
