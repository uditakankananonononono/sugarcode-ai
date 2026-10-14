"""Row 699, Git Flow: branch name classification.

gitflow_names takes names, a list or tuple of 0 to max_names strings, and
max_names, a nonbool int from 1 to 20 (default 8). A name is main, develop,
or a prefix feature/, release/ or hotfix/ followed by a topic of 1 to 16
characters from a-z, 0-9 and '-' (the topic may not start or end with '-').
Any other string, including an empty one, is invalid. Each name must be
distinct.
Returns kinds ((name, kind) in input order, kind being main, develop,
feature, release, hotfix or invalid), counts ((kind, count) in the fixed
order main, develop, feature, release, hotfix, invalid) and valid (no invalid
name).
Checks, in this order: max_names, names type, names size, each name type,
duplicate names.
NOT_CLAIMED: real repository branches, merge direction, release content,
naming policy beyond this pattern, production readiness.
"""
SCOPE = 'PARTIAL: naming pattern classification of supplied branch names, no repository is read'
NOT_CLAIMED = ('real repository branches', 'merge direction', 'release content',
               'naming policy beyond this pattern', 'production readiness')

KINDS = ('main', 'develop', 'feature', 'release', 'hotfix', 'invalid')
OK = 'abcdefghijklmnopqrstuvwxyz0123456789-'


def _kind(name):
    if name == 'main':
        return 'main'
    if name == 'develop':
        return 'develop'
    for k in ('feature', 'release', 'hotfix'):
        pre = k + '/'
        if name.startswith(pre):
            topic = name[len(pre):]
            if (1 <= len(topic) <= 16 and topic[0] != '-' and topic[-1] != '-'
                    and all(c in OK for c in topic)):
                return k
            return 'invalid'
    return 'invalid'


def gitflow_names(names, max_names=8):
    if type(max_names) is not int or not 1 <= max_names <= 20:
        raise ValueError('max_names must be a nonbool integer between 1 and 20')
    if type(names) not in (list, tuple):
        raise TypeError('names must be a list or tuple')
    if len(names) > max_names:
        raise ValueError('names must contain at most max_names entries')
    for n in names:
        if type(n) is not str:
            raise ValueError('each name must be a string')
    if len(set(names)) != len(names):
        raise ValueError('names must be distinct')
    kinds = [(n, _kind(n)) for n in names]
    counts = [(k, sum(1 for _, kk in kinds if kk == k)) for k in KINDS]
    return {'kinds': kinds, 'counts': counts, 'valid': counts[-1][1] == 0}
