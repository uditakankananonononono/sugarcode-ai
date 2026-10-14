"""Row 458: Six Sigma - Reduces defects.

PARTIAL: counts supplied defects against supplied opportunities and
computes a floored defects-per-million figure. Checks a supplied ppm
limit with exact cross-multiplication. No sigma-level conversion,
process capability, statistical assurance or defect-reduction claim.
Caps of 1-20 batches, 1-10000 opportunities, 0 to opportunity-count
 defects and limit 0-1000000 ppm are this module's own choices.
"""
MAX_BATCHES = 20
MAX_OPPORTUNITIES = 10000
MILLION = 1000000
NOT_CLAIMED = ('sigma_level', 'process_capability', 'defect_reduction')


def defects(batches, ppm_limit):
    if type(batches) is not tuple or not 1 <= len(batches) <= MAX_BATCHES:
        raise ValueError('batches: tuple of 1 to 20 pairs required')
    for i,row in enumerate(batches):
        if type(row) is not tuple or len(row) != 2:
            raise ValueError(f'batches[{i}]: pair (defects, opportunities) required')
        count, opportunities = row
        if type(opportunities) is not int or not 1 <= opportunities <= MAX_OPPORTUNITIES:
            raise ValueError(f'batches[{i}].opportunities: whole number 1 to 10000 required')
        if type(count) is not int or not 0 <= count <= opportunities:
            raise ValueError(f'batches[{i}].defects: whole number 0 to opportunities required')
    if type(ppm_limit) is not int or not 0 <= ppm_limit <= MILLION:
        raise ValueError('ppm_limit: whole number 0 to 1000000 required')
    total_defects = sum(row[0] for row in batches)
    total_opportunities = sum(row[1] for row in batches)
    numerator = total_defects * MILLION
    return {'defect_opportunities_validated': False, 'not_claimed': NOT_CLAIMED,
            'defects': total_defects, 'opportunities': total_opportunities,
            'ppm': numerator // total_opportunities,
            'within_limit': numerator <= ppm_limit * total_opportunities}
