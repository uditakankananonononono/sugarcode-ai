"""Quantum Error Correction - Handles decoherence.

PARTIAL: double-precision three-qubit repetition-code correction of bit flips, including
coherent superpositions through density-matrix recovery. No correction of phase
errors, arbitrary decoherence, fault-tolerant gates or physical hardware.
"""
from math import isfinite


def recover_bit_flip(alpha, beta, probabilities):
    """Encode alpha|0>+beta|1>, apply independent flips, measure syndromes/recover.

    Accept finite built-in int/float/complex amplitudes with unit squared norm
    within 1e-12. Three built-in real probabilities lie in [0,1]. Return the
    decoded logical density matrix, four syndrome probabilities, logical flip
    probability and fidelity to the supplied pure state. Failure is >=2 flips.
    """
    for a in (alpha, beta):
        if type(a) not in (int, float, complex):
            raise ValueError('amplitudes must be finite built-in numbers')
        if abs(a.real) > 1 or abs(a.imag) > 1:
            raise ValueError('amplitudes must have unit norm')
        if not isfinite(a.real) or not isfinite(a.imag):
            raise ValueError('amplitudes must be finite built-in numbers')
    if abs(abs(alpha)**2 + abs(beta)**2 - 1) > 1e-12:
        raise ValueError('amplitudes must have unit norm')
    if type(probabilities) not in (tuple, list) or len(probabilities) != 3:
        raise ValueError('three flip probabilities required')
    for p in probabilities:
        if type(p) not in (int, float) or not 0 <= p <= 1 or not isfinite(p):
            raise ValueError('probabilities must be finite built-in reals in [0,1]')
    syndromes = [0.0]*4
    failure = 0.0
    for mask in range(8):
        bits = [(mask >> i) & 1 for i in range(3)]
        weight = 1.0
        for bit, p in zip(bits, probabilities):
            weight *= p if bit else 1-p
        syndrome = (bits[0] ^ bits[1]) + 2*(bits[1] ^ bits[2])
        syndromes[syndrome] += weight
        if sum(bits) >= 2:
            failure += weight
    a, b = complex(alpha), complex(beta)
    rho = (( (1-failure)*abs(a)**2 + failure*abs(b)**2,
             (1-failure)*a*b.conjugate() + failure*b*a.conjugate()),
           ( (1-failure)*b*a.conjugate() + failure*a*b.conjugate(),
             (1-failure)*abs(b)**2 + failure*abs(a)**2 ))
    overlap = abs(a.conjugate()*b + b.conjugate()*a)**2
    fidelity = 1-failure + failure*overlap
    return {'density_matrix': rho, 'syndrome_probabilities': tuple(syndromes),
            'logical_flip_probability': failure, 'fidelity': fidelity,
            'scope': 'three-qubit bit-flip channel only; no phase correction'}
