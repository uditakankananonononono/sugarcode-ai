"""Row269 Voice Development: constrained supplied-rule voice generation.

Choose lexical alternatives and a supplied syntax rule, realize a sentence and
voice profile nearest a supplied lexical/syntax tone target in exact L1 distance.
Certificate proves optimum within the bounded supplied candidate grammar.
NOT_CLAIMED learned/distinctive literary voice, quality/originality assessment,
free-text storytelling, broad stylistic generalization or natural-language AI.
"""
from fractions import Fraction as F
from itertools import product


def _integer(x):
    if type(x) is not int:raise TypeError('exact nonbool integer required')
    if not -10<=x<=10:raise ValueError('tone cap exceeded')


def voice_development(lexicon,rules,target):
    if not isinstance(lexicon,list) or not 1<=len(lexicon)<=3:raise ValueError('slot cap 1..3 required')
    if not isinstance(rules,list) or not 1<=len(rules)<=4:raise ValueError('rule cap 1..4 required')
    if not isinstance(target,list) or len(target)!=2:raise ValueError('two target tones required')
    for value in target:_integer(value)
    for slot in lexicon:
        if not isinstance(slot,list) or not 1<=len(slot)<=3:raise ValueError('alternative cap 1..3 required')
        for item in slot:
            if type(item) is not tuple or len(item)!=2:raise ValueError('word/tone pair required')
            word,tone=item
            if type(word) is not str or not 1<=len(word)<=20:raise ValueError('word cap 1..20 required')
            if any(x.isspace() for x in word):raise ValueError('single token required')
            _integer(tone)
    for rule in rules:
        if type(rule) is not tuple or len(rule)!=3:raise ValueError('order/tone/ending rule required')
        order,tone,ending=rule
        if not isinstance(order,list) or len(order)!=len(lexicon):raise ValueError('syntax dimension mismatch')
        if any(type(x) is not int for x in order) or sorted(order)!=list(range(len(lexicon))):raise ValueError('syntax permutation required')
        _integer(tone)
        if type(ending) is not str or ending not in ('.','!','?'):raise ValueError('sentence ending required')
    best=None
    for rid,(order,tone,ending) in enumerate(rules):
        for indices in product(*(range(len(slot)) for slot in lexicon)):
            words=[lexicon[i][j] for i,j in enumerate(indices)]
            profile=(sum(F(x[1]) for x in words)/len(words),F(tone))
            distance=sum(abs(a-b) for a,b in zip(profile,target))
            candidate=(distance,rid,indices,profile,' '.join(words[i][0] for i in order)+ending)
            if best is None or candidate<best:best=candidate
    distance,rid,indices,profile,sentence=best
    return {'sentence':sentence,'profile':list(profile),'word_indices':list(indices),'rule_index':rid,
            'certificate':{'distance':distance,'optimal':True,'target':target[:]}}
