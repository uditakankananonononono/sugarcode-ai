"""Quantum Machine Learning - Combines quantum and ML.

PARTIAL: one-qubit variational classifier trained with parameter-shift
loss gradients using classical circuit expectations. No hardware, quantum
advantage or general-purpose machine learning platform.
"""
from math import cos, sin, pi, isfinite


def _real(x):
    if type(x) not in (int, float):
        raise ValueError('finite built-in real required')
    if type(x) is float and not isfinite(x):
        raise ValueError('finite built-in real required')
    if abs(x) > 1e6:
        raise ValueError('real magnitude must be <=1e6')
    if not isfinite(x):
        raise ValueError('finite built-in real required')


def _data(features, labels):
    if type(features) not in (list, tuple) or type(labels) not in (list, tuple) or not 1 <= len(features) <= 10000 or len(features) != len(labels):
        raise ValueError('equal nonempty feature/label sequences of at most 10000 required')
    for x in features: _real(x)
    for y in labels:
        if type(y) is not int or y not in (0, 1):
            raise ValueError('labels must be built-in integer 0 or 1')


def probability(feature, theta):
    """P(1), |feature| and |theta| <=1e6, for |0> -> Ry(feature) -> Ry(theta) -> Z measurement."""
    _real(feature); _real(theta)
    return (1-cos(feature+theta))/2


def loss_gradient(features, labels, theta):
    """Mean squared probability loss and double-precision chain-rule parameter-shift gradient."""
    _data(features, labels); _real(theta)
    loss = gradient = 0.0
    for x, y in zip(features, labels):
        p = probability(x, theta)
        # Internal parameter shifts may cross the public theta bound.
        derivative = ((1-cos(x+theta+pi/2))/2-(1-cos(x+theta-pi/2))/2)/2
        loss += (p-y)**2
        gradient += 2*(p-y)*derivative
    return loss/len(features), gradient/len(features)


def fit(features, labels, theta=0.0, learning_rate=0.1, steps=100):
    """Fixed-step gradient descent; history includes initial and final loss.

    No convergence guarantee. Training refuses with the real-magnitude ValueError
    after an update moves theta outside the supported domain; no silent clamp.
    Threshold ties at 0.5 are assigned class 1.
    """
    _data(features, labels); _real(theta); _real(learning_rate)
    if not 0 < learning_rate <= 1:
        raise ValueError('learning_rate must lie in (0,1]')
    if type(steps) is not int or not 0 <= steps <= 10000:
        raise ValueError('steps must be a built-in int in [0,10000]')
    history=[]
    for _ in range(steps):
        loss, gradient = loss_gradient(features, labels, theta)
        history.append(loss)
        theta -= learning_rate*gradient
    final, _ = loss_gradient(features, labels, theta)
    history.append(final)
    probabilities = tuple(probability(x, theta) for x in features)
    return {'theta': theta, 'loss_history': tuple(history), 'probabilities': probabilities,
            'predictions': tuple(int(p >= 0.5) for p in probabilities),
            'scope': 'classically simulated one-qubit variational classifier'}
