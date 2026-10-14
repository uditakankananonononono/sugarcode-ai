"""Row 528 key management: rotation-schedule bookkeeping for a key inventory.

This checks dates only. It does not handle key material and says nothing about how secure any key or process is.
Each key is (name, created_day, rotation_days, revoked): a non-empty name up to 60 characters, created_day a whole
day number from 0 to 1,000,000 that must not be after today, rotation_days a whole number from 1 to 3650 and
revoked a real bool. due_day is created_day + rotation_days and days_left is due_day - today. Status is revoked
for a revoked key, otherwise overdue when days_left is below 0, due_soon when days_left is from 0 up to and
including warn_days, else ok. Which rotation period is right is not judged here."""

MAX_KEYS = 500
MAX_NAME = 60
MAX_DAY = 1_000_000
MAX_ROTATION = 3650
MAX_WARN = 3650
STATUS_NOTE = ("PARTIAL: date arithmetic over a supplied inventory only; no key material handled and no judgment "
               "of security or of the rotation periods")
STATUSES = ("revoked", "overdue", "due_soon", "ok")


def _int(v, name, lo, hi):
    if type(v) is not int:
        raise ValueError(f"{name}: integer required")
    if not lo <= v <= hi:
        raise ValueError(f"{name}: must be within {lo} to {hi}")
    return v


def audit(keys, today, warn_days=14):
    t = _int(today, "today", 0, MAX_DAY)
    warn = _int(warn_days, "warn_days", 0, MAX_WARN)
    if type(keys) not in (list, tuple):
        raise ValueError("keys: list required")
    if not 1 <= len(keys) <= MAX_KEYS:
        raise ValueError(f"keys: 1 to {MAX_KEYS} entries required")
    rows, seen = [], set()
    for i, k in enumerate(keys):
        if type(k) not in (list, tuple):
            raise ValueError(f"keys[{i}]: (name, created_day, rotation_days, revoked) required")
        if len(k) != 4:
            raise ValueError(f"keys[{i}]: 4 entries required")
        name, created, rot, revoked = k
        if type(name) is not str or not name.strip() or len(name) > MAX_NAME:
            raise ValueError(f"keys[{i}] name: non-empty string up to {MAX_NAME} characters required")
        if name in seen:
            raise ValueError(f"keys[{i}]: duplicate key {name}")
        seen.add(name)
        c = _int(created, f"keys[{i}] created_day", 0, MAX_DAY)
        if c > t:
            raise ValueError(f"keys[{i}] created_day: must not be after today")
        r = _int(rot, f"keys[{i}] rotation_days", 1, MAX_ROTATION)
        if type(revoked) is not bool:
            raise ValueError(f"keys[{i}] revoked: bool required")
        due = c + r
        left = due - t
        status = "revoked" if revoked else "overdue" if left < 0 else "due_soon" if left <= warn else "ok"
        rows.append({"name": name, "age_days": t - c, "due_day": due, "days_left": left, "status": status})
    counts = {s: sum(1 for x in rows if x["status"] == s) for s in STATUSES}
    return {"keys": rows, "counts": counts, "status_note": STATUS_NOTE}
