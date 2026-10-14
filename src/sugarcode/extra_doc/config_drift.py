"""Row 613, Configuration Management (bounded scope: one exact step): layered settings and drift from them.

config_drift(layers, actual) merges settings layers, lowest priority first, and compares the result with a supplied
actual configuration. A setting key is 1 to 4 lowercase identifier segments joined by dots (each segment 1 to 16
characters, starting with a letter; for example "db.pool_size"); a value is a nonbool int from -1000000 to 1000000 or a
string of 0 to 32 printable ASCII characters. A later layer replaces the value of the same key from an earlier one.
It returns:
  merged      sorted (key, value) pairs of the final settings;
  source      sorted (key, layer_index) pairs: which layer (0 is the first) supplied each final value;
  overridden  how many (layer, key) settings were replaced by a later layer;
  missing     keys in merged but not in actual, sorted;
  extra       keys in actual but not in merged, sorted;
  changed     keys in both whose values differ (the string "1" and the int 1 differ), sorted;
  in_sync     True when missing, extra and changed are all empty.
A key may not be both a setting and the start of a longer key across the layers ("a" with "a.b" is an error).
Caps: 1 to 8 layers, each a dict of at most 16 settings; actual a dict of at most 128 settings.
Order of checks: layers type, layer count, then each layer in order (dict type, size, then each setting in insertion
order: key type, key shape, value type, value range or characters), then actual (dict type, size, each setting the same
way), then the prefix conflict (the first conflicting key in sorted order), and only then
the comparison.

NOT_CLAIMED: this is a calculation on supplied dictionaries. It does not read or write any real configuration or
file, apply a setting to any system, check that a value suits any program, handle secrets, or watch for change.
No clinical or wet-lab claim.
"""
import re

SEG = r'[a-z][a-z0-9_]{0,15}'
KEY = re.compile(SEG + r'(\.' + SEG + r'){0,3}\Z')
MAX_LAYERS = 8
MAX_LAYER = 16
MAX_ACTUAL = 128


def _setting(k, v, what):
    if type(k) is not str:
        raise TypeError(what + ': key must be an exact string')
    if KEY.fullmatch(k) is None:
        raise ValueError(what + ': key must be 1 to 4 dotted lowercase identifiers')
    if type(v) is int:
        if not -1000000 <= v <= 1000000:
            raise ValueError(what + ': int value must be between -1000000 and 1000000')
    elif type(v) is str:
        if len(v) > 32 or any(not 32 <= ord(ch) <= 126 for ch in v):
            raise ValueError(what + ': string value must be at most 32 printable ASCII characters')
    else:
        raise TypeError(what + ': value must be an exact int or str')


def _dict(d, cap, what):
    if type(d) is not dict:
        raise TypeError(what + ': must be an exact dict')
    if len(d) > cap:
        raise ValueError(what + ': at most %d settings' % cap)
    for k, v in d.items():
        _setting(k, v, what)


def config_drift(layers, actual):
    if type(layers) is not list:
        raise TypeError('layers must be an exact list')
    if not 1 <= len(layers) <= MAX_LAYERS:
        raise ValueError('layer count must be between 1 and 8')
    for i, layer in enumerate(layers):
        _dict(layer, MAX_LAYER, 'layer %d' % i)
    _dict(actual, MAX_ACTUAL, 'actual')
    merged = {}
    source = {}
    overridden = 0
    for i, layer in enumerate(layers):
        for k, v in layer.items():
            if k in merged:
                overridden += 1
            merged[k] = v
            source[k] = i
    keys = sorted(merged)
    for k in keys:
        if any(other.startswith(k + '.') for other in keys):
            raise ValueError('key conflicts with a longer key: ' + k)
    missing = [k for k in keys if k not in actual]
    extra = sorted(k for k in actual if k not in merged)
    changed = [k for k in keys if k in actual and actual[k] != merged[k]]
    return {'merged': [(k, merged[k]) for k in keys], 'source': [(k, source[k]) for k in keys],
            'overridden': overridden, 'missing': missing, 'extra': extra, 'changed': changed,
            'in_sync': not (missing or extra or changed)}
