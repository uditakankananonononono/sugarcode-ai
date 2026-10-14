"""Row 263 Dialogue Writing: shortest alternating finite dialogue generation.

Searches supplied speech rules (speaker,utterance,required fact,result fact)
for the shortest two-speaker alternating exchange reaching a target fact.
Utterances are supplied, but their coherent ordering and selected exchange
are generated rather than a text diagnostic. Facts persist monotonically.
NOT_CLAIMED: novel utterance invention, naturalness or literary quality,
pragmatic realism, arbitrary-length conversation, autonomous communication.
"""
from collections import deque


def _label(v):
    if type(v) is not str:raise TypeError('labels must be strings')
    if not 1<=len(v)<=160:raise ValueError('label length must be between 1 and 160')
    if not v.strip():raise ValueError('labels must not be blank')
    return v


def generate_dialogue(speakers,rules,initial_facts,target,max_turns=8):
    if any(type(v) not in (list,tuple) for v in (speakers,rules,initial_facts)):
        raise TypeError('speakers rules and facts must be lists or tuples')
    if len(speakers)!=2:raise ValueError('exactly two speakers required')
    if not 1<=len(rules)<=32:raise ValueError('rule count must be between 1 and 32')
    if len(initial_facts)>32:raise ValueError('initial fact count must not exceed 32')
    if type(max_turns) is not int or not 0<=max_turns<=8:
        raise ValueError('max_turns must be a nonbool integer between 0 and 8')
    if any(type(r) not in (list,tuple) or len(r)!=4 for r in rules):
        raise ValueError('speech rules must have four fields')
    names=[_label(v) for v in speakers]
    if names[0]==names[1]:raise ValueError('speakers must be distinct')
    rs=[tuple(_label(v) for v in r) for r in rules]
    facts=frozenset(_label(v) for v in initial_facts);goal=_label(target)
    if any(r[0] not in names for r in rs):raise ValueError('rule speaker must be known')
    queue=deque([(facts,0,[])]);seen={(facts,0)};expanded=0
    while queue:
        state,turn,path=queue.popleft()
        if goal in state:
            return {'turns':path,'final_facts':sorted(state),'turn_count':len(path),'naturalness_claimed':False}
        if len(path)==max_turns:continue
        expanded+=1
        if expanded>4096:raise ValueError('dialogue search exceeds 4096 expanded states')
        for speaker,utterance,required,result in rs:
            if speaker!=names[turn] or required not in state:continue
            next_state=state|{result};next_turn=1-turn
            key=(next_state,next_turn)
            if key in seen:continue
            seen.add(key)
            queue.append((next_state,next_turn,path+[{'speaker':speaker,'utterance':utterance,'required':required,'result':result}]))
    raise ValueError('no alternating dialogue reaches target within turn cap')
