"""Row 682, Ports and Adapters (PARTIAL: one exact wiring rule): check that ports have adapters on one side and the core uses them.

check_wiring(ports, adapters, core_ports) takes ports as a list of port names, adapters as a list of (adapter, port, side)
where side is 'driving' (the outside calls the core through the port) or 'driven' (the core calls the outside through the
port), and core_ports as a list of the ports the core declares it uses. It returns:
  problems  sorted (port, code) with code one of
            'no_adapter'      the port has no adapter;
            'mixed_sides'     its adapters are not all on one side;
            'not_in_core'     no entry in core_ports names the port.
Rules in plain words: every port needs at least one adapter, all adapters of one port sit on one side, and every port is
named by the core.
Caps: 1 to 16 ports with unique names, 0 to 32 adapters with unique names, 0 to 16 core_ports without repeats. Every adapter
port and every core_ports entry must be one of ports. Names are 1 to 24 lowercase identifier characters.
Order of checks: ports (list type, count, then each in order: name type and shape), duplicate port, adapters (list type, count,
then each in order: tuple type, 3 items, adapter name type and shape, port name type and shape, side type and value),
duplicate adapter, unknown port in adapters (in order), core_ports (list type, count, then each name type and shape), repeated
entry, unknown port in core_ports (in order), and only then the analysis.

NOT_CLAIMED: this checks a supplied wiring table. It does not read code, say that the ports are the right ones, or say that
an adapter does what its port needs. No clinical or wet-lab claim.
"""
import re

LABEL = re.compile(r'[a-z][a-z0-9_]{0,23}\Z')


def _name(v):
    if type(v) is not str:
        raise TypeError('name must be an exact string')
    if LABEL.fullmatch(v) is None:
        raise ValueError('name must be 1 to 24 lowercase identifier characters')


def check_wiring(ports, adapters, core_ports):
    if type(ports) is not list:
        raise TypeError('ports must be an exact list')
    if not 1 <= len(ports) <= 16:
        raise ValueError('port count must be between 1 and 16')
    for p in ports:
        _name(p)
    if len(set(ports)) != len(ports):
        raise ValueError('duplicate port')
    if type(adapters) is not list:
        raise TypeError('adapters must be an exact list')
    if len(adapters) > 32:
        raise ValueError('adapter count must be at most 32')
    for a in adapters:
        if type(a) is not tuple:
            raise TypeError('each adapter must be an exact tuple')
        if len(a) != 3:
            raise ValueError('each adapter must have 3 items')
        _name(a[0])
        _name(a[1])
        if type(a[2]) is not str:
            raise TypeError('side must be an exact string')
        if a[2] not in ('driving', 'driven'):
            raise ValueError("side must be 'driving' or 'driven'")
    if len({a[0] for a in adapters}) != len(adapters):
        raise ValueError('duplicate adapter')
    for a in adapters:
        if a[1] not in ports:
            raise ValueError('unknown port: ' + a[1])
    if type(core_ports) is not list:
        raise TypeError('core_ports must be an exact list')
    if len(core_ports) > 16:
        raise ValueError('core_ports count must be at most 16')
    for c in core_ports:
        _name(c)
    if len(set(core_ports)) != len(core_ports):
        raise ValueError('repeated core port')
    for c in core_ports:
        if c not in ports:
            raise ValueError('unknown port: ' + c)
    problems = []
    for p in ports:
        sides = {s for _, q, s in adapters if q == p}
        if not sides:
            problems.append((p, 'no_adapter'))
        elif len(sides) > 1:
            problems.append((p, 'mixed_sides'))
        if p not in core_ports:
            problems.append((p, 'not_in_core'))
    return {'problems': sorted(problems)}
