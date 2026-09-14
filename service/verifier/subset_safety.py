"""Acceptance criterion 2 — subset safety.

No medication, dose, frequency, or instruction may appear in the draft that
isn't present in the source note. This module never calls a model: it checks
each claim's structured fields (and any day/week/month count mentioned in
instruction/red-flag claim text) against the specific note span that claim
cites as its evidence.

This deliberately does NOT diff arbitrary draft prose against the note —
plain-language rewording (e.g. "HOMA-IR" -> "how well your body handles
blood sugar") legitimately shares no words with its source, so a bag-of-words
overlap check would produce false failures on exactly the simplification the
feature exists to do. Structured fields sidestep that.
"""

import re
from typing import List, Set, Tuple

from service.models import CheckResult, ClaimType, SummarizerOutput

CHECK_NAME = "subset_safety"

# Fixture notes write time periods both ways ("30 days", "RTC 30d") and
# ("RTC day-30", "F/U day-30") — both must normalize to the same token so a
# plain-language rewording in either direction doesn't look like a mismatch.
_FORWARD_RE = re.compile(
    r"\b(\d+)\s*-?\s*(day|days|d|week|weeks|wk|month|months|mo)\b", re.IGNORECASE
)
_REVERSE_RE = re.compile(
    r"\b(day|days|week|weeks|month|months)\s*-\s*(\d+)\b", re.IGNORECASE
)

_UNIT_ALIASES = {
    "day": "day", "days": "day", "d": "day",
    "week": "week", "weeks": "week", "wk": "week",
    "month": "month", "months": "month", "mo": "month",
}


def _normalize(text: str) -> str:
    return re.sub(r"\s+", "", text.lower())


def _contains_normalized(haystack: str, needle: str) -> bool:
    return _normalize(needle) in _normalize(haystack)


def _time_periods(text: str) -> Set[Tuple[str, str]]:
    periods = set()
    for match in _FORWARD_RE.finditer(text):
        periods.add((match.group(1), _UNIT_ALIASES[match.group(2).lower()]))
    for match in _REVERSE_RE.finditer(text):
        periods.add((match.group(2), _UNIT_ALIASES[match.group(1).lower()]))
    return periods


def check(note_text: str, output: SummarizerOutput) -> CheckResult:
    details: List[str] = []

    for claim in output.claims:
        if claim.evidence is None:
            # Absence of evidence is the evidence-trail check's job to flag;
            # subset safety can't verify a claim against a span that doesn't
            # exist.
            continue

        source = claim.evidence.quote

        if claim.claim_type == ClaimType.MEDICATION:
            if claim.drug_name and not _contains_normalized(source, claim.drug_name):
                details.append(
                    f"medication '{claim.drug_name}' not found in its cited "
                    f"source span: {source!r}"
                )
            if claim.dose and not _contains_normalized(source, claim.dose):
                details.append(
                    f"dose '{claim.dose}' for '{claim.drug_name}' not found in "
                    f"its cited source span: {source!r}"
                )
            if claim.frequency and not _contains_normalized(source, claim.frequency):
                details.append(
                    f"frequency '{claim.frequency}' for '{claim.drug_name}' not "
                    f"found in its cited source span: {source!r}"
                )
        else:
            claim_periods = _time_periods(claim.text)
            source_periods = _time_periods(source)
            for number, unit in claim_periods - source_periods:
                details.append(
                    f"claim {claim.text!r} states a time period ({number} "
                    f"{unit}) not found in its cited source span: {source!r}"
                )

    return CheckResult(name=CHECK_NAME, passed=not details, details=details)
