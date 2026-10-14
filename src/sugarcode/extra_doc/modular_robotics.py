"""Row 948, Modular Robotics: docking modules into structures.

Reconfigurable robots dock module to module, and docked clusters merge:
docking a pair that belongs to two clusters joins them into one
structure.  dock() folds the supplied dock records, merges the clusters,
and reports the resulting structures.

Input rows: (module 1-8, partner 1-8).  Output: {'total', 'modules':
distinct modules, 'structures': connected structure count, 'largest':
modules in the largest structure, 'singletons': sorted modules docked
only to themselves}.  Reported: docking a-b then b-c makes one structure
of 3; docking a-b then c-d leaves 2 structures of 2 until b-c joins
them into 4; a self-dock (a,a) leaves a a singleton structure.
"""

from typing import Any

MAX_ROWS = 100
MAX_NAME = 8

SCOPE = 'PARTIAL: connectivity only; no geometry or kinematics modeled'
NOT_CLAIMED = (
    'does not model docking mechanics or alignment',
    'does not plan reconfiguration sequences',
    'does not simulate structure locomotion',
    'does not undock modules once docked',
)


def _check_name(name: Any, row: int, field: str) -> None:
    if not isinstance(name, str) or type(name) is not str:
        raise TypeError(
            f'row {row}: {field} must be str, got {type(name).__name__}')
    if not 1 <= len(name) <= MAX_NAME:
        raise ValueError(f'row {row}: {field} must be 1-8 chars')


def _find(parent: dict, module: str) -> str:
    root = module
    while parent[root] != root:
        root = parent[root]
    while parent[module] != root:
        parent[module], module = root, parent[module]
    return root


def dock(rows: Any) -> dict:
    """Return the structure summary for the supplied dock records."""
    if type(rows) not in (list, tuple):
        raise TypeError(f'rows must be list or tuple, got {type(rows).__name__}')
    if len(rows) > MAX_ROWS:
        raise ValueError(f'rows must contain at most {MAX_ROWS} entries')
    parent: dict = {}
    for index, row in enumerate(rows, 1):
        if type(row) not in (list, tuple):
            raise TypeError(
                f'row {index}: expected (module, partner) tuple, got {type(row).__name__}')
        if len(row) != 2:
            raise ValueError(
                f'row {index}: expected 2 fields, got {len(row)}')
        module, partner = row
        _check_name(module, index, 'module')
        _check_name(partner, index, 'partner')
        parent.setdefault(module, module)
        parent.setdefault(partner, partner)
        root_m = _find(parent, module)
        root_p = _find(parent, partner)
        if root_m != root_p:
            parent[root_p] = root_m
    sizes: dict = {}
    for module in parent:
        root = _find(parent, module)
        sizes[root] = sizes.get(root, 0) + 1
    singletons = sorted(
        module for module in parent
        if parent[module] == module and sizes.get(module, 0) == 1)
    return {'total': len(rows), 'modules': len(parent),
            'structures': len(sizes),
            'largest': max(sizes.values()) if sizes else 0,
            'singletons': singletons}
