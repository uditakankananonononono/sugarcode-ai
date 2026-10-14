"""Relation Extraction - exact entity-relation-entity triples from caller-supplied text.

Pure function over caller data. No retrieval, no network, no clock, no floats, no
randomness, no model. Input: text, ASCII of 1..2000 characters made of printable
characters, newline and tab; entities, 1..50 [label, phrase] pairs; relations, 1..20
[name, phrase] pairs. A label is 1..10 lower-case ASCII letters; a relation name is
1..20 lower-case letters and underscores. An entity phrase is 1..40 ASCII characters of
letters, digits, spaces and tabs holding 1..6 tokens; a relation phrase has the same
character rule and holds 1..4 tokens. A token is a maximal run of ASCII letters and
digits. Phrases are compared case-insensitively as token sequences; entity phrases must
be distinct and relation phrases must be distinct.

Extraction: the text is cut into sentences at every '.', '!', '?' and newline. Inside a
sentence, entity mentions are found left to right, taking at each token the longest
entity phrase whose tokens follow (gaps between its tokens only spaces and tabs);
mentions never overlap. For each pair of consecutive mentions in the same sentence, if
the text between them consists only of spaces, tabs and the tokens of exactly one
relation phrase (separated by spaces and tabs), the triple (first mention, relation
name, second mention) is returned with exact offsets. Nothing else is inferred: no
transitive, symmetric or inverse relations, and no pairs that are not consecutive.

Scope: PARTIAL for the Relation Extraction line. Exact adjacency-pattern extraction
over caller-listed entities and relation phrases. It is not statistical relation
extraction: no coreference, no negation, no unlisted phrasing.

Not claimed: that a returned triple is true or is what the sentence means (for example
a negated sentence still matches), that absent triples are false, or anything about the
real world. Every claim flag in the result is False.
"""
MAX_TEXT = 2000
MAX_ENT = 50
MAX_REL = 20
MAX_LABEL = 10
MAX_NAME = 20
MAX_PHRASE = 40
MAX_ENT_TOKENS = 6
MAX_REL_TOKENS = 4
_TOP = frozenset({"text", "entities", "relations"})

NOT_CLAIMED = (
    "a returned triple is true or is what the sentence means",
    "absent triples are false",
    "negation, coreference or unlisted phrasing is handled",
    "real-world outcome",
)
CLAIMS = {"truth": False, "negation_handled": False, "completeness": False, "real_world": False}


class ReError(ValueError):
    pass


def _alnum(c):
    return ("a" <= c <= "z") or ("A" <= c <= "Z") or ("0" <= c <= "9")


def _tokens(s):
    out, i, n = [], 0, len(s)
    while i < n:
        if _alnum(s[i]):
            j = i
            while j < n and _alnum(s[j]):
                j += 1
            out.append((s[i:j].lower(), i, j))
            i = j
        else:
            i += 1
    return out


def _pairs(raw, what, lo_max, tok_max, name_ok, name_msg):
    if not isinstance(raw, list) or not 1 <= len(raw) <= lo_max:
        raise ReError(f"{what} must be a list of 1..{lo_max} pairs")
    index = {}
    for e in raw:
        if not isinstance(e, list) or len(e) != 2:
            raise ReError(f"{what} entry must be a pair")
        name, phrase = e
        if not isinstance(name, str) or not isinstance(phrase, str):
            raise ReError(f"{what} name and phrase must be strings")
        if not name_ok(name):
            raise ReError(name_msg)
        if not 1 <= len(phrase) <= MAX_PHRASE:
            raise ReError(f"{what} phrase length out of range")
        if not all(_alnum(c) or c in " \t" for c in phrase):
            raise ReError(f"{what} phrase may contain only letters, digits, spaces and tabs")
        toks = tuple(t[0] for t in _tokens(phrase))
        if not 1 <= len(toks) <= tok_max:
            raise ReError(f"{what} phrase must have 1..{tok_max} tokens")
        if toks in index:
            raise ReError(f"{what} phrases must be distinct")
        index[toks] = name
    return index


def _label_ok(s):
    return 1 <= len(s) <= MAX_LABEL and all("a" <= c <= "z" for c in s)


def _relname_ok(s):
    return 1 <= len(s) <= MAX_NAME and all(("a" <= c <= "z") or c == "_" for c in s)


def _validate(data):
    if not isinstance(data, dict) or set(data) != _TOP:
        raise ReError("data keys must be exactly text, entities, relations")
    text = data["text"]
    if not isinstance(text, str):
        raise ReError("text must be a string")
    if not 1 <= len(text) <= MAX_TEXT:
        raise ReError("text length out of range")
    if not text.isascii():
        raise ReError("text must be ASCII")
    for c in text:
        if (ord(c) < 32 and c not in "\n\t") or ord(c) == 127:
            raise ReError("text has a disallowed control character")
    ents = _pairs(data["entities"], "entities", MAX_ENT, MAX_ENT_TOKENS, _label_ok,
                  "entity label must be 1..10 lower-case ASCII letters")
    rels = _pairs(data["relations"], "relations", MAX_REL, MAX_REL_TOKENS, _relname_ok,
                  "relation name must be 1..20 lower-case letters or underscores")
    return text, ents, rels


def _sentences(text):
    out, start = [], 0
    for i, c in enumerate(text):
        if c in ".!?\n":
            out.append((start, i))
            start = i + 1
    out.append((start, len(text)))
    return out


def _mentions(text, a, b, ents, longest):
    toks = [(w, s + a, e + a) for w, s, e in _tokens(text[a:b])]
    out, i = [], 0
    while i < len(toks):
        hit = None
        for n in range(min(longest, len(toks) - i), 0, -1):
            key = tuple(t[0] for t in toks[i:i + n])
            if key in ents and all(
                all(c in " \t" for c in text[toks[k][2]:toks[k + 1][1]]) for k in range(i, i + n - 1)
            ):
                hit = (n, key)
                break
        if hit is None:
            i += 1
            continue
        n, key = hit
        out.append({"label": ents[key], "phrase": " ".join(key), "start": toks[i][1], "end": toks[i + n - 1][2]})
        i += n
    return out


def _relation_between(gap, rels):
    if not all(_alnum(c) or c in " \t" for c in gap):
        return None
    key = tuple(t[0] for t in _tokens(gap))
    return rels.get(key)


def relation_extraction(data):
    text, ents, rels = _validate(data)
    longest = max(len(k) for k in ents)
    triples, found, scanned = [], 0, 0
    for a, b in _sentences(text):
        if _tokens(text[a:b]):
            scanned += 1
        ms = _mentions(text, a, b, ents, longest)
        found += len(ms)
        for x, y in zip(ms, ms[1:]):
            name = _relation_between(text[x["end"]:y["start"]], rels)
            if name is not None:
                triples.append({"subject": dict(x), "relation": name, "object": dict(y)})
    return {
        "status": "completed",
        "triples": triples,
        "mentions_found": found,
        "sentences_scanned": scanned,
        "claims": dict(CLAIMS),
        "not_claimed": list(NOT_CLAIMED),
    }
