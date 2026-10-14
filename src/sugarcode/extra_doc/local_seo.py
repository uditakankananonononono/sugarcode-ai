"""Row 413, Local SEO (Bounded: one exact consistency rule): check supplied location pages for slug and phone consistency.

check_locations(pages) takes pages as a list of 0 to 30 tuples (slug, city, phone): slug 1 to 24 lowercase identifier
characters, city an exact string of 1 to 40 characters, phone an exact string of exactly 10 digits. A city's folded
form is its words lowercased and joined with '_'. The rules, applied to each page i (0-based), are:
  a slug used by an earlier page, else (i, 'same_slug');
  a phone used by an earlier page, else (i, 'shared_phone');
  the city's folded form not a substring of the slug, else (i, 'slug_mismatch');
  a city whose folded form is already used with a different phone, else (i, 'phone_split').
One page can break several rules; all are reported. It returns {'problems': sorted (index, code), 'cities': sorted
distinct folded cities, 'total': the page count}.
Order of checks: pages (list type, count, then each in order: tuple type, 3 items, slug type and shape, city type and
length, phone type and shape), and only then the rules.

NOT_CLAIMED: this checks supplied records against one naming style. It does not say the pages rank locally, that the
phones are real, or that matching slugs help. No clinical or wet-lab claim.
"""
import re

LABEL = re.compile(r'[a-z][a-z0-9_]{0,23}\Z')
DIGITS = re.compile(r'[0-9]{10}\Z')


def _fold(city):
    return '_'.join(city.lower().split())


def check_locations(pages):
    if type(pages) is not list:
        raise TypeError('pages must be an exact list')
    if len(pages) > 30:
        raise ValueError('page count must be at most 30')
    for p in pages:
        if type(p) is not tuple:
            raise TypeError('each page must be an exact tuple')
        if len(p) != 3:
            raise ValueError('each page must have 3 items')
        if type(p[0]) is not str:
            raise TypeError('slug must be an exact string')
        if LABEL.fullmatch(p[0]) is None:
            raise ValueError('slug must be 1 to 24 lowercase identifier characters')
        if type(p[1]) is not str:
            raise TypeError('city must be an exact string')
        if not 1 <= len(p[1]) <= 40:
            raise ValueError('city length must be 1 to 40 characters')
        if type(p[2]) is not str:
            raise TypeError('phone must be an exact string')
        if DIGITS.fullmatch(p[2]) is None:
            raise ValueError('phone must be exactly 10 digits')
    problems = []
    seen_slugs = set()
    seen_phones = set()
    city_phone = {}
    for i, (slug, city, phone) in enumerate(pages):
        if slug in seen_slugs:
            problems.append((i, 'same_slug'))
        seen_slugs.add(slug)
        if phone in seen_phones:
            problems.append((i, 'shared_phone'))
        seen_phones.add(phone)
        folded = _fold(city)
        if folded not in slug:
            problems.append((i, 'slug_mismatch'))
        if folded in city_phone and city_phone[folded] != phone:
            problems.append((i, 'phone_split'))
        else:
            city_phone.setdefault(folded, phone)
    return {'problems': sorted(problems), 'cities': sorted(city_phone), 'total': len(pages)}
