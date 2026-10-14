"""Row 304 Rhythm Programming: bounded evenly distributed pulse sequencing.

Generates steps with floor-difference Euclidean pulse placement, then rotates
by a supplied offset. Pulse count is exact; cyclic inter-hit gaps differ by
at most one. Explicit velocity accents distinguish first pulse from others.
NOT_CLAIMED: human groove feel, swing, audio playback, stylistic authenticity,
artistic quality or autonomous publication.
"""


def program_rhythm(steps,pulses,rotation=0,velocity=96,accent=127):
    if type(steps) is not int or not 1<=steps<=128:
        raise ValueError('steps must be a nonbool integer between 1 and 128')
    if type(pulses) is not int or not 0<=pulses<=steps:
        raise ValueError('pulses must be a nonbool integer between zero and steps')
    if type(rotation) is not int or not 0<=rotation<steps:
        raise ValueError('rotation must be a nonbool integer inside step range')
    for value in (velocity,accent):
        if type(value) is not int or not 1<=value<=127:
            raise ValueError('velocities must be nonbool integers between 1 and 127')
    base=[(i+1)*pulses//steps-i*pulses//steps for i in range(steps)]
    pattern=base[-rotation:]+base[:-rotation] if rotation else base[:]
    hits=[i for i,v in enumerate(pattern) if v]
    velocities=[0]*steps
    for index,step in enumerate(hits):velocities[step]=accent if index==0 else velocity
    gaps=[(hits[(i+1)%len(hits)]-step)%steps or steps for i,step in enumerate(hits)]
    return {'pattern':pattern,'velocities':velocities,'hit_steps':hits,'cyclic_gaps':gaps,'groove_validated':False}
