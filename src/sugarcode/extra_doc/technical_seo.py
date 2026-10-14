"""Row 412, Technical SEO (Bounded: one exact path rule): check supplied URL paths against a fixed structure style.

check_urls(urls) takes urls as a list of 0 to 40 exact strings of 1 to 120 characters. A path's segments are its
'/'-separated parts, empty parts dropped; its folded form is the segments lowercased and rejoined with '/'. The rules,
applied to each url i (0-based), are:
  not starting with '/', else (i, 'relative');
  an empty part inside (a double slash), else (i, 'double_slash');
  more than 4 segments, else (i, 'too_deep');
  any uppercase letter A-Z, else (i, 'uppercase');
  a folded form already listed by an earlier url, else (i, 'repeat').
One url can break several rules; all are reported. It returns {'problems': sorted (index, code), 'deepest': the
largest segment count or 0, 'total': the url count}.
Order of checks: urls (list type, count, then each in order: string type, length bounds), and only then the rules.

NOT_CLAIMED: this checks supplied strings against one fixed style. It does not say the site is crawlable, that four
levels is the right cap, or that flat paths rank better. No clinical or wet-lab claim.
"""


def _segments(url):
    return [p for p in url.split('/') if p != '']


def check_urls(urls):
    if type(urls) is not list:
        raise TypeError('urls must be an exact list')
    if len(urls) > 40:
        raise ValueError('url count must be at most 40')
    for u in urls:
        if type(u) is not str:
            raise TypeError('each url must be an exact string')
        if not 1 <= len(u) <= 120:
            raise ValueError('url length must be 1 to 120 characters')
    problems = []
    seen = set()
    deepest = 0
    for i, u in enumerate(urls):
        if not u.startswith('/'):
            problems.append((i, 'relative'))
        if '//' in u:
            problems.append((i, 'double_slash'))
        segments = _segments(u)
        if len(segments) > 4:
            problems.append((i, 'too_deep'))
        deepest = max(deepest, len(segments))
        if any('A' <= c <= 'Z' for c in u):
            problems.append((i, 'uppercase'))
        folded = '/' + '/'.join(p.lower() for p in segments)
        if folded in seen:
            problems.append((i, 'repeat'))
        seen.add(folded)
    return {'problems': sorted(problems), 'deepest': deepest, 'total': len(urls)}
