"""Row 667 Dependency Injection (PARTIAL): lifetime check over a supplied service registration table.

services is a list of 1..32 (name, lifetime, dependencies) tuples. name is 1..30 characters of a-z, 0-9 and
underscore starting with a letter (ASCII only), distinct across the table. lifetime is exactly "singleton",
"scoped" or "transient", ranked 2, 1, 0 by how long an instance lives. dependencies is a list of 0..8 distinct
names of other services in the table. A dependency is a captive_dependency violation when its lifetime rank is
lower than the rank of the service that holds it. Violations are listed as (service, dependency) in table order,
then dependency order. These ranges and this rank rule are this module's own choices. It checks a supplied
table. It builds no container, resolves no objects and says nothing about whether the wiring is a good design."""
import re

MAX_SERVICES, MAX_DEPS = 32, 8
RANK = {"singleton": 2, "scoped": 1, "transient": 0}
NOT_CLAIMED = ("a dependency injection container", "object resolution", "thread safety",
               "design quality", "runtime behaviour")
_NAME = re.compile(r"[a-z][a-z0-9_]{0,29}")


def check(services):
    if type(services) is not list or not 1 <= len(services) <= MAX_SERVICES:
        raise ValueError(f"services: list of 1 to {MAX_SERVICES} required")
    for i, row in enumerate(services):
        if type(row) is not tuple or len(row) != 3:
            raise ValueError(f"services[{i}]: (name, lifetime, dependencies) tuple required")
        if type(row[0]) is not str or _NAME.fullmatch(row[0]) is None:
            raise ValueError(f"services[{i}] name: name of a-z, 0-9, _ (1 to 30, starting with a letter) required")
        if type(row[1]) is not str or row[1] not in RANK:
            raise ValueError(f"services[{i}] lifetime: 'singleton', 'scoped' or 'transient' required")
        if type(row[2]) is not list or len(row[2]) > MAX_DEPS:
            raise ValueError(f"services[{i}] dependencies: list of 0 to {MAX_DEPS} required")
    life = {r[0]: r[1] for r in services}
    if len(life) != len(services):
        raise ValueError("services: names must be distinct")
    for i, (name, _, deps) in enumerate(services):
        for j, d in enumerate(deps):
            if type(d) is not str or d not in life:
                raise ValueError(f"services[{i}] dependencies[{j}]: name of a service in the table required")
            if d == name:
                raise ValueError(f"services[{i}] dependencies[{j}]: a service cannot depend on itself")
        if len(set(deps)) != len(deps):
            raise ValueError(f"services[{i}] dependencies: names must be distinct")
    violations = [(name, d) for name, lt, deps in services for d in deps if RANK[life[d]] < RANK[lt]]
    return {"violations": violations, "lifetimes_consistent": not violations,
            "di_validated": False, "not_claimed": NOT_CLAIMED}
