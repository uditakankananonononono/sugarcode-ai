"""Row 1908, Title: Visual Culture

rank_images(rows): rows are (image, medium, impact) triples;
image and medium strings of 1 to 16 characters; impact a
nonbool integer between 1 and 9. Caps (checked before any
work): 1 to 60 rows. Reported: the total row count, for each
image its clout (the total impact), the viral images (clout
at least 15, sorted alphabetically), the overlooked images
(clout at most 4, sorted alphabetically), and the podium (the
top 3 images ordered by clout descending, first supplied on
ties).

SCOPE: PARTIAL: image ranking over supplied impacts
NOT_CLAIMED: visual semiotics, reception studies, censorship,
media archaeology, production readiness.
"""

SCOPE = 'PARTIAL: image ranking over supplied impacts'
NOT_CLAIMED = ('visual semiotics', 'reception studies', 'censorship',
               'media archaeology', 'production readiness')


def rank_images(rows):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 60:
        raise ValueError('rows must contain between 1 and 60 entries')
    for i, row in enumerate(rows, 1):
        if type(row) not in (list, tuple):
            raise TypeError(f'row {i}: expected a (image, medium, impact) triple')
        if len(row) != 3:
            raise ValueError(f'row {i}: expected 3 fields, got {len(row)}')
        image, medium, impact = row
        if type(image) is not str or not 1 <= len(image) <= 16:
            raise ValueError(f'row {i}: image must be a string of 1 to 16 characters')
        if type(medium) is not str or not 1 <= len(medium) <= 16:
            raise ValueError(f'row {i}: medium must be a string of 1 to 16 characters')
        if type(impact) is not int or not 1 <= impact <= 9:
            raise ValueError(f'row {i}: impact must be a nonbool integer between 1 and 9')
    clout = {}
    for image, medium, impact in rows:
        if image not in clout:
            clout[image] = 0
        clout[image] += impact
    viral = sorted(i for i in clout if clout[i] >= 15)
    overlooked = sorted(i for i in clout if clout[i] <= 4)
    position = {}
    for j, image in enumerate(clout):
        position[image] = j
    podium = sorted(clout, key=lambda k: (-clout[k], position[k]))[:3]
    return {'total': len(rows),
            'clout': clout,
            'viral': viral,
            'overlooked': overlooked,
            'podium': podium}
