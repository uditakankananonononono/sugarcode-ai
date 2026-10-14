"""Row 616 API gateway (PARTIAL): choosing a backend for a method and path from a route table.

routes is a list of 1 to 50 (prefix, methods, target) triples. prefix starts with "/", is at most 60 characters,
has no whitespace and no trailing "/" unless it is exactly "/", and is unique in the table; methods is a list of 1
to 5 distinct names from GET, POST, PUT, PATCH, DELETE; target is a non-empty string up to 30 characters. A prefix
matches a path when the prefix is "/" or the path equals it or continues it after a "/" ("/api" matches "/api" and
"/api/x" but not "/apix"). route(routes, method, path) takes the longest matching prefix that allows the method
and returns status 200 with its target. If prefixes match but none allows the method the status is 405 with the
sorted union of the methods those routes allow; if none match the status is 404. method is one of the five names
and path starts with "/" and is at most 200 characters. This picks a name from a table; it does not forward
requests, authenticate, or rate limit."""

MAX_ROUTES = 50
MAX_PREFIX = 60
MAX_TARGET = 30
MAX_PATH = 200
METHODS = ("GET", "POST", "PUT", "PATCH", "DELETE")
STATUS_NOTE = ("PARTIAL: route-table lookup on supplied strings only; nothing is forwarded, authenticated or "
               "rate limited")


def route(routes, method, path):
    if type(method) is not str:
        raise ValueError("method: string required")
    if method not in METHODS:
        raise ValueError("method: must be one of GET, POST, PUT, PATCH, DELETE")
    if type(path) is not str:
        raise ValueError("path: string required")
    if not path.startswith("/") or len(path) > MAX_PATH:
        raise ValueError(f"path: must start with / and be at most {MAX_PATH} characters")
    if type(routes) not in (list, tuple):
        raise ValueError("routes: list required")
    if not 1 <= len(routes) <= MAX_ROUTES:
        raise ValueError(f"routes: 1 to {MAX_ROUTES} entries required")
    table = []
    seen = set()
    for i, r in enumerate(routes):
        if type(r) not in (list, tuple):
            raise ValueError(f"routes[{i}]: (prefix, methods, target) required")
        if len(r) != 3:
            raise ValueError(f"routes[{i}]: 3 entries required")
        prefix, methods, target = r
        if (type(prefix) is not str or not prefix.startswith("/") or len(prefix) > MAX_PREFIX
                or any(c.isspace() for c in prefix) or (prefix != "/" and prefix.endswith("/"))):
            raise ValueError(f"routes[{i}] prefix: must start with /, have no whitespace or trailing / and be at "
                             f"most {MAX_PREFIX} characters")
        if prefix in seen:
            raise ValueError(f"routes[{i}] prefix: duplicate")
        seen.add(prefix)
        if type(methods) not in (list, tuple) or not 1 <= len(methods) <= len(METHODS):
            raise ValueError(f"routes[{i}] methods: list of 1 to {len(METHODS)} entries required")
        for m in methods:
            if type(m) is not str or m not in METHODS:
                raise ValueError(f"routes[{i}] methods: each must be one of GET, POST, PUT, PATCH, DELETE")
        if len(set(methods)) != len(methods):
            raise ValueError(f"routes[{i}] methods: duplicate entry")
        if type(target) is not str or not target or len(target) > MAX_TARGET:
            raise ValueError(f"routes[{i}] target: non-empty string up to {MAX_TARGET} characters required")
        table.append((prefix, tuple(methods), target))
    matching = [t for t in table if t[0] == "/" or path == t[0] or path.startswith(t[0] + "/")]
    matching.sort(key=lambda t: -len(t[0]))
    for prefix, methods, target in matching:
        if method in methods:
            return {"status": 200, "target": target, "prefix": prefix, "allowed": None,
                    "status_note": STATUS_NOTE}
    if matching:
        allowed = sorted({m for _, ms, _ in matching for m in ms})
        return {"status": 405, "target": None, "prefix": None, "allowed": allowed, "status_note": STATUS_NOTE}
    return {"status": 404, "target": None, "prefix": None, "allowed": None, "status_note": STATUS_NOTE}
