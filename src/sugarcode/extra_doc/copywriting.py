"""Row 406, Copywriting (PARTIAL: one exact channel-cap rule): check supplied copy blocks against fixed channel caps.

check_copy(blocks) takes blocks as a list of 0 to 20 tuples (channel, text): channel one of 'subject', 'headline',
'button', 'post' (exact strings), text an exact string of 1 to 300 characters. Each channel has a fixed character cap:
subject 60, headline 30, button 20, post 280. The rules, applied to each block i (0-based), are:
  text longer than its channel cap, else (i, 'over_cap');
  two or more '!' characters, else (i, 'hype');
  a word of 4 or more characters that is all capital letters A-Z, else (i, 'shouting').
One block can break several rules; all are reported. It returns {'problems': sorted (index, code), 'channels': {channel:
count} for the channels used, keyed in sorted order, 'chars': the total character count}.
Order of checks: blocks (list type, count, then each in order: tuple type, 2 items, channel type and value, text type
and length), and only then the rules.

NOT_CLAIMED: this checks caps and surface markers on supplied text. It does not say the copy converts, that the caps
fit every brand, or that shouting never works. No clinical or wet-lab claim.
"""

CAPS = {'subject': 60, 'headline': 30, 'button': 20, 'post': 280}


def _shouts(text):
    return any(len(w) >= 4 and all('A' <= c <= 'Z' for c in w) for w in text.split())


def check_copy(blocks):
    if type(blocks) is not list:
        raise TypeError('blocks must be an exact list')
    if len(blocks) > 20:
        raise ValueError('block count must be at most 20')
    for b in blocks:
        if type(b) is not tuple:
            raise TypeError('each block must be an exact tuple')
        if len(b) != 2:
            raise ValueError('each block must have 2 items')
        if type(b[0]) is not str:
            raise TypeError('channel must be an exact string')
        if b[0] not in CAPS:
            raise ValueError('channel must be one of: button, headline, post, subject')
        if type(b[1]) is not str:
            raise TypeError('text must be an exact string')
        if not 1 <= len(b[1]) <= 300:
            raise ValueError('text length must be 1 to 300 characters')
    problems = []
    channels = {}
    chars = 0
    for i, (channel, text) in enumerate(blocks):
        if len(text) > CAPS[channel]:
            problems.append((i, 'over_cap'))
        if text.count('!') >= 2:
            problems.append((i, 'hype'))
        if _shouts(text):
            problems.append((i, 'shouting'))
        channels[channel] = channels.get(channel, 0) + 1
        chars += len(text)
    return {'problems': sorted(problems), 'channels': dict(sorted(channels.items())), 'chars': chars}
