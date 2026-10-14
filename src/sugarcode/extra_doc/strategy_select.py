"""Row 664 Strategy Pattern (PARTIAL): choosing one named strategy per input size from a threshold table.

table is a list of 1..16 (name, max_size) tuples with strictly increasing max_size (whole numbers 0..10**9);
names are 1..30 characters of a-z, 0-9 and underscore starting with a letter (ASCII only) and distinct. sizes is
a list of 1..100 whole numbers 0..10**9. Each size gets the first table entry whose max_size is at least the
size, or None when it is above every threshold. The result also counts how many sizes each entry received. These
ranges are this module's own choices. It selects names from supplied data. It runs no algorithm and says
nothing about which strategy is faster or better."""
import re

MAX_TABLE, MAX_SIZES, MAX_SIZE = 16, 100, 10 ** 9
NOT_CLAIMED = ("an implementation of the pattern", "algorithm performance", "which strategy is best",
               "design quality", "runtime behaviour")
_NAME = re.compile(r"[a-z][a-z0-9_]{0,29}")


def choose(table, sizes):
    if type(table) is not list or not 1 <= len(table) <= MAX_TABLE:
        raise ValueError(f"table: list of 1 to {MAX_TABLE} required")
    for i, row in enumerate(table):
        if type(row) is not tuple or len(row) != 2:
            raise ValueError(f"table[{i}]: (name, max_size) tuple required")
        if type(row[0]) is not str or _NAME.fullmatch(row[0]) is None:
            raise ValueError(f"table[{i}] name: name of a-z, 0-9, _ (1 to 30, starting with a letter) required")
        if type(row[1]) is not int or not 0 <= row[1] <= MAX_SIZE:
            raise ValueError(f"table[{i}] max_size: whole number 0 to {MAX_SIZE} required")
    if len({r[0] for r in table}) != len(table):
        raise ValueError("table: names must be distinct")
    if any(table[i][1] >= table[i + 1][1] for i in range(len(table) - 1)):
        raise ValueError("table: max_size must be strictly increasing")
    if type(sizes) is not list or not 1 <= len(sizes) <= MAX_SIZES:
        raise ValueError(f"sizes: list of 1 to {MAX_SIZES} required")
    for i, s in enumerate(sizes):
        if type(s) is not int or not 0 <= s <= MAX_SIZE:
            raise ValueError(f"sizes[{i}]: whole number 0 to {MAX_SIZE} required")
    chosen, counts = [], [0] * len(table)
    for s in sizes:
        k = next((j for j, r in enumerate(table) if s <= r[1]), None)
        chosen.append(None if k is None else table[k][0])
        if k is not None:
            counts[k] += 1
    return {"chosen": chosen, "counts": counts, "unmatched": chosen.count(None),
            "strategy_validated": False, "not_claimed": NOT_CLAIMED}
