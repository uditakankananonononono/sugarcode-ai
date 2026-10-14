"""Heart Failure Management.

PARTIAL: caller-threshold weight and fluid ledger arithmetic, not heart-failure
management, diagnosis, risk assessment, treatment or emergency triage. No medical
thresholds inferred; thresholds/observations must be supplied by the caller.
"""
from fractions import Fraction
from math import isfinite
SCOPE='caller-threshold weight/fluid ledger only; no diagnosis treatment or triage'


def summarize(rows,reference_weight,weight_threshold,net_threshold):
    """Rows(day,weight_kg,intake_ml,output_ml),1..90 unique ordinal days.

    Day exactint0..100000;weight real[0,1000];intake/outputreal[0,100000]. Other
    scalars exactbuilt-in finite int/float:reference[0,1000],weightthreshold[0,1000],
    netthreshold[0,100000]. Fractions over str(value), inclusive flags weight-
    reference>=threshold and net>=threshold. Sortbyday only;no gaps filled or
    missingdata inferred. Outputdaily/cumulative net,weightdelta,flags,meanweight.
    Exactlist/tuple rowsmixtures accepted;no strings/names/medical advice.
    """
    def real(value,high):
        if type(value) not in (int,float) or not 0<=value<=high or not isfinite(value):
            raise ValueError('finite built-in nonnegative ledger real outside range')
        return Fraction(str(value))
    reference=real(reference_weight,1000);wt=real(weight_threshold,1000);nt=real(net_threshold,100000)
    if type(rows) not in (list,tuple) or not 1<=len(rows)<=90:raise ValueError('rows must contain1..90 ledger records')
    parsed=[];days=set()
    for row in rows:
        if type(row) not in (list,tuple) or len(row)!=4:raise ValueError('ledger row must be exactlist/tuple four values')
        day,weight,intake,output=row
        if type(day) is not int or not 0<=day<=100000:raise ValueError('day must be built-in int0..100000')
        if day in days:raise ValueError('days must be unique')
        days.add(day);parsed.append((day,real(weight,1000),real(intake,100000),real(output,100000)))
    daily=[];cumulative=Fraction(0)
    for day,weight,intake,output in sorted(parsed,key=lambda row:row[0]):
        net=intake-output;cumulative+=net;delta=weight-reference
        daily.append({'day':day,'weight':weight,'weight_delta':delta,'net_fluid':net,
                      'cumulative_net':cumulative,'weight_flag':delta>=wt,'net_flag':net>=nt})
    return {'daily':tuple(daily),'mean_weight':sum(row[1] for row in parsed)/len(parsed),
            'net_total':cumulative,'scope':SCOPE}
