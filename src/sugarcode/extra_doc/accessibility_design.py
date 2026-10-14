"""Row 344 Accessibility Design: bounded semantic content-page generation.

Creates an escaped HTML page with one h1, ordered h2 sections, descriptive
paragraphs, a keyboard skip link, and optional SVG illustration descriptions.
Illustration labels are emitted as accessible SVG titles, not filename guesses.
Implementation caps eight sections and bounded XML-valid text fields.
NOT_CLAIMED: universal accessibility, WCAG certification, assistive-technology
compatibility testing, semantic accuracy of descriptions or deployment.
"""
from html import escape


def _text(value,limit):
    if type(value) is not str:raise TypeError('text fields must be strings')
    if not 1<=len(value)<=limit:raise ValueError('text length exceeds supported range')
    if not value.strip():raise ValueError('text fields must not be blank')
    if any(not (ord(c) in (9,10,13) or 32<=ord(c)<=55295 or 57344<=ord(c)<=65533 or 65536<=ord(c)<=1114111) for c in value):
        raise ValueError('text must contain only XML-valid characters')
    return value


def accessible_page(title,sections):
    if type(sections) not in (list,tuple):raise TypeError('sections must be a list or tuple')
    if not 1<=len(sections)<=8:raise ValueError('section count must be between 1 and 8')
    if any(type(section) not in (list,tuple) or len(section)!=3 for section in sections):
        raise ValueError('sections must contain heading paragraph and optional illustration description')
    name=_text(title,80);data=[]
    for heading,paragraph,description in sections:
        h=_text(heading,80);p=_text(paragraph,1024)
        d=None if description is None else _text(description,256)
        data.append((h,p,d))
    content=[]
    for i,(heading,paragraph,description) in enumerate(data):
        image=''
        if description is not None:
            image=f'<svg xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="image-title-{i}" viewBox="0 0 200 60" width="200" height="60"><title id="image-title-{i}">{escape(description)}</title><rect x="1" y="1" width="198" height="58" fill="#e8eef4" stroke="#172a40"/></svg>'
        content.append(f'<section aria-labelledby="heading-{i}"><h2 id="heading-{i}">{escape(heading)}</h2><p>{escape(paragraph)}</p>{image}</section>')
    html='<html lang="en"><head><meta charset="utf-8"/><title>'+escape(name)+'</title><style>body{font:18px sans-serif;line-height:1.5;color:#172a40;background:white;max-width:720px;margin:24px auto;padding:0 20px}p{overflow-wrap:anywhere}h1,h2{overflow-wrap:anywhere}.skip{display:inline-block}section{margin:24px 0}</style></head><body><a class="skip" href="#main">Skip to content</a><main id="main" tabindex="-1"><h1>'+escape(name)+'</h1>'+''.join(content)+'</main></body></html>'
    return {'html':html,'section_count':len(data),'illustration_count':sum(d is not None for h,p,d in data),'accessibility_certified':False}
