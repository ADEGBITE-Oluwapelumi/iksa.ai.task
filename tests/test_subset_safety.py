from service.models import ClaimType, ClinicalClaim, EvidenceSpan, SummarizerOutput
from service.verifier import subset_safety

NOTE = "P: - Semaglutide 0.5 mg SC weekly.\n   - RTC 30d for titration review.\n"


def _med_claim(text, drug_name, dose, frequency, quote):
    start = NOTE.index(quote)
    return ClinicalClaim(
        text=text,
        claim_type=ClaimType.MEDICATION,
        evidence=EvidenceSpan(start=start, end=start + len(quote), quote=quote),
        drug_name=drug_name,
        dose=dose,
        frequency=frequency,
    )


def test_dose_matching_the_source_span_passes():
    claim = _med_claim(
        "You're taking semaglutide 0.5 mg once a week.",
        "Semaglutide", "0.5 mg", "weekly",
        "Semaglutide 0.5 mg SC weekly.",
    )
    result = subset_safety.check(NOTE, SummarizerOutput(draft_summary=claim.text, claims=[claim]))
    assert result.passed, result.details


def test_altered_dose_fails():
    """The dose in the claim doesn't match the dose in its own cited span."""
    claim = _med_claim(
        "You're taking semaglutide 2 mg once a week.",
        "Semaglutide", "2 mg", "weekly",
        "Semaglutide 0.5 mg SC weekly.",
    )
    result = subset_safety.check(NOTE, SummarizerOutput(draft_summary=claim.text, claims=[claim]))
    assert not result.passed
    assert any("dose" in detail for detail in result.details)


def test_invented_medication_fails():
    """The claim cites a REAL span from the note, but names a drug that
    isn't in that span (or anywhere in the note) at all — not merely an
    altered dose, but a wholesale invented medication. This is the case
    fixtures/note_02_multi_med.groundtruth.md calls out: "No medication
    added that isn't listed above."
    """
    claim = _med_claim(
        "You're also taking ibuprofen 200 mg as needed for pain.",
        "ibuprofen", "200 mg", "as needed",
        "RTC 30d for titration review.",
    )
    result = subset_safety.check(NOTE, SummarizerOutput(draft_summary=claim.text, claims=[claim]))
    assert not result.passed
    assert any("ibuprofen" in detail for detail in result.details)


def test_instruction_time_period_matching_source_passes():
    quote = "RTC 30d for titration review."
    start = NOTE.index(quote)
    claim = ClinicalClaim(
        text="Come back to the clinic in 30 days for a dose check.",
        claim_type=ClaimType.INSTRUCTION,
        evidence=EvidenceSpan(start=start, end=start + len(quote), quote=quote),
    )
    result = subset_safety.check(NOTE, SummarizerOutput(draft_summary=claim.text, claims=[claim]))
    assert result.passed, result.details


def test_instruction_time_period_not_in_source_fails():
    quote = "RTC 30d for titration review."
    start = NOTE.index(quote)
    claim = ClinicalClaim(
        text="Come back to the clinic in 60 days for a dose check.",
        claim_type=ClaimType.INSTRUCTION,
        evidence=EvidenceSpan(start=start, end=start + len(quote), quote=quote),
    )
    result = subset_safety.check(NOTE, SummarizerOutput(draft_summary=claim.text, claims=[claim]))
    assert not result.passed


def test_claim_without_evidence_is_skipped_not_double_counted():
    """Evidence-trail owns flagging unmapped claims; subset_safety should not
    also try (and fail) to verify a claim that has no span to check against.
    """
    claim = ClinicalClaim(
        text="Take something unmapped.",
        claim_type=ClaimType.MEDICATION,
        evidence=None,
        drug_name="something",
        dose="1 mg",
        frequency="daily",
    )
    result = subset_safety.check(NOTE, SummarizerOutput(draft_summary=claim.text, claims=[claim]))
    assert result.passed
