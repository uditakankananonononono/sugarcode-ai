"""5G/6G.

PARTIAL: caller rectangular resource-grid occupancy only, not5G/6G protocol,
radio simulation, throughput, interference or standards compliance. Abstract
slot/subcarrier coordinates and reservations are caller declarations.
"""
from fractions import Fraction
SCOPE='caller abstract resource-grid occupancy only; no 5G/6G radio or protocol claims'


def occupancy(rows,slots,carriers):
    """Rows exactlist/tuple0..64 rectangles(slotstart,slotend,carrierstart,
    carrierend),exactint half-open endpoints within slots/carriers exactint1..32.
    Strictly positive rectangle dimensions. Overlaps/duplicates allowed;count
    union occupied cells once,return row-major tuple cells,free count,exact
    occupied fraction. Mixedrows accepted. No users,PHY,modulation or allocation.
    """
    if type(slots) is not int or type(carriers) is not int or not 1<=slots<=32 or not 1<=carriers<=32:raise ValueError('grid dimensions must be exactint1..32')
    if type(rows) not in (list,tuple) or len(rows)>64:raise ValueError('rows must be exactlist/tuple atmost64')
    cells=set()
    for row in rows:
        if type(row) not in (list,tuple) or len(row)!=4:raise ValueError('row must be exactlist/tuple four values')
        a,b,c,d=row
        if any(type(x) is not int for x in row) or not 0<=a<b<=slots or not 0<=c<d<=carriers:raise ValueError('rectangle endpoints must be exactint positive spans inside grid')
        cells.update((slot,carrier) for slot in range(a,b) for carrier in range(c,d))
    total=slots*carriers
    return {'occupied':tuple(sorted(cells)),'free_count':total-len(cells),'occupied_fraction':Fraction(len(cells),total),'scope':SCOPE}
