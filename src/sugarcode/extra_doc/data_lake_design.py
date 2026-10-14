"""Row 537, Data Lake Design (PARTIAL: one exact dataset check): each dataset is an
exact tuple (dataset, gb, zones) - dataset an exact string of 1 to 24 lowercase
identifier characters, gb an exact integer 0 to 100000 of raw data stored, zones an
exact integer 0 to 10 of named zones. A dataset is checked against two storage bars,
and each bar it fails adds (index, code) to problems:
  gb over 50000, else (i, 'sprawling');
  zones below 2, else (i, 'unzoned').
Checks run in this order: datasets must be an exact list; dataset count must be at
most 40; each dataset must be an exact tuple; each dataset must have 3 items; dataset
must be an exact string; dataset must be 1 to 24 lowercase identifier characters; gb
must be an exact integer; gb must be 0 to 100000; zones must be an exact integer;
zones must be 0 to 10. Returns {'problems': sorted, 'datasets': sorted distinct,
'total': number of datasets}.

NOT_CLAIMED: this checks supplied storage numbers against two raw-data bars. It does
not say raw data is stored well, that 50000 gb or 2 zones are the right bars, or that
any byte is safe. No clinical or wet-lab claim.
"""

import re

LABEL = re.compile(r'[a-z][a-z0-9_]{0,23}\Z')


def fail(message):
    raise ValueError(message)


def check_datasets(datasets):
    """Flag datasets outside the storage bars."""
    if type(datasets) is not list:
        raise TypeError('datasets must be an exact list')
    if len(datasets) > 40:
        fail('dataset count must be at most 40')
    problems = []
    names = set()
    for i, dataset in enumerate(datasets):
        if type(dataset) is not tuple:
            raise TypeError('each dataset must be an exact tuple')
        if len(dataset) != 3:
            fail('each dataset must have 3 items')
        name, gb, zones = dataset
        if type(name) is not str:
            raise TypeError('dataset must be an exact string')
        if not LABEL.match(name):
            fail('dataset must be 1 to 24 lowercase identifier characters')
        if type(gb) is not int:
            raise TypeError('gb must be an exact integer')
        if not 0 <= gb <= 100000:
            fail('gb must be 0 to 100000')
        if type(zones) is not int:
            raise TypeError('zones must be an exact integer')
        if not 0 <= zones <= 10:
            fail('zones must be 0 to 10')
        if gb > 50000:
            problems.append((i, 'sprawling'))
        if zones < 2:
            problems.append((i, 'unzoned'))
        names.add(name)
    return {'problems': sorted(problems), 'datasets': sorted(names), 'total': len(datasets)}
