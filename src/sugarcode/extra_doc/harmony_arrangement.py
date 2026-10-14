"""Row 303 Harmony Arrangement: exact finite chord voicing arrangement.

Selects one supplied MIDI pitch per voice, in strictly ascending voice order,
minimizing supplied pairwise pitch-class dissonance costs. Equal-cost chords
use lexicographic pitch order. Enumerates at most 4096 candidate voicings.
NOT_CLAIMED: perceptual pleasingness, aesthetic harmony, cultural universality,
voice-leading over time, audio rendering or autonomous publication.
"""
from itertools import product


def arrange_harmony(pitch_options,interval_costs):
    if type(pitch_options) not in (list,tuple) or type(interval_costs) not in (list,tuple):
        raise TypeError('inputs must be lists or tuples')
    if not 1<=len(pitch_options)<=6:raise ValueError('voice count must be between 1 and 6')
    for options in pitch_options:
        if type(options) not in (list,tuple) or not 1<=len(options)<=4:
            raise ValueError('each voice must have between 1 and 4 pitches')
    if len(interval_costs)!=12:raise ValueError('interval costs must have twelve entries')
    if any(type(v) is not int or not 0<=v<=1000000 for v in interval_costs):
        raise ValueError('interval costs must be nonbool integers between zero and 1000000')
    for options in pitch_options:
        if any(type(p) is not int or not 0<=p<=127 for p in options):
            raise ValueError('pitches must be nonbool MIDI integers between zero and 127')
        if len(set(options))!=len(options):raise ValueError('pitch options must be unique')
    best=None;feasible=0;candidates=0
    for chord in product(*pitch_options):
        candidates+=1
        if any(a>=b for a,b in zip(chord,chord[1:])):continue
        feasible+=1
        cost=sum(interval_costs[(chord[j]-chord[i])%12] for i in range(len(chord)) for j in range(i+1,len(chord)))
        candidate=(cost,chord)
        if best is None or candidate<best:best=candidate
    if best is None:raise ValueError('no strictly ascending voicing exists')
    cost,chord=best
    return {'pitches':list(chord),'dissonance_cost':cost,'candidate_count':candidates,
            'feasible_count':feasible,'pleasingness_validated':False}
