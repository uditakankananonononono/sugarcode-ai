"""Bounded codepoint-length counts only, no normalization or quality inference."""
from collections import Counter
from dataclasses import dataclass

@dataclass(frozen=True)
class LengthHistogram:
    counts: tuple[tuple[int,int], ...]
    total: int

def length_histogram(items, *, max_entries=10000, max_codepoints=10000):
    for cap in (max_entries,max_codepoints):
        if type(cap) is not int or cap<=0:raise ValueError('positive exact integer caps required')
    if type(items) is not list:raise TypeError('exact list required')
    if len(items)>max_entries:raise ValueError('entry cap exceeded')
    counts=Counter()
    for item in items:
        if type(item) is not str:raise TypeError('exact strings required')
        if len(item)>max_codepoints:raise ValueError('codepoint cap exceeded')
        counts[len(item)]+=1
    return LengthHistogram(tuple(sorted(counts.items())),len(items))
