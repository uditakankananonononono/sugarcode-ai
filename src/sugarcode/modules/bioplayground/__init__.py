"""Wright-Fisher population-genetics sandbox: drift, selection, mutation and bottleneck shocks on a multi-allele construct locus."""
from .core import *
from .core import __dict__ as _d
__all__=[k for k,v in _d.items() if not k.startswith('_') and callable(v)]
