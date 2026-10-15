"""Neural Dust - Tiny neural sensors (canonical1012).

PARTIAL abstractintegerenergybucket,notneural/biomedicalhardware. capacityexact
int1..16,initial exactint0..capacity,harvest exacttuple8 exactint0..8,leakexact
int0..4,packetexactint1..8. Eachslot:leakmin(charge,leak),addharvestcappedcapacity,
spilloverflow,transmitfloor(charge/packet)packets,retainremainder. Return8charge,
packetcount,spill,andlostcharge series. No realneural sensing/devicefeasibility.
Validatecapacity,initial,harvestouter/cells,leak,packet.Numericinputs.
"""
SCOPE='PARTIAL: caller eight-slot integer harvest-leak packet energy bucket'
NOT_CLAIMED=('neural sensing','biomedical device feasibility','measured energy')


def telemetry(capacity,initial,harvest,leak,packet):
    if type(capacity) is not int or not 1<=capacity<=16:raise ValueError('capacity exact int1..16')
    if type(initial) is not int or not 0<=initial<=capacity:raise ValueError('initial exact int0..capacity')
    if type(harvest) is not tuple or len(harvest)!=8:raise ValueError('harvest exact tuple8')
    for v in harvest:
        if type(v) is not int or not 0<=v<=8:raise ValueError('harvest exact int0..8')
    for name,v,lo,hi in (('leak',leak,0,4),('packet',packet,1,8)):
        if type(v) is not int or not lo<=v<=hi:raise ValueError(name+' exact int'+str(lo)+'..'+str(hi))
    charge=initial;residual=[];sent=[];spilled=[];lost=[]
    for h in harvest:
        loss=min(charge,leak);charge-=loss;raw=charge+h;spill=max(0,raw-capacity);charge=min(raw,capacity);n,charge=divmod(charge,packet);residual.append(charge);sent.append(n);spilled.append(spill);lost.append(loss)
    return {'charge':tuple(residual),'packets':tuple(sent),'spill':tuple(spilled),'leak_loss':tuple(lost),'sensor_validated':False}
