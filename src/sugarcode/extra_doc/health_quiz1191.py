"""Row 1191, Health Education.

PARTIAL: caller-supplied quiz response scoring only. No health information is
created or validated; no health literacy, clinical knowledge or outcome claim.

score_quiz(key, responses) accepts exact list/tuple containers. Key has 1..32
exact pairs (question, answer) of exact ASCII word strings, length 1..24.
Question IDs must be unique. Responses has 0..64 exact triples (learner,
question, answer); each question must occur in key. All identifiers use ASCII
letters, digits and underscore with no initial-character restriction. The
last response per learner and question replaces earlier responses. At most
16 learners. Validate all key rows in order, then response rows in order;
learner count is checked after response validation. Returned rows are sorted
(learner, correct, attempted, unanswered). A learner with no response is not
invented. Answers are compared by exact string equality, case sensitive.
"""
SCOPE = 'PARTIAL: supplied quiz-key comparison only; no health-content judgment'
NOT_CLAIMED = (
    'does not generate health advice or educational content',
    'does not validate the supplied answer key',
    'does not measure health literacy or clinical knowledge',
    'does not establish learning or health outcomes',
)


def _name(x):
    if type(x) is not str:
        raise TypeError('identifier must be an exact string')
    if not 1 <= len(x) <= 24 or not all(
        c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_'
        for c in x
    ):
        raise ValueError('identifier must be 1..24 ASCII word characters')


def score_quiz(key, responses):
    if type(key) not in (list, tuple):
        raise TypeError('key must be an exact list or tuple')
    if not 1 <= len(key) <= 32:
        raise ValueError('key must contain 1..32 questions')
    answers = {}
    for row in key:
        if type(row) not in (list, tuple):
            raise TypeError('key row must be an exact list or tuple')
        if len(row) != 2:
            raise ValueError('key row must have two identifiers')
        q, answer = row
        _name(q)
        _name(answer)
        if q in answers:
            raise ValueError('key question identifiers must be unique')
        answers[q] = answer
    if type(responses) not in (list, tuple):
        raise TypeError('responses must be an exact list or tuple')
    if len(responses) > 64:
        raise ValueError('at most 64 responses required')
    latest = {}
    for row in responses:
        if type(row) not in (list, tuple):
            raise TypeError('response row must be an exact list or tuple')
        if len(row) != 3:
            raise ValueError('response row must have three identifiers')
        learner, question, answer = row
        _name(learner)
        _name(question)
        _name(answer)
        if question not in answers:
            raise ValueError('response question must occur in key')
        latest.setdefault(learner, {})[question] = answer
    if len(latest) > 16:
        raise ValueError('at most 16 learners allowed')
    scores = []
    for learner in sorted(latest):
        attempts = latest[learner]
        correct = sum(answer == answers[q] for q, answer in attempts.items())
        scores.append((learner, correct, len(attempts), len(answers) - len(attempts)))
    return {'scores': scores, 'scope': SCOPE, 'not_claimed': list(NOT_CLAIMED)}
