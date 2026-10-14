"""Doc row1744 Conversation Analysis: PARTIAL supplied speaker sequence audit.

Turns exact list2..100 tuples(speaker,duration); speaker exact nonblank str1..80,
 duration exact int1..1000. Count ordered adjacent transitions, same-speaker
continuations, switches and duration totals. No overlap, intent or speech inference.
"""


def audit_turns(turns):
    if type(turns) is not list or not 2<=len(turns)<=100:
        raise ValueError('turns must be an exact list with 2..100 entries')
    for row in turns:
        if type(row) is not tuple or len(row)!=2:raise ValueError('turn must be a speaker duration tuple')
        speaker,duration=row
        if type(speaker) is not str or not 1<=len(speaker)<=80 or not speaker.strip():
            raise ValueError('speaker must be a nonblank exact string of 1..80 characters')
        if type(duration) is not int or not 1<=duration<=1000:raise ValueError('duration must be an integer in 1..1000')
    edges={};duration_totals={};same=0
    for s,d in turns:duration_totals[s]=duration_totals.get(s,0)+d
    for (a,_),(b,__) in zip(turns,turns[1:]):
        edges[(a,b)]=edges.get((a,b),0)+1
        same+=a==b
    return {'edges':[(a,b,n) for (a,b),n in sorted(edges.items())],'durations':sorted(duration_totals.items()),'continuations':same,'switches':len(turns)-1-same,'claim':'PARTIAL','conversation_validated':False}
