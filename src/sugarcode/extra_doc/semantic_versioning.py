"""Row 700, Semantic Versioning: bumping one version over supplied changes.

Communicates changes through version arithmetic. A version is a
(major, minor, patch) row. Changes apply in order, each the string
breaking, feature, or fix: breaking bumps major and resets minor and
patch to 0, feature bumps minor and resets patch to 0, fix bumps patch.
Reported: the version after each change and the final version. Caps
(checked before any work): each supplied version component a nonbool
int from 0 to 100; 0 to 100 changes. Bumped components may exceed 100;
only the supplied version is capped.
NOT_CLAIMED: git tags, release automation, dependency resolution,
compatibility checks, pre-release versions, build metadata, production
readiness.
"""
SCOPE = 'PARTIAL: rule-based version bumping over supplied changes, no real release management'
NOT_CLAIMED = ('git tags', 'release automation', 'dependency resolution',
               'compatibility checks', 'pre-release versions', 'build metadata',
               'production readiness')

MAX_COMPONENT = 100
MAX_CHANGES = 100


def bump(version, changes):
    if type(version) not in (list, tuple):
        raise TypeError('version must be a list or tuple')
    if len(version) != 3:
        raise ValueError('version must be a (major, minor, patch) row')
    for component in version:
        if type(component) is not int or not 0 <= component <= MAX_COMPONENT:
            raise ValueError('version components must be nonbool integers between 0 and 100')
    if type(changes) not in (list, tuple):
        raise TypeError('changes must be a list or tuple')
    if len(changes) > MAX_CHANGES:
        raise ValueError('changes must contain at most 100 rows')
    for change in changes:
        if type(change) is not str or change not in ('breaking', 'feature', 'fix'):
            raise ValueError('changes must be the strings breaking, feature, or fix')
    major, minor, patch = version
    versions = []
    for change in changes:
        if change == 'breaking':
            major, minor, patch = major + 1, 0, 0
        elif change == 'feature':
            minor, patch = minor + 1, 0
        else:
            patch = patch + 1
        versions.append((major, minor, patch))
    return {'versions': versions, 'final': (major, minor, patch)}
