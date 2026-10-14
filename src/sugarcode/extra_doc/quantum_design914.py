"""Quantum Algorithm Design - Creates quantum solutions.

PARTIAL: constructive Bernstein-Vazirani circuit synthesis and exact simulation
for a supplied binary hidden string. Not an automatic general algorithm inventor
and not quantum hardware execution. Qubit zero is the least significant bit;
the last qubit is the phase-kickback ancilla.
"""
from math import sqrt


def bernstein_vazirani(secret):
    """Synthesize H/X/CNOT gates, execute them and return data-bit probabilities.

    Input is a nonempty binary string of at most 11 bits, most-significant bit
    first. The oracle consists of one CNOT per set bit, all sharing an ancilla.
    Oracle calls are one regardless of the decomposition's CNOT count.
    """
    if type(secret) is not str or not 1 <= len(secret) <= 11 or set(secret) - {'0', '1'}:
        raise ValueError('secret must be a binary string of length 1..11')
    bits = len(secret)
    ancilla = bits
    gates = [('X', ancilla)]
    gates += [('H', q) for q in range(bits + 1)]
    gates += [('CX', q, ancilla) for q, bit in enumerate(reversed(secret)) if bit == '1']
    gates += [('H', q) for q in range(bits)]
    state = [0.0] * (1 << (bits + 1))
    state[0] = 1.0
    for gate in gates:
        name, q, *tail = gate
        mask = 1 << q
        if name == 'H':
            for i in range(len(state)):
                if i & mask == 0:
                    a, b = state[i], state[i | mask]
                    state[i] = (a + b) / sqrt(2)
                    state[i | mask] = (a - b) / sqrt(2)
        elif name == 'X':
            for i in range(len(state)):
                if i & mask == 0:
                    state[i], state[i | mask] = state[i | mask], state[i]
        else:
            target = 1 << tail[0]
            for i in range(len(state)):
                if i & mask and i & target == 0:
                    state[i], state[i | target] = state[i | target], state[i]
    probabilities = tuple(state[i] ** 2 + state[i | (1 << bits)] ** 2 for i in range(1 << bits))
    return {'gates': tuple(gates), 'state': tuple(state), 'probabilities': probabilities,
            'decoded': format(max(range(len(probabilities)), key=probabilities.__getitem__), '0' + str(bits) + 'b'),
            'oracle_calls': 1, 'cnot_count': secret.count('1'),
            'scope': 'classical Bernstein-Vazirani circuit synthesis and simulation'}
