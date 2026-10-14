"""Row 671, Domain-Driven Design (PARTIAL: one exact layering rule): check module dependencies against the DDD layers.

check_layers(modules, dependencies) takes the modules of a design, each with the layer it sits in, and the dependencies
between them. modules is a list of (name, layer), layer one of 'domain', 'application', 'infrastructure', 'interface'.
dependencies is a list of (user, used): module `user` uses module `used`. The rule: a layer may use only these layers:
  domain          domain;
  application     application, domain;
  infrastructure  infrastructure, application, domain;
  interface       interface, application, domain.
It returns:
  violations  sorted (user, used, code) for each dependency that breaks the rule, code '<layer of user>_uses_<layer of used>';
  cycles      sorted names of modules that lie on a dependency cycle (a module that can reach itself by one or more
              dependencies), whatever their layers; a module that uses itself is on a cycle;
  by_layer    {layer: sorted module names} for all four layers (empty list when none).
Caps: 1 to 32 modules with unique lowercase identifier names of 1 to 24 characters; 0 to 96 dependencies, no duplicates, every
name among the modules.
Order of checks: modules (list type, count, then each in order: tuple type, 2 items, name type and shape, layer type and value),
then duplicate names, then dependencies (list type, count, then each in order: tuple type, 2 items, user name type and shape,
used name type and shape), then duplicate dependencies, then unknown names (user before used, in dependency order), and only
then the analysis.

NOT_CLAIMED: this checks a supplied table of layers and dependencies. It does not read code, say that the layers or boundaries
are the right ones, model any business, or say that a design without violations is good design. No clinical or wet-lab claim.
"""
import re

LABEL = re.compile(r'[a-z][a-z0-9_]{0,23}\Z')
LAYERS = ('domain', 'application', 'infrastructure', 'interface')
ALLOWED = {'domain': ('domain',), 'application': ('application', 'domain'),
           'infrastructure': ('infrastructure', 'application', 'domain'),
           'interface': ('interface', 'application', 'domain')}


def _name(v):
    if type(v) is not str:
        raise TypeError('name must be an exact string')
    if LABEL.fullmatch(v) is None:
        raise ValueError('name must be 1 to 24 lowercase identifier characters')


def check_layers(modules, dependencies):
    if type(modules) is not list:
        raise TypeError('modules must be an exact list')
    if not 1 <= len(modules) <= 32:
        raise ValueError('module count must be between 1 and 32')
    for m in modules:
        if type(m) is not tuple:
            raise TypeError('each module must be an exact tuple')
        if len(m) != 2:
            raise ValueError('each module must have 2 items')
        _name(m[0])
        if type(m[1]) is not str:
            raise TypeError('layer must be an exact string')
        if m[1] not in LAYERS:
            raise ValueError("layer must be 'domain', 'application', 'infrastructure' or 'interface'")
    layer = dict(modules)
    if len(layer) != len(modules):
        raise ValueError('duplicate module name')
    if type(dependencies) is not list:
        raise TypeError('dependencies must be an exact list')
    if len(dependencies) > 96:
        raise ValueError('dependency count must be at most 96')
    for d in dependencies:
        if type(d) is not tuple:
            raise TypeError('each dependency must be an exact tuple')
        if len(d) != 2:
            raise ValueError('each dependency must have 2 items')
        _name(d[0])
        _name(d[1])
    if len(set(dependencies)) != len(dependencies):
        raise ValueError('duplicate dependency')
    for user, used in dependencies:
        if user not in layer:
            raise ValueError('unknown module: ' + user)
        if used not in layer:
            raise ValueError('unknown module: ' + used)
    violations = sorted((u, v, layer[u] + '_uses_' + layer[v]) for u, v in dependencies
                        if layer[v] not in ALLOWED[layer[u]])
    out = {n: sorted({v for u, v in dependencies if u == n}) for n in layer}
    cyc = []
    for n in layer:
        seen = set()
        todo = list(out[n])
        while todo:
            x = todo.pop()
            if x not in seen:
                seen.add(x)
                todo.extend(out[x])
        if n in seen:
            cyc.append(n)
    return {'violations': violations, 'cycles': sorted(cyc),
            'by_layer': {l: sorted(n for n in layer if layer[n] == l) for l in LAYERS}}
