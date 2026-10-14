"""Row 302 Music Composition: constrained finite melody synthesis.

Generates a lowest-motion melody from supplied allowed MIDI pitches at each
beat, honoring maximum adjacent leap and required final pitch. Dynamic
programming minimizes sum of absolute semitone motion, then pitch-tuple order.
Every beat has one quarter-note duration. This creates a melody sequence, not
merely a diagnostic of an existing tune.
NOT_CLAIMED: musical originality, aesthetic quality, harmony, audio rendering,
copyright clearance, arbitrary rhythms or autonomous publication.
"""


def compose_melody(pitch_options,final_pitch,max_leap=7):
    if type(pitch_options) not in (list,tuple):raise TypeError('pitch options must be a list or tuple')
    if not 1<=len(pitch_options)<=32:raise ValueError('beat count must be between 1 and 32')
    for options in pitch_options:
        if type(options) not in (list,tuple) or not 1<=len(options)<=8:
            raise ValueError('each beat must have between 1 and 8 pitches')
    if type(final_pitch) is not int or not 0<=final_pitch<=127:
        raise ValueError('final_pitch must be a nonbool MIDI integer between zero and 127')
    if type(max_leap) is not int or not 0<=max_leap<=127:
        raise ValueError('max_leap must be a nonbool integer between zero and 127')
    for options in pitch_options:
        if any(type(p) is not int or not 0<=p<=127 for p in options):
            raise ValueError('pitches must be nonbool MIDI integers between zero and 127')
        if len(set(options))!=len(options):raise ValueError('pitch options must be unique')
    states={p:(0,(p,)) for p in pitch_options[0]}
    for options in pitch_options[1:]:
        nxt={}
        for pitch in options:
            choices=[(cost+abs(pitch-prior),path+(pitch,)) for prior,(cost,path) in states.items()
                     if abs(pitch-prior)<=max_leap]
            if choices:nxt[pitch]=min(choices)
        states=nxt
    if final_pitch not in states:raise ValueError('no melody satisfies final pitch and leap cap')
    cost,path=states[final_pitch]
    return {'pitches':list(path),'quarter_note_durations':[1]*len(path),
            'total_semitone_motion':cost,'originality_validated':False}
