"""Optical Computing - Light-based processing.

PARTIAL: double-precision coherent-mode Fourier optical processor simulation,
not physical optics, a fabricated photonic accelerator or nonlinear computing.
"""
from cmath import exp
from math import pi,isfinite

SCOPE='coherent discrete Fourier mode processing; double precision; no hardware'


def fourier_process(amplitudes,phases):
    """Apply unitary DFT, phase mask, inverse DFT to coherent complex modes.

    1..32 input amplitudes/phases, equal lengths, exact list/tuple only. Built-in
    finite complex/int/float amplitudes with each real/imag magnitude<=10, real
    phase magnitudes<=1e6 radians. Output amplitudes/intensities, Fourier-plane
    intensities and input/output power. Coherent interference, no shot noise,
    real-space diffraction, polarization, wavelength or propagation-loss model.
    DFT convention exp(-2pi*i*k*j/N)/sqrt(N), inverse with positive exponent.
    """
    if type(amplitudes) not in (list,tuple) or type(phases) not in (list,tuple) or not 1<=len(amplitudes)<=32 or len(phases)!=len(amplitudes):
        raise ValueError('equal mode/phase sequences of length 1..32 required')
    for x in amplitudes:
        if type(x) not in (int,float,complex) or abs(x.real)>10 or abs(x.imag)>10 or not isfinite(x.real) or not isfinite(x.imag):
            raise ValueError('finite built-in complex components with magnitude <=10 required')
    for x in phases:
        if type(x) not in (int,float) or abs(x)>1e6 or not isfinite(x):
            raise ValueError('finite built-in real phase magnitude <=1e6 required')
    n=len(amplitudes)
    frequency=tuple(sum(amplitudes[j]*exp(-2j*pi*k*j/n) for j in range(n))/n**.5 for k in range(n))
    masked=tuple(x*exp(1j*p) for x,p in zip(frequency,phases))
    output=tuple(sum(masked[k]*exp(2j*pi*k*j/n) for k in range(n))/n**.5 for j in range(n))
    return {'amplitudes':output,'intensities':tuple(abs(x)**2 for x in output),
            'fourier_intensities':tuple(abs(x)**2 for x in frequency),
            'input_power':sum(abs(x)**2 for x in amplitudes),
            'output_power':sum(abs(x)**2 for x in output),'scope':SCOPE}
