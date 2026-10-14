"""Row 549 Search System - Finds relevant content.

Bounded bounded token-overlap search over supplied ASCII document text only.
No external retrieval, index persistence, stemming or semantic relevance claim.
Explicit import, no IO. Query/document tokens are exact case-folded words.
"""
import re

LABEL = re.compile(r"[a-z][a-z0-9_]{0,23}\Z")


def _label(value):
    if type(value) is not str:
        raise TypeError('exact string label required')
    if len(value) > 24 or LABEL.fullmatch(value) is None:
        raise ValueError('label must be 1..24 lowercase identifier characters')


def _rows(rows, arity):
    if type(rows) is not list:
        raise TypeError('exact list required')
    if not 1 <= len(rows) <= 32:
        raise ValueError('row count must be 1..32')
    for row in rows:
        if type(row) is not tuple:
            raise TypeError('exact tuple row required')
        if len(row) != arity:
            raise ValueError('wrong row arity')



def _text(value, cap):
    if type(value) is not str:
        raise TypeError('exact text string required')
    if not 1 <= len(value) <= cap:
        raise ValueError('text length outside declared range')
    if re.fullmatch(r'[A-Za-z0-9 ]+', value) is None:
        raise ValueError('ASCII words and spaces required')
    tokens = set(value.lower().split())
    if not tokens:
        raise ValueError('at least one token required')
    return tokens


def search_documents(rows, query):
    """Rows (document_id, text1..1024), query1..256. Return matching docs
    ranked by count of distinct query tokens matched, ties by document ID.
    """
    terms = _text(query, 256)
    _rows(rows, 2)
    parsed = []
    for document, text in rows:
        _label(document)
        tokens = _text(text, 1024)
        parsed.append((document,tokens))
    if len({document for document,_ in parsed}) != len(rows):
        raise ValueError('duplicate document')
    matches = [(document,len(tokens & terms),sorted(tokens & terms))
               for document,tokens in parsed if tokens & terms]
    return {'matches': sorted(matches,key=lambda x:(-x[1],x[0])),
            'query_tokens': sorted(terms)}
