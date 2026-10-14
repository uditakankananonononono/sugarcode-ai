"""Row 704 API Documentation : comparing documented parameters with the parameters an API lists.

endpoints is a list of 1..32 (name, params) tuples; docs is a list of 0..32 (name, documented_params) tuples.
Names and parameter names are 1..30 characters of a-z, 0-9 and underscore starting with a letter (ASCII only).
Each params list holds 0..8 distinct names; endpoint names are distinct and doc names are distinct. The result
has, per endpoint in endpoint order, the parameters missing from its doc (in endpoint order) and the documented
parameters the endpoint does not have (in doc order); endpoints with no doc entry at all; and doc entries that
name no endpoint. These ranges are this module's own choices. It compares two supplied lists. It reads no API
spec, judges no wording and says nothing about whether the documentation is accurate, clear or complete."""
import re

MAX_ENDPOINTS, MAX_PARAMS = 32, 8
NOT_CLAIMED = ("accuracy of the documentation", "clarity or wording", "completeness beyond parameter names",
               "an API specification", "runtime behaviour")
_NAME = re.compile(r"[a-z][a-z0-9_]{0,29}")


def _name(label, v):
    if type(v) is not str or _NAME.fullmatch(v) is None:
        raise ValueError(f"{label}: name of a-z, 0-9, _ (1 to 30, starting with a letter) required")


def _table(label, rows, low):
    if type(rows) is not list or not low <= len(rows) <= MAX_ENDPOINTS:
        raise ValueError(f"{label}: list of {low} to {MAX_ENDPOINTS} required")
    for i, row in enumerate(rows):
        if type(row) is not tuple or len(row) != 2:
            raise ValueError(f"{label}[{i}]: (name, params) tuple required")
        _name(f"{label}[{i}] name", row[0])
        if type(row[1]) is not list or len(row[1]) > MAX_PARAMS:
            raise ValueError(f"{label}[{i}] params: list of 0 to {MAX_PARAMS} required")
        for j, p in enumerate(row[1]):
            _name(f"{label}[{i}] params[{j}]", p)
        if len(set(row[1])) != len(row[1]):
            raise ValueError(f"{label}[{i}] params: names must be distinct")
    if len({r[0] for r in rows}) != len(rows):
        raise ValueError(f"{label}: names must be distinct")


def compare(endpoints, docs):
    _table("endpoints", endpoints, 1)
    _table("docs", docs, 0)
    doc = dict(docs)
    rows = []
    for name, params in endpoints:
        if name in doc:
            rows.append({"endpoint": name, "undocumented_params": [p for p in params if p not in doc[name]],
                         "stale_doc_params": [p for p in doc[name] if p not in params]})
    return {"endpoints": rows,
            "endpoints_without_docs": [n for n, _ in endpoints if n not in doc],
            "docs_without_endpoint": [n for n, _ in docs if n not in {e[0] for e in endpoints}],
            "documentation_validated": False, "not_claimed": NOT_CLAIMED}
