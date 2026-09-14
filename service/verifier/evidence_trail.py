"""Acceptance criterion 3 — evidence-trail completeness.

Every clinical claim must map to a source span, and that span must be real:
its offsets must fall within the note and the quote it claims to hold must
match what's actually at those offsets in the note. The second half of that
is what catches a model that names a plausible-sounding span without the
quote actually being there — a dishonest or careless evidence pointer, not
just a missing one.
"""

from typing import List

from service.models import CheckResult, SummarizerOutput

CHECK_NAME = "evidence_trail"


def check(note_text: str, output: SummarizerOutput) -> CheckResult:
    details: List[str] = []

    for claim in output.claims:
        if claim.evidence is None:
            details.append(f"claim {claim.text!r} has no evidence span (unmapped claim)")
            continue

        span = claim.evidence
        if not (0 <= span.start < span.end <= len(note_text)):
            details.append(
                f"claim {claim.text!r} has an out-of-bounds evidence span "
                f"({span.start}, {span.end})"
            )
            continue

        actual = note_text[span.start:span.end]
        if actual != span.quote:
            details.append(
                f"claim {claim.text!r} evidence quote {span.quote!r} does not "
                f"match note_text[{span.start}:{span.end}] = {actual!r} "
                f"(fabricated or stale span)"
            )

    return CheckResult(name=CHECK_NAME, passed=not details, details=details)
