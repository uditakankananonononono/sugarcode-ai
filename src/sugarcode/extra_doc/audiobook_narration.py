"""Row 311 Audiobook Narration: spoken-segment assembly and text cue alignment.

Assembles supplied mono signed-16-bit spoken segments, inserts requested
inter-segment silence, and maps each supplied text cue to its sample interval.
Creates a narration audio timeline, not merely a textual reading plan.
Caps: 32 segments, 4096 samples per segment, 16384 total samples, 1024 pause.
NOT_CLAIMED: speech synthesis, voice quality, engaging performance, semantic
text/audio verification, loudness mastering or autonomous publication.
"""


def assemble_narration(texts,segments,pause_samples=0):
    if type(texts) not in (list,tuple) or type(segments) not in (list,tuple):
        raise TypeError('texts and segments must be lists or tuples')
    if not 1<=len(texts)<=32:raise ValueError('segment count must be between 1 and 32')
    if len(segments)!=len(texts):raise ValueError('text and audio segment counts must match')
    if type(pause_samples) is not int or not 0<=pause_samples<=1024:
        raise ValueError('pause_samples must be a nonbool integer between zero and 1024')
    for text in texts:
        if type(text) is not str:raise TypeError('text cues must be strings')
        if not 1<=len(text)<=256:raise ValueError('text cue length must be between 1 and 256')
    for segment in segments:
        if type(segment) not in (list,tuple) or not 1<=len(segment)<=4096:
            raise ValueError('audio segments must have between 1 and 4096 samples')
    total=sum(len(s) for s in segments)+pause_samples*(len(segments)-1)
    if total>16384:raise ValueError('narration must not exceed 16384 samples')
    if any(not text.strip() for text in texts):raise ValueError('text cues must not be blank')
    if any(type(v) is not int or not -32768<=v<=32767 for segment in segments for v in segment):
        raise ValueError('samples must be nonbool signed 16-bit integers')
    audio=[];cues=[]
    for i,(text,segment) in enumerate(zip(texts,segments)):
        start=len(audio);audio.extend(segment)
        cues.append({'text':text,'start_sample':start,'end_sample':len(audio)})
        if i<len(segments)-1:audio.extend([0]*pause_samples)
    return {'samples':audio,'cues':cues,'sample_count':total,'performance_validated':False}
