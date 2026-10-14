"""Coding Theory.

PARTIAL: caller binary codebook Hamming distances only, not coding-theory
coverage, encoder/decoder, channel reliability or error-correction execution.
Codewords are caller declarations with no channel or protocol assumptions.
"""
SCOPE='caller binary codebook distances only; no encoding decoding or channel reliability'


def distances(words):
    """Exactlist/tuple2..32 unique exactstr binary words length1..64 with equal
    width. No text/container subclasses. Return lexical sorted word pairs and
    integer Hamming distance,minimum distance,and formal disjoint-ball radius
    floor((minimum-1)/2). Radius is codebook combinatorics,not a decoder/safety
    guarantee or measured correction performance. Case/alphabet not normalized.
    """
    if type(words) not in (list,tuple) or not 2<=len(words)<=32:raise ValueError('words must be exactlist/tuple length2..32')
    for word in words:
        if type(word) is not str or not 1<=len(word)<=64 or any(bit not in '01' for bit in word):raise ValueError('word must be exactstr binary length1..64')
    if len(set(words))!=len(words):raise ValueError('words must be unique')
    width=len(words[0])
    if any(len(word)!=width for word in words):raise ValueError('words must have equal width')
    ordered=sorted(words);pairs=[]
    for i,left in enumerate(ordered):
        for right in ordered[i+1:]:pairs.append((left,right,sum(a!=b for a,b in zip(left,right))))
    minimum=min(row[2] for row in pairs)
    return {'pairs':tuple(pairs),'minimum_distance':minimum,'disjoint_ball_radius':(minimum-1)//2,'scope':SCOPE}
