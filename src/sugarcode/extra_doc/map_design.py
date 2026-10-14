"""Row 318 Map Design: bounded schematic route SVG generation.

Draws supplied coordinate locations and a supplied ordered route in a fixed
500x500 canvas, with labels and direction markers. Coordinates already use
canvas pixels; no invented projection, geocoding or navigation advice.
NOT_CLAIMED: geographic accuracy, shortest routing, live traffic, accessibility,
label collision optimization, real-world directions or deployment.
"""
from html import escape


def route_map(locations,route):
    if type(locations) not in (list,tuple) or type(route) not in (list,tuple):
        raise TypeError('locations and route must be lists or tuples')
    if not 1<=len(locations)<=16:raise ValueError('location count must be between 1 and 16')
    if not 1<=len(route)<=32:raise ValueError('route count must be between 1 and 32')
    if any(type(v) not in (list,tuple) or len(v)!=3 for v in locations):
        raise ValueError('locations must contain label x and y')
    for label,x,y in locations:
        if type(label) is not str:raise TypeError('labels must be strings')
        if not 1<=len(label)<=12:raise ValueError('label length must be between 1 and 12')
        if not label.strip():raise ValueError('labels must not be blank')
        if any(not (ord(c) in (9,10,13) or 32<=ord(c)<=55295 or 57344<=ord(c)<=65533 or 65536<=ord(c)<=1114111) for c in label):
            raise ValueError('labels must contain only XML-valid characters')
        if type(x) is not int or type(y) is not int or not 30<=x<=440 or not 30<=y<=440:
            raise ValueError('coordinates must be nonbool integers between 30 and 440')
    if any(type(i) is not int or not 0<=i<len(locations) for i in route):
        raise ValueError('route indices must be nonbool integers inside location range')
    points=[(locations[i][1],locations[i][2]) for i in route]
    path=' '.join(f'{x},{y}' for x,y in points)
    elements=[f'<polyline points="{path}" fill="none" stroke="#2463a0" stroke-width="4" marker-mid="url(#arrow)" marker-end="url(#arrow)"/>']
    for i,(label,x,y) in enumerate(locations):
        elements.append(f'<circle cx="{x}" cy="{y}" r="5" fill="#172a40"/>')
        anchor='end' if x>250 else 'start';tx=x-8 if x>250 else x+8
        elements.append(f'<text x="{tx}" y="{y-8}" text-anchor="{anchor}" font-size="10">{escape(label)}</text>')
    svg='<svg xmlns="http://www.w3.org/2000/svg" width="500" height="500"><rect width="100%" height="100%" fill="white"/><defs><marker id="arrow" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="4" markerHeight="4" orient="auto"><path d="M0 0 L10 5 L0 10 Z" fill="#2463a0"/></marker></defs><g font-family="sans-serif">'+''.join(elements)+'</g></svg>'
    return {'route_points':points,'svg':svg,'geographic_accuracy_validated':False}
