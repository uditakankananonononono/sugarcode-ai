"""Row 1583: Signal Processing.

PARTIAL: computes the full discrete convolution of supplied integer
signal and kernel sequences, with implicit zero outside each sequence.
No sampling assumptions, spectral interpretation or filter design.
Caps of 1-30 signal samples, 1-8 kernel coefficients and values -1000
to 1000 are this module's own choices, not a domain standard.
"""
MAX_SIGNAL = 30
MAX_KERNEL = 8
LIMIT = 1000
NOT_CLAIMED = ('sampling_assumptions', 'spectral_interpretation', 'filter_design')


def convolve(signal, kernel):
    for name,sequence,cap in (('signal',signal,MAX_SIGNAL),('kernel',kernel,MAX_KERNEL)):
        if type(sequence) is not tuple or not 1 <= len(sequence) <= cap:
            raise ValueError(f'{name}: tuple of 1 to {cap} entries required')
        for i,value in enumerate(sequence):
            if type(value) is not int or not -LIMIT <= value <= LIMIT:
                raise ValueError(f'{name}[{i}]: whole number -1000 to 1000 required')
    result = []
    for position in range(len(signal) + len(kernel) - 1):
        total = 0
        for i in range(len(signal)):
            j = position - i
            if 0 <= j < len(kernel):
                total += signal[i] * kernel[j]
        result.append(total)
    return {'finite_convolution_validated': False, 'not_claimed': NOT_CLAIMED,
            'samples': tuple(result), 'output_length': len(result)}
