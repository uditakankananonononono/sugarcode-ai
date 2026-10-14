"""Row 554, Natural Language Processing (PARTIAL: one exact pipeline check): each
pipeline is an exact tuple (pipeline, docs, languages) - pipeline an exact string of 1
to 24 lowercase identifier characters, docs an exact integer 0 to 100000 of documents
processed, languages an exact integer 0 to 50 supported. A pipeline is checked against
two text bars, and each bar it fails adds (index, code) to problems:
  docs below 100, else (i, 'tiny_corpus');
  languages below 2, else (i, 'monolingual').
Checks run in this order: pipelines must be an exact list; pipeline count must be at
most 40; each pipeline must be an exact tuple; each pipeline must have 3 items;
pipeline must be an exact string; pipeline must be 1 to 24 lowercase identifier
characters; docs must be an exact integer; docs must be 0 to 100000; languages must be
an exact integer; languages must be 0 to 50. Returns {'problems': sorted, 'pipelines':
sorted distinct, 'total': number of pipelines}.

NOT_CLAIMED: this checks supplied pipeline numbers against two text bars. It does not
say text is understood, that 100 documents or 2 languages are the right bars, or that
any output is right. No clinical or wet-lab claim.
"""

import re

LABEL = re.compile(r'[a-z][a-z0-9_]{0,23}\Z')


def fail(message):
    raise ValueError(message)


def check_pipelines(pipelines):
    """Flag pipelines outside the text bars."""
    if type(pipelines) is not list:
        raise TypeError('pipelines must be an exact list')
    if len(pipelines) > 40:
        fail('pipeline count must be at most 40')
    problems = []
    names = set()
    for i, pipeline in enumerate(pipelines):
        if type(pipeline) is not tuple:
            raise TypeError('each pipeline must be an exact tuple')
        if len(pipeline) != 3:
            fail('each pipeline must have 3 items')
        name, docs, languages = pipeline
        if type(name) is not str:
            raise TypeError('pipeline must be an exact string')
        if not LABEL.match(name):
            fail('pipeline must be 1 to 24 lowercase identifier characters')
        if type(docs) is not int:
            raise TypeError('docs must be an exact integer')
        if not 0 <= docs <= 100000:
            fail('docs must be 0 to 100000')
        if type(languages) is not int:
            raise TypeError('languages must be an exact integer')
        if not 0 <= languages <= 50:
            fail('languages must be 0 to 50')
        if docs < 100:
            problems.append((i, 'tiny_corpus'))
        if languages < 2:
            problems.append((i, 'monolingual'))
        names.add(name)
    return {'problems': sorted(problems), 'pipelines': sorted(names), 'total': len(pipelines)}
