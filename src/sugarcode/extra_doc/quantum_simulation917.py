"""Quantum Simulation - Models quantum systems.

PARTIAL: double-precision exact-form propagator for the single-qubit Hamiltonian
H=hx*X+hy*Y+hz*Z (hbar=1). Not a many-body simulator or quantum hardware.
"""
from math import cos, sin, sqrt, isfinite


def evolve(state, field, time):
    """Return exp(-i H time)|state>, Bloch vector, norm and energy.

    Built-in finite numbers only, normalized two-amplitude list/tuple; three real
    field components. Unit-norm tolerance 1e-12. Reject overflowing field/time
    scales rather than return NaNs. No open-system or noise dynamics.
    """
    if type(state) not in (list, tuple) or len(state) != 2:
        raise ValueError('state must have two amplitudes')
    for value in state:
        if type(value) not in (int, float, complex) or not isfinite(value.real) or not isfinite(value.imag):
            raise ValueError('finite built-in amplitudes required')
    if abs(sum(abs(x)**2 for x in state)-1)>1e-12:
        raise ValueError('state must have unit norm')
    if type(field) not in (list, tuple) or len(field)!=3:
        raise ValueError('field must have three components')
    for x in (*field,time):
        if type(x) not in (int,float) or not isfinite(x) or abs(x)>1e100:
            raise ValueError('finite built-in real with magnitude <=1e100 required')
    hx,hy,hz=field
    radius=sqrt(hx*hx+hy*hy+hz*hz)
    if radius==0:
        out=tuple(complex(x) for x in state)
    else:
        a,b=state
        scale=sin(radius*time)/radius
        out=(cos(radius*time)*a-1j*scale*(hz*a+(hx-1j*hy)*b),
             cos(radius*time)*b-1j*scale*((hx+1j*hy)*a-hz*b))
    a,b=out
    bloch=(2*(a.conjugate()*b).real,2*(a.conjugate()*b).imag,abs(a)**2-abs(b)**2)
    return {'state':out,'bloch':bloch,'norm':sum(abs(x)**2 for x in out),
            'energy':sum(x*y for x,y in zip(field,bloch)),
            'scope':'closed single-qubit Pauli Hamiltonian; double precision'}
