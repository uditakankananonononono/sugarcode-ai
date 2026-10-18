"""Exact bounded Latin-square tests and transformations.

SCOPE: caller-supplied n-by-n tables, 1<=n<=4, symbols 0..n-1.
NOT_CLAIMED: design search at scale, randomness, retrieval, integration.
"""
from itertools import permutations

CLAIMS=False
SCOPE="bounded exact symbol-table and Latin-square arithmetic"
NOT_CLAIMED="design search at scale, randomness, retrieval, product integration"
MAX_ORDER=4


def _square(table):
    if type(table) not in (list, tuple):raise TypeError("table must be a list or tuple")
    n=len(table)
    if not 1<=n<=MAX_ORDER:raise ValueError("order out of range")
    for row in table:
        if type(row) not in (list, tuple):raise TypeError("row must be a list or tuple")
        if len(row)!=n:raise ValueError("table must be square")
    for row in table:
        for x in row:
            if type(x) is not int:raise TypeError("symbol must be an integer")
            if x<0 or x>=n:raise ValueError("symbol out of range")
    return tuple(tuple(row) for row in table)


def _pair(a,b):
    a=_square(a);b=_square(b)
    if len(a)!=len(b):raise ValueError("orders must agree")
    return a,b


def row_collision_count(table):
    a=_square(table);n=len(a)
    return sum(row[i]==row[j] for row in a for i in range(n) for j in range(i+1,n))


def column_collision_count(table):
    a=_square(table);n=len(a)
    return sum(a[i][c]==a[j][c] for c in range(n) for i in range(n) for j in range(i+1,n))


def is_latin(table):
    a=_square(table);n=len(a)
    return all(len(set(row))==n for row in a) and all(len({a[r][c] for r in range(n)})==n for c in range(n))


def orthogonal_pair_count(left,right):
    """Number of distinct ordered symbol pairs, whether or not inputs are Latin."""
    a,b=_pair(left,right);n=len(a)
    return len({(a[r][c],b[r][c]) for r in range(n) for c in range(n)})


def is_orthogonal(left,right):
    a,b=_pair(left,right)
    return is_latin(a) and is_latin(b) and orthogonal_pair_count(a,b)==len(a)**2


def transpose_square(table):
    a=_square(table)
    return tuple(zip(*a))


def reduce_latin_square(table):
    """Relabel using first row, then sort rows by first symbol; no isotopy claim."""
    a=_square(table)
    if not is_latin(a):raise ValueError("table must be Latin")
    relabel={x:i for i,x in enumerate(a[0])}
    rows=[tuple(relabel[x] for x in row) for row in a]
    return tuple(sorted(rows,key=lambda row:row[0]))


def transversal_count(table):
    """Count one-per-row/column selections using every symbol exactly once."""
    a=_square(table);n=len(a)
    return sum(len({a[r][c] for r,c in enumerate(order)})==n for order in permutations(range(n)))


def diagonal_sum(table):
    a=_square(table)
    return sum(row[i] for i,row in enumerate(a))


def symbol_histogram(table):
    a=_square(table);n=len(a)
    return tuple(sum(x==symbol for row in a for x in row) for symbol in range(n))
