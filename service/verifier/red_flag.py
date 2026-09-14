"""Acceptance criterion 4 — red-flag / escalation retention.

Detects safety-critical escalation language in the SOURCE note (keyword
based — see the "Known limitations" note in the README: a production
version needs a more robust clinical-escalation classifier, not a keyword
list) and checks that every such instruction is covered by a draft claim
whose evidence overlaps it, and — for emergency-tier language specifically —
that the draft claim's own wording still carries the urgency, rather than
being downgraded to something like "contact your provider".
"""

import re
from typing import List, Tuple

from service.models import CheckResult, SummarizerOutput

CHECK_NAME = "red_flag_retention"

EMERGENCY_KEYWORDS = [
    "go to the er",
    "emergency room",
    "emergency department",
    "call 911",
    "immediately",
    "do not wait",
]

URGENT_KEYWORDS = [
    "call clinic",
    "call the clinic",
    "contact clinic",
    "call your provider",
]


def _pattern_for(keyword: str) -> re.Pattern:
    escaped = re.escape(keyword)
    flexible = escaped.replace(r"\ ", r"\s+")
    return re.compile(flexible, re.IGNORECASE | re.DOTALL)


def _find_keyword_spans(text: str, keywords: List[str]) -> List[Tuple[int, int, str]]:
    spans = []
    for keyword in keywords:
        for match in _pattern_for(keyword).finditer(text):
            spans.append((match.start(), match.end(), keyword))
    return spans


def _text_contains_any(text: str, keywords: List[str]) -> bool:
    return any(_pattern_for(keyword).search(text) for keyword in keywords)


def _overlaps(a_start: int, a_end: int, b_start: int, b_end: int) -> bool:
    return a_start < b_end and b_start < a_end


def check(note_text: str, output: SummarizerOutput) -> CheckResult:
    details: List[str] = []

    for start, end, keyword in _find_keyword_spans(note_text, EMERGENCY_KEYWORDS):
        covering = [
            claim
            for claim in output.claims
            if claim.evidence and _overlaps(claim.evidence.start, claim.evidence.end, start, end)
        ]
        if not covering:
            details.append(
                f"emergency-level instruction ({keyword!r} at note[{start}:{end}]) "
                f"has no covering claim in the draft"
            )
        elif not any(_text_contains_any(claim.text, EMERGENCY_KEYWORDS) for claim in covering):
            details.append(
                f"emergency-level instruction ({keyword!r}) is covered but its "
                f"urgency was downgraded in the draft: "
                f"{[claim.text for claim in covering]!r}"
            )

    for start, end, keyword in _find_keyword_spans(note_text, URGENT_KEYWORDS):
        covering = [
            claim
            for claim in output.claims
            if claim.evidence and _overlaps(claim.evidence.start, claim.evidence.end, start, end)
        ]
        if not covering:
            details.append(
                f"urgent instruction ({keyword!r} at note[{start}:{end}]) has no "
                f"covering claim in the draft"
            )

    return CheckResult(name=CHECK_NAME, passed=not details, details=details)
