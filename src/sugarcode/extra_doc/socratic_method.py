"""Row 741, Socratic Method: auditing one teacher-student exchange.

Teaches through questions by structure. Turns apply in order, each a
(speaker, text) row with speaker the string teacher or student and
text a string of 1 to 80 characters. Turns must alternate, starting
with the teacher. A probe is a teacher turn whose text ends with ?.
Reported: the probe count, the turn count, and stopped_at - the index
of the first teacher turn that is not a probe, or None when every
teacher turn probes.
Caps (checked before any work): 0 to 100 turns.
NOT_CLAIMED: real dialogue, pedagogy, question quality, intent,
follow-up generation, assessment, production readiness.
"""
SCOPE = 'PARTIAL: turn-structure audit over supplied turns, no real dialogue'
NOT_CLAIMED = ('real dialogue', 'pedagogy', 'question quality', 'intent',
               'follow-up generation', 'assessment', 'production readiness')

MAX_TURNS = 100
MAX_TEXT = 80


def probe(turns):
    if type(turns) not in (list, tuple):
        raise TypeError('turns must be a list or tuple')
    if len(turns) > MAX_TURNS:
        raise ValueError('turns must contain at most 100 rows')
    rows = []
    for index, row in enumerate(turns):
        if type(row) not in (list, tuple) or len(row) != 2:
            raise ValueError('each turn must be a (speaker, text) row')
        speaker, text = row
        if type(speaker) is not str or speaker not in ('teacher', 'student'):
            raise ValueError('speaker must be the string teacher or student')
        if type(text) is not str or not 1 <= len(text) <= MAX_TEXT:
            raise ValueError('text must be a string of 1 to 80 characters')
        if speaker != ('teacher' if index % 2 == 0 else 'student'):
            raise ValueError('turns must alternate starting with the teacher')
        rows.append((speaker, text))
    probes = 0
    stopped_at = None
    for index, (speaker, text) in enumerate(rows):
        if speaker != 'teacher':
            continue
        if text.endswith('?'):
            probes += 1
        elif stopped_at is None:
            stopped_at = index
    return {'probes': probes, 'turns': len(rows), 'stopped_at': stopped_at}
