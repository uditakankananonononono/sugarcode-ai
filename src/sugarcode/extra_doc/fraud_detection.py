"""Row 551 fraud detection (PARTIAL): two fixed screening rules over a list of transactions.

transactions is a list of (ts, amount) pairs, 1 to 500 of them: ts a whole-number second count from 0 to 1e12 that
never decreases along the list, amount a whole-number minor-unit amount from 0 to 1e9. Rule "large" flags a
transaction whose amount is greater than amount_limit (1 to 1e9). Rule "burst" flags a transaction when the
number of transactions with ts in the half-open window (ts - window, ts] is greater than max_count (1 to 100);
window is 1 to 86400 seconds and the count includes the transaction itself and any other with the same ts.
screen returns the flagged transactions with their index and rules. A flag is a prompt for a person to look, not a
finding of fraud, and unflagged transactions are not cleared."""
from bisect import bisect_right

MAX_TX = 500
MAX_TS = 10**12
MAX_AMOUNT = 10**9
MAX_COUNT = 100
MAX_WINDOW = 86400
STATUS_NOTE = ("PARTIAL: two fixed rules over supplied transactions; a flag is a prompt to review, not a finding "
               "of fraud, and unflagged is not cleared")


def _int(v, name, lo, hi):
    if isinstance(v, bool) or not isinstance(v, int):
        raise ValueError(f"{name}: integer required")
    if not lo <= v <= hi:
        raise ValueError(f"{name}: must be within {lo} to {hi}")
    return v


def screen(transactions, amount_limit, max_count, window):
    amount_limit = _int(amount_limit, "amount_limit", 1, MAX_AMOUNT)
    max_count = _int(max_count, "max_count", 1, MAX_COUNT)
    window = _int(window, "window", 1, MAX_WINDOW)
    if not isinstance(transactions, (list, tuple)):
        raise ValueError("transactions: list required")
    if not 1 <= len(transactions) <= MAX_TX:
        raise ValueError(f"transactions: 1 to {MAX_TX} entries required")
    tx = []
    for i, t in enumerate(transactions):
        if not isinstance(t, (list, tuple)):
            raise ValueError(f"transactions[{i}]: (ts, amount) required")
        if len(t) != 2:
            raise ValueError(f"transactions[{i}]: 2 entries required")
        ts = _int(t[0], f"transactions[{i}] ts", 0, MAX_TS)
        amount = _int(t[1], f"transactions[{i}] amount", 0, MAX_AMOUNT)
        if tx and ts < tx[-1][0]:
            raise ValueError(f"transactions[{i}] ts: must not decrease")
        tx.append((ts, amount))
    stamps = [t[0] for t in tx]
    flagged = []
    for i, (ts, amount) in enumerate(tx):
        rules = []
        if amount > amount_limit:
            rules.append("large")
        if bisect_right(stamps, ts) - bisect_right(stamps, ts - window) > max_count:
            rules.append("burst")
        if rules:
            flagged.append({"index": i, "ts": ts, "amount": amount, "rules": rules})
    return {"flagged": flagged, "checked": len(tx), "status_note": STATUS_NOTE}
