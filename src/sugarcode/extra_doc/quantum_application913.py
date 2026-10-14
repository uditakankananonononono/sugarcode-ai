"""Quantum Computing Application - Solves problems exponentially faster.

PARTIAL: double-precision classical simulation of Grover amplitude amplification, not a
physical quantum processor or evidence of exponential speedup. Grover gives a
quadratic oracle-query advantage in the ideal black-box model, not exponential.
Amplitudes use little-endian basis indices and double precision. At most 12
qubits; classical memory and runtime grow exponentially.
"""
from math import asin, floor, pi, sin, sqrt


def _integer(value, name, low, high):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(name + ' must be a built-in int in range')


def grover_search(qubits, marked, iterations=None):
    """Return the full state, marked success probability and oracle-query count.

    Marked indices must be unique built-in integers. Empty and full marked sets
    are accepted; their default iteration count is zero. Otherwise the default
    maximizes the first success peak using round(pi/(4 theta)-1/2), with half
    ties rounded upward. An explicit count permits observing over-rotation.
    """
    _integer(qubits, 'qubits', 1, 12)
    size = 1 << qubits
    if type(marked) not in (list, tuple):
        raise ValueError('marked must be a list or tuple')
    for index in marked:
        _integer(index, 'marked index', 0, size - 1)
    if len(set(marked)) != len(marked):
        raise ValueError('marked indices must be unique')
    count = len(marked)
    theta = asin(sqrt(count / size))
    if iterations is None:
        iterations = 0 if count in (0, size) else max(0, floor(pi / (4 * theta)))
    _integer(iterations, 'iterations', 0, 10000)
    state = [1 / sqrt(size)] * size
    for _ in range(iterations):
        for index in marked:
            state[index] = -state[index]
        mean = sum(state) / size
        state = [2 * mean - amplitude for amplitude in state]
    success = sum(state[index] ** 2 for index in marked)
    predicted = sin((2 * iterations + 1) * theta) ** 2 if count else 0.0
    return {'state': tuple(state), 'success_probability': success,
            'predicted_probability': predicted, 'oracle_queries': iterations,
            'norm': sum(x * x for x in state), 'marked_count': count,
            'scope': 'classical statevector simulation; quadratic ideal oracle-query advantage only'}
