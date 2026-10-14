"""Row 979, Personalized Medicine: balancing each patient's responses.

A tailored course alternates between pushing and easing, so the
running balance says whether the patient is being over- or
under-corrected.  tailor() alternates the sign of each patient's
responses - first record positive, second negative, and so on - and
reports the patients whose balance lands inside the steady band.

Input rows: (patient 1-8, response int 0-10).  Steady band is -3..3.
Output: {'total', 'balances': {patient: alternating sum},
'steady': sorted patients balancing between -3 and 3 inclusive}.
Reported: responses 4, 1, 2 balance 4 - 1 + 2 = 5 and lose steady;
4, 1 balance 3 and hold the edge of the band; 1, 4 balance -3, the
other edge; a lone record balances itself; the sign alternates per
record, so 4, 1, 2, 3 balances 2 while 3, 2, 1, 4 balances -2.
"""

from typing import Any

MAX_ROWS = 100
MAX_NAME = 8
MIN_RESPONSE = 0
MAX_RESPONSE = 10
BAND = 3

SCOPE = 'PARTIAL: response bookkeeping only; no treatment modeling'
NOT_CLAIMED = (
    'does not model drug interactions',
    'does not weight responses by recency',
    'does not compare patients against each other',
    'does not cap the balance during accumulation',
)


def _check_name(patient: Any, row: int) -> None:
    if not isinstance(patient, str) or type(patient) is not str:
        raise TypeError(
            f'row {row}: patient must be str, got {type(patient).__name__}')
    if not 1 <= len(patient) <= MAX_NAME:
        raise ValueError(f'row {row}: patient must be 1-8 chars')


def _check_response(response: Any, row: int) -> None:
    if type(response) is not int:
        raise TypeError(
            f'row {row}: response must be int, got {type(response).__name__}')
    if not MIN_RESPONSE <= response <= MAX_RESPONSE:
        raise ValueError(
            f'row {row}: response must be {MIN_RESPONSE}-{MAX_RESPONSE}, got {response}')


def tailor(rows: Any) -> dict:
    """Return the balance summary for the supplied response records."""
    if type(rows) not in (list, tuple):
        raise TypeError(f'rows must be list or tuple, got {type(rows).__name__}')
    if len(rows) > MAX_ROWS:
        raise ValueError(f'rows must contain at most {MAX_ROWS} entries')
    balances: dict = {}
    signs: dict = {}
    for index, row in enumerate(rows, 1):
        if type(row) not in (list, tuple):
            raise TypeError(
                f'row {index}: expected (patient, response) tuple, got {type(row).__name__}')
        if len(row) != 2:
            raise ValueError(
                f'row {index}: expected 2 fields, got {len(row)}')
        patient, response = row
        _check_name(patient, index)
        _check_response(response, index)
        if patient not in balances:
            balances[patient] = 0
            signs[patient] = 1
        balances[patient] += signs[patient] * response
        signs[patient] = -signs[patient]
    steady = sorted(patient for patient, balance in balances.items()
                    if -BAND <= balance <= BAND)
    return {'total': len(rows), 'balances': balances, 'steady': steady}
