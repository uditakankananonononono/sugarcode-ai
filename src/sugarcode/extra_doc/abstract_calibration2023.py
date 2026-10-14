"""Row 2023: Metacognition.

PARTIAL: exact supplied binary correctness and confidence-bin calibration
counts. Local caps; no metacognitive validity, confidence truth or learning
benefit. Bins 0-10 are supplied abstract units, not measured probabilities.
"""
NOT_CLAIMED = ('metacognitive_validity', 'confidence_truth', 'learning_benefit')


def calibration(rows):
    if type(rows) is not tuple or not 1 <= len(rows) <= 20:
        raise ValueError('rows: tuple of 1 to 20 confidence-bit pairs required')
    for i,row in enumerate(rows):
        if type(row) is not tuple or len(row) != 2:
            raise ValueError(f'rows[{i}]: pair (confidence, correct) required')
        confidence,correct = row
        if type(confidence) is not int or not 0 <= confidence <= 10:
            raise ValueError(f'rows[{i}].confidence: integer 0 to 10 required')
        if type(correct) is not int or correct not in (0,1):
            raise ValueError(f'rows[{i}].correct: integer zero or one required')
    counts = tuple(sum(c == k for c,_ in rows) for k in range(11))
    successes = tuple(sum(bit for c,bit in rows if c == k) for k in range(11))
    gaps = tuple(10*successes[k]-k*counts[k] for k in range(11))
    return {'abstract_calibration_validated': False, 'not_claimed': NOT_CLAIMED,
            'bin_counts': counts, 'bin_successes': successes, 'signed_calibration_units': gaps}
