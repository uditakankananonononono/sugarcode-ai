"""Row 316 Data Visualization: bounded zero-baseline SVG bar chart.

Maps supplied nonnegative integer data to exact rational bar heights, includes
escaped category labels and value annotations, and returns both geometry and
SVG. Fixed layout permits at most eight categories without overlap.
NOT_CLAIMED: perceptual beauty, arbitrary signed/log axes, interactive charts,
statistical interpretation, universal accessibility or deployment.
"""
from fractions import Fraction
from html import escape


def bar_chart(labels,values):
    if type(labels) not in (list,tuple) or type(values) not in (list,tuple):
        raise TypeError('labels and values must be lists or tuples')
    if not 1<=len(labels)<=8:raise ValueError('category count must be between 1 and 8')
    if len(values)!=len(labels):raise ValueError('label and value counts must match')
    for label in labels:
        if type(label) is not str:raise TypeError('labels must be strings')
        if not 1<=len(label)<=12:raise ValueError('label length must be between 1 and 12')
        if not label.strip():raise ValueError('labels must not be blank')
    if any(type(v) is not int or not 0<=v<=1000000 for v in values):
        raise ValueError('values must be nonbool integers zero through 1000000')
    scale=max(values) or 1;bars=[];elements=[]
    for i,(label,value) in enumerate(zip(labels,values)):
        height=Fraction(200*value,scale);x=40+80*i;y=240-height
        bars.append({'x':x,'y':y,'width':48,'height':height,'value':value,'label':label})
        elements.append(f'<rect x="{x}" y="{float(y):.6f}" width="48" height="{float(height):.6f}" fill="#2463a0"/>')
        elements.append(f'<text x="{x+24}" y="{float(y)-8:.6f}" text-anchor="middle">{value}</text>')
        elements.append(f'<text x="{x+24}" y="265" text-anchor="middle">{escape(label)}</text>')
    width=80*len(labels)+40
    svg=f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="290" viewBox="0 0 {width} 290"><rect width="100%" height="100%" fill="white"/><g font-family="sans-serif" font-size="10"><path d="M30 40 V240 H{width-15}" fill="none" stroke="black"/>'+''.join(elements)+'</g></svg>'
    return {'bars':bars,'axis_max':scale,'svg':svg,'beauty_validated':False}
