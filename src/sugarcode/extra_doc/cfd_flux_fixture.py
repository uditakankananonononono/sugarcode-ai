"""Row 1523, Computational Fluid Dynamics.

cfd_flux_fixture subtracts supplied outflow y from inflow x and adds fixed
source count per row. Returns sorted residuals, balanced zero labels,
absolute_total without cross-row cancellation and net signed sum. These
are abstract count balances, not a CFD solver, fluid simulation, mesh,
Navier-Stokes solution, physical units or engineering safety claim.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
source defaults to 2, an exact int from 0 to 5.
Validation order: rows type, rows size, source, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: CFD solver, physical units, fluid simulation, engineering safety, production readiness.
"""

SCOPE = 'PARTIAL: supplied count flux residual bookkeeping, no CFD solver'
NOT_CLAIMED = ('CFD solver', 'physical units', 'fluid simulation', 'engineering safety', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def cfd_flux_fixture(rows, source=2):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(source) is not int or not 0 <= source <= 5:
        raise ValueError('source must be a nonbool integer between 0 and 5')
    clean = []
    for row in rows:
        if type(row) not in (list, tuple) or len(row) != 3:
            raise ValueError('each row must be a (label, x, y) triple')
        label, x, y = row
        if not _label(label):
            raise ValueError('label must be a printable ASCII string of 1 to 12 characters')
        if type(x) is not int or not 0 <= x <= 10:
            raise ValueError('x must be a nonbool integer between 0 and 10')
        if type(y) is not int or not 0 <= y <= 10:
            raise ValueError('y must be a nonbool integer between 0 and 10')
        clean.append((label, x, y))
    if len({r[0] for r in clean}) != len(clean):
        raise ValueError('labels must be distinct')
    values=sorted((n,x-y+source) for n,x,y in clean)
    return {'residuals':values,'balanced':[n for n,v in values if v==0],
            'absolute_total':sum(abs(v) for n,v in values),'net':sum(v for n,v in values)}
