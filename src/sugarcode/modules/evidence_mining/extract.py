"""Regex extraction from source text. Heuristic: it does not report only values
explicitly stated.

sample_size is the largest regex match anywhere in the text, so counts from
earlier trials can be picked up. effect_direction is set by keyword matching on
the first sentence that contains one, whether or not that sentence reports the
study's own result."""
from __future__ import annotations
import re
from .models import MISSING

_NUM = r"(\d{1,3}(?:,\d{3})+|\d{1,8})"  # "3,649" is one number, not 3
_SAMPLE_PATTERNS = [
    re.compile(r"\b(?:n\s*=\s*|enrolled\s+|included\s+|randomi[sz]ed\s+)" + _NUM + r"\b", re.I),
    re.compile(r"\b" + _NUM + r"\s+(?:patients|participants|subjects|individuals|adults|children)\b", re.I),
]
_ENDPOINT = re.compile(r"(?:primary|secondary)\s+(?:outcome|endpoint)s?\s*(?:was|were|:)?\s*([^.;]{3,180})", re.I)
_SENTENCES = re.compile(r"(?<=[.!?])\s+")
_POSITIVE = re.compile(r"\b(?:significantly\s+)?(?:improved|increased|higher|superior|benefit(?:ed)?|reduced|decreased|lower)\b", re.I)
_NULL = re.compile(r"\b(?:no significant (?:difference|change)|did not (?:improve|increase|reduce|decrease)|non[- ]significant)\b", re.I)
_NEGATIVE = re.compile(r"\b(?:worsened|inferior|increased (?:risk|mortality|adverse)|higher (?:risk|mortality|adverse))\b", re.I)


def extract_text_evidence(text: str) -> dict:
    compact = " ".join((text or "").split())
    sizes = [int(m.group(1).replace(",", "")) for p in _SAMPLE_PATTERNS for m in p.finditer(compact)]
    endpoints = []
    for m in _ENDPOINT.finditer(compact):
        endpoint = m.group(1).strip(" :-")
        if endpoint and endpoint.casefold() not in {x.casefold() for x in endpoints}:
            endpoints.append(endpoint)
    effect_direction, effect_text = MISSING, MISSING
    for sentence in _SENTENCES.split(compact):
        if _NULL.search(sentence):
            effect_direction, effect_text = "no_difference", sentence
            break
        if _NEGATIVE.search(sentence):
            effect_direction, effect_text = "negative", sentence
            break
        if _POSITIVE.search(sentence):
            effect_direction, effect_text = "stated_effect", sentence
            break
    return {"sample_size": max(sizes) if sizes else MISSING,
            "endpoints": endpoints, "effect_direction": effect_direction,
            "effect_text": effect_text}
