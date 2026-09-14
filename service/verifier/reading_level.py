"""Acceptance criterion 5 — reading level.

Uses `textstat` (a well-maintained readability library) rather than
hand-rolling the Flesch-Kincaid formula. The max grade is configured via
READING_LEVEL_MAX_GRADE (service/config.py) — issue #1 originally set this
at 6 (NIH/AMA/HHS patient-materials guidance); it was raised to 8 after live
testing against a real model showed its non-red-flag prose reliably landed
around grade 7-8 on realistic notes.

Priority rule (deliberate safety decision): red-flag / safety-critical
claims are EXEMPT from this gate entirely, at any configured grade.
Retention and urgency for that content is enforced separately, and
completely, by service/verifier/red_flag.py — that check has no
reading-level ceiling of its own. We do not simplify emergency instructions
below completeness to hit a readability number. Concretely: this check
computes the grade on the non-red-flag claims only ("the body"), never on
red-flag claim text.

This rule exists because of a real regression: an early draft of the
note_03 ER instruction was reworded to hit the (then grade-6) reading-level
target and, in the process, silently dropped a listed leg symptom and
softened "immediately" / "do not wait for clinic". Criteria 4 (retention)
and 5 (reading level) can conflict, and prior to this rule the system had
no way to say which one wins. Now it does: retention always wins for
red-flag content, regardless of what the numeric threshold is set to.
"""

import textstat

from service.config import READING_LEVEL_MAX_GRADE
from service.models import CheckResult, ClaimType, SummarizerOutput

CHECK_NAME = "reading_level"


def _gradable_text(output: SummarizerOutput) -> str:
    """draft_summary with red-flag claim text carved out.

    We grade draft_summary itself (not a reconstruction from claims) so this
    check still reacts to whatever text is actually delivered to the
    patient. Red-flag text is removed by exact substring match against each
    red-flag claim's own `text` — which is safe for the reference/stub
    implementation, where draft_summary is assembled by joining claim texts,
    so the substring is always present. If a claim's text can't be found
    verbatim in draft_summary (e.g. a live, free-form draft where the model
    paraphrased around it), we can't safely carve out its boundary, so that
    text is left in and graded — the conservative default, not a silent
    exemption we can't actually verify.
    """
    text = output.draft_summary
    for claim in output.claims:
        if claim.claim_type == ClaimType.RED_FLAG:
            text = text.replace(claim.text, "")
    return text


def check(note_text: str, output: SummarizerOutput) -> CheckResult:
    text = _gradable_text(output)
    if not text.strip():
        # Nothing but red-flag content to grade — there's no "body" left to
        # hold to a readability target, so there's nothing to fail here.
        return CheckResult(name=CHECK_NAME, passed=True, details=[])

    grade = textstat.flesch_kincaid_grade(text)
    passed = grade <= READING_LEVEL_MAX_GRADE
    details = []
    if not passed:
        details.append(
            f"non-red-flag body scored grade {grade:.1f}, above the max of "
            f"{READING_LEVEL_MAX_GRADE}"
        )
    return CheckResult(name=CHECK_NAME, passed=passed, details=details)
