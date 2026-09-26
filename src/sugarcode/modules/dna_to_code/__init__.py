"""Educational mapper: molecular-biology concepts (transcription, translation, regulation) explained as executable code analogies."""
from .core import *
from .core import __dict__ as _d
__all__=[k for k,v in _d.items() if not k.startswith('_') and (callable(v) or k=='CONCEPTS')]
