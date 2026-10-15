"""Focused Ultrasound - Non-invasive brain treatment (canonical1011).

PARTIAL abstractintegerphasorarithmeticonly,notacoustic/clinicalmodel.
channels exacttuple4 exact(amplitude,phase)tuple2; amplitudeexactint0..8,
phaseexactint0..3 quarterturns. Sumphasors0=(1,0),1=(0,1),2=(-1,0),3=(0,-1).
Returnintegerreal/imaginary/squaredmagnitude/cancelledbool;no wavepropagation,
brain/treatment/safetyclaims. Validateouter,eachshape/amplitude/phaseinorder.
"""
SCOPE='PARTIAL: caller four-channel integer quarter-turn phasor sum only'
NOT_CLAIMED=('acoustic propagation','brain treatment','clinical safety')


def combine(channels):
    if type(channels) is not tuple or len(channels)!=4:raise ValueError('channels exact tuple4')
    for row in channels:
        if type(row) is not tuple or len(row)!=2:raise ValueError('channel exact tuple2')
        a,p=row
        if type(a) is not int or not 0<=a<=8:raise ValueError('amplitude exact int0..8')
        if type(p) is not int or not 0<=p<=3:raise ValueError('phase exact int0..3')
    direction=((1,0),(0,1),(-1,0),(0,-1));real=sum(a*direction[p][0] for a,p in channels);imag=sum(a*direction[p][1] for a,p in channels)
    return {'real':real,'imaginary':imag,'squared_magnitude':real*real+imag*imag,'cancelled':real==0 and imag==0,'treatment_validated':False}
