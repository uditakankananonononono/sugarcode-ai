"""Row 951, Molecular Nanotechnology: pairing atoms into bonds.

Atom-precise manufacturing pairs every supplied atom into a bond; a
structure assembles only when every atom type comes in an even quantity,
leaving nothing unpaired.  assemble() tallies the supplied atoms per
type and reports the bond count and the loose atoms.

Input rows: (atom 1-8, atoms int 0-10).  Output: {'total', 'assembled':
True when every atom type's tally is even, 'pairs': {atom: tally // 2},
'loose': sorted atom types with an odd tally}.  Reported: a tally of 5
makes 2 pairs and leaves the type loose; an even tally of 0 (no rows for
a type) never appears because only supplied types are tallied; with no
records there is nothing loose and the structure assembles vacuously.
"""

from typing import Any

MAX_ROWS = 100
MAX_NAME = 8
MIN_ATOMS = 0
MAX_ATOMS = 10
BOND = 2

SCOPE = 'PARTIAL: stoichiometric tally only; no positional chemistry modeled'
NOT_CLAIMED = (
    'does not model atomic positions or lattice geometry',
    'does not simulate reaction energies',
    'does not plan assembly sequences',
    'does not model bond types beyond pairing',
)


def _check_name(atom: Any, row: int) -> None:
    if not isinstance(atom, str) or type(atom) is not str:
        raise TypeError(
            f'row {row}: atom must be str, got {type(atom).__name__}')
    if not 1 <= len(atom) <= MAX_NAME:
        raise ValueError(f'row {row}: atom must be 1-8 chars')


def _check_atoms(atoms: Any, row: int) -> None:
    if type(atoms) is not int:
        raise TypeError(
            f'row {row}: atoms must be int, got {type(atoms).__name__}')
    if not MIN_ATOMS <= atoms <= MAX_ATOMS:
        raise ValueError(
            f'row {row}: atoms must be {MIN_ATOMS}-{MAX_ATOMS}, got {atoms}')


def assemble(rows: Any) -> dict:
    """Return the bond tally for the supplied atom records."""
    if type(rows) not in (list, tuple):
        raise TypeError(f'rows must be list or tuple, got {type(rows).__name__}')
    if len(rows) > MAX_ROWS:
        raise ValueError(f'rows must contain at most {MAX_ROWS} entries')
    tally: dict = {}
    for index, row in enumerate(rows, 1):
        if type(row) not in (list, tuple):
            raise TypeError(
                f'row {index}: expected (atom, atoms) tuple, got {type(row).__name__}')
        if len(row) != 2:
            raise ValueError(
                f'row {index}: expected 2 fields, got {len(row)}')
        atom, atoms = row
        _check_name(atom, index)
        _check_atoms(atoms, index)
        tally[atom] = tally.get(atom, 0) + atoms
    loose = sorted(atom for atom, count in tally.items() if count % BOND != 0)
    return {'total': len(rows), 'assembled': not loose,
            'pairs': {atom: count // BOND for atom, count in tally.items()},
            'loose': loose}
