"""Row 317 Infographic Design: bounded SVG fact-card composition.

Combines a supplied title and labeled integer facts into equal-sized visual
cards with relative-magnitude bars and escaped text. Returns explicit card
geometry and one SVG infographic, not a textual layout recommendation.
NOT_CLAIMED: factual verification, artistic originality, universal readability,
long prose layout, accessibility certification or publication.
"""
from html import escape
from fractions import Fraction


def _text(v,limit):
    if type(v) is not str:raise TypeError('text must be strings')
    if not 1<=len(v)<=limit:raise ValueError('text length exceeds supported range')
    if not v.strip():raise ValueError('text must not be blank')
    if any(not (ord(c) in (9,10,13) or 32<=ord(c)<=55295 or 57344<=ord(c)<=65533 or 65536<=ord(c)<=1114111) for c in v):
        raise ValueError('text must contain only XML-valid characters')
    return v


def fact_infographic(title,facts):
    if type(facts) not in (list,tuple):raise TypeError('facts must be a list or tuple')
    if not 1<=len(facts)<=6:raise ValueError('fact count must be between 1 and 6')
    if any(type(f) not in (list,tuple) or len(f)!=2 for f in facts):raise ValueError('facts must contain label and value')
    heading=_text(title,40);data=[(_text(label,20),value) for label,value in facts]
    if any(type(value) is not int or not 0<=value<=1000000 for label,value in data):
        raise ValueError('values must be nonbool integers zero through 1000000')
    maximum=max(value for label,value in data) or 1;cards=[];elements=[]
    for i,(label,value) in enumerate(data):
        y=70+90*i;length=Fraction(240*value,maximum)
        cards.append({'x':20,'y':y,'width':360,'height':76,'bar_width':length,'label':label,'value':value})
        elements.append(f'<rect x="20" y="{y}" width="360" height="76" rx="8" fill="#edf2f8"/>')
        elements.append(f'<text x="32" y="{y+24}" font-size="10">{escape(label)}</text>')
        elements.append(f'<text x="368" y="{y+24}" text-anchor="end" font-size="10">{value}</text>')
        elements.append(f'<rect x="32" y="{y+42}" width="{float(length):.6f}" height="12" fill="#2463a0"/>')
    height=90*len(data)+80
    svg=f'<svg xmlns="http://www.w3.org/2000/svg" width="400" height="{height}"><rect width="100%" height="100%" fill="white"/><g font-family="sans-serif" fill="#172a40"><text x="20" y="38" font-size="8">{escape(heading)}</text>'+''.join(elements)+'</g></svg>'
    return {'cards':cards,'svg':svg,'source_facts_verified':False}
