"""Row 957, Thermal Metamaterials (PARTIAL: one exact heat-flow rule).

Each supplied device is checked with two heat-flow bars:
- 'leaky' when insulation_layers < 2
- 'unrouted' when channels < 1

NOT_CLAIMED: this checks supplied device numbers against two heat-flow bars. It does not say heat is controlled, that 2 layers or 1 channel are the right bars, or that any device works. No clinical or wet-lab claim.
"""
import re

LABEL = re.compile(r'[a-z][a-z0-9_]{0,23}\Z')


def check_devices(devices):
    if type(devices) is not list:
        raise TypeError('devices must be an exact list')
    if len(devices) > 40:
        raise ValueError('device count must be at most 40')
    problems = []
    for i, item in enumerate(devices):
        if type(item) is not tuple:
            raise TypeError('each device must be an exact tuple')
        if len(item) != 3:
            raise ValueError('each device must have 3 items')
        name, insulation_layers, channels = item
        if type(name) is not str:
            raise TypeError('device must be an exact string')
        if not LABEL.fullmatch(name):
            raise ValueError('device must be 1 to 24 lowercase identifier characters')
        for field, value, high in (('insulation_layers', insulation_layers, 100), ('channels', channels, 100)):
            if type(value) is not int:
                raise TypeError(field + ' must be an exact integer')
            if not 0 <= value <= high:
                raise ValueError(field + ' must be 0 to ' + str(high))
        if insulation_layers < 2:
            problems.append((i, 'leaky'))
        if channels < 1:
            problems.append((i, 'unrouted'))
    return {'problems': sorted(problems),
            'devices': sorted({x[0] for x in devices}),
            'total': len(devices)}
