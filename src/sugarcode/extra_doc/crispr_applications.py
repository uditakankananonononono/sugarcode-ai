"""Row 966, CRISPR Applications: counting the excision pairs.

Two cuts flanking a fragment let the cell excise it: a guide that
cuts at one site and again exactly four positions later excises the
fragment between them.  excise() collects the distinct cut sites
per guide, counts the site pairs exactly four apart, and reports
the guides that excise anything.

Input rows: (guide 1-8, site int 0-10).  Output: {'total',
'excisions': {guide: count of cut pairs exactly 4 apart},
'cutting': sorted guides with at least one excision}.  Reported:
cuts at 1 and 5 excise one fragment; cuts at 1, 5, and 9 excise
two (1-5 and 5-9); a repeated cut is counted once, the sites are
distinct; cuts at 2 and 5 are 3 apart and excise nothing.
"""

from typing import Any

MAX_ROWS = 100
MAX_NAME = 8
MIN_SITE = 0
MAX_SITE = 10
FRAGMENT = 4

SCOPE = 'PARTIAL: cut-site bookkeeping only; no repair outcomes modeled'
NOT_CLAIMED = (
    'does not model off-target cutting',
    'does not choose between repair pathways',
    'does not count overlapping fragments more than once per site pair',
    'does not order the cuts in time',
)


def _check_name(guide: Any, row: int) -> None:
    if not isinstance(guide, str) or type(guide) is not str:
        raise TypeError(
            f'row {row}: guide must be str, got {type(guide).__name__}')
    if not 1 <= len(guide) <= MAX_NAME:
        raise ValueError(f'row {row}: guide must be 1-8 chars')


def _check_site(site: Any, row: int) -> None:
    if type(site) is not int:
        raise TypeError(
            f'row {row}: site must be int, got {type(site).__name__}')
    if not MIN_SITE <= site <= MAX_SITE:
        raise ValueError(
            f'row {row}: site must be {MIN_SITE}-{MAX_SITE}, got {site}')


def excise(rows: Any) -> dict:
    """Return the excision summary for the supplied cut records."""
    if type(rows) not in (list, tuple):
        raise TypeError(f'rows must be list or tuple, got {type(rows).__name__}')
    if len(rows) > MAX_ROWS:
        raise ValueError(f'rows must contain at most {MAX_ROWS} entries')
    sites: dict = {}
    for index, row in enumerate(rows, 1):
        if type(row) not in (list, tuple):
            raise TypeError(
                f'row {index}: expected (guide, site) tuple, got {type(row).__name__}')
        if len(row) != 2:
            raise ValueError(
                f'row {index}: expected 2 fields, got {len(row)}')
        guide, site = row
        _check_name(guide, index)
        _check_site(site, index)
        sites.setdefault(guide, set()).add(site)
    excisions = {guide: sum(1 for site in cuts if site + FRAGMENT in cuts)
                 for guide, cuts in sites.items()}
    cutting = sorted(guide for guide, count in excisions.items() if count > 0)
    return {'total': len(rows), 'excisions': excisions, 'cutting': cutting}
