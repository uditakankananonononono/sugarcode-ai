"""Row 925: DNA Computing - Biological computation.

PARTIAL: encodes A,C,G,T as 0,1,2,3 and XORs paired symbols, returning
the symbols for the result. This arbitrary two-bit encoding is this
module's own choice, not a DNA computing protocol. No molecular
execution, biological computation or laboratory validation.
Caps of 1-30 symbols per exact string are this module's own choices.
"""
MAX_SYMBOLS = 30
ALPHABET = 'ACGT'
NOT_CLAIMED = ('molecular_execution', 'biological_computation', 'laboratory_validation')


def xor(left, right):
    for name,text in (('left',left),('right',right)):
        if type(text) is not str or not 1 <= len(text) <= MAX_SYMBOLS:
            raise ValueError(f'{name}: text of 1 to 30 symbols required')
        for i,symbol in enumerate(text):
            if symbol not in ALPHABET:
                raise ValueError(f'{name}[{i}]: uppercase A,C,G,T required')
    if len(left) != len(right):
        raise ValueError('left and right must have equal length')
    encoded = tuple(ALPHABET.index(a) ^ ALPHABET.index(b) for a,b in zip(left,right))
    result = ''.join(ALPHABET[value] for value in encoded)
    return {'dna_symbol_xor_validated': False, 'not_claimed': NOT_CLAIMED,
            'symbols': result, 'encoded': encoded, 'zero_positions': tuple(i for i in range(len(encoded)) if encoded[i] == 0)}
