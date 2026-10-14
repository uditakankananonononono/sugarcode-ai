"""Row 312 Radio Drama: timed audio-only spoken/effect cue composition.

Composes supplied signed-16-bit cue samples at explicit sample offsets,
retains speaker/effect labels, sums overlaps exactly and reports clipping
locations without silently clipping. Output is an integer mono timeline.
NOT_CLAIMED: story invention, voice acting, aesthetic drama quality, actual
playback, loudness mastering or autonomous publication.
"""


def compose_radio_drama(cues):
    if type(cues) not in (list,tuple):raise TypeError('cues must be a list or tuple')
    if not 1<=len(cues)<=32:raise ValueError('cue count must be between 1 and 32')
    for cue in cues:
        if type(cue) not in (list,tuple) or len(cue)!=3:
            raise ValueError('cues must contain label offset and samples')
    for label,offset,samples in cues:
        if type(offset) is not int or not 0<=offset<=16383:
            raise ValueError('offsets must be nonbool integers zero through 16383')
        if type(samples) not in (list,tuple) or not 1<=len(samples)<=4096:
            raise ValueError('cue samples must have between 1 and 4096 entries')
    length=max(offset+len(samples) for label,offset,samples in cues)
    if length>16384:raise ValueError('drama timeline must not exceed 16384 samples')
    for label,offset,samples in cues:
        if type(label) is not str:raise TypeError('cue labels must be strings')
        if not 1<=len(label)<=80:raise ValueError('cue label length must be between 1 and 80')
        if not label.strip():raise ValueError('cue labels must not be blank')
    if any(type(v) is not int or not -32768<=v<=32767 for label,offset,samples in cues for v in samples):
        raise ValueError('samples must be nonbool signed 16-bit integers')
    output=[0]*length;timeline=[]
    for label,offset,samples in cues:
        for i,value in enumerate(samples):output[offset+i]+=value
        timeline.append({'label':label,'start_sample':offset,'end_sample':offset+len(samples)})
    return {'samples':output,'timeline':timeline,'overload_indices':[i for i,v in enumerate(output) if not -32768<=v<=32767],
            'sample_count':length,'story_quality_validated':False}
