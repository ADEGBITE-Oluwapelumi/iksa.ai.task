from service.models import ClaimType, ClinicalClaim, EvidenceSpan, SummarizerOutput
from service.verifier import evidence_trail

NOTE = "P: - Continue current peptide regimen, no changes.\n   - RTC day-30 for scheduled review.\n"


def test_correctly_mapped_claim_passes():
    quote = "Continue current peptide regimen, no changes."
    start = NOTE.index(quote)
    claim = ClinicalClaim(
        text="Keep taking your current treatment.",
        claim_type=ClaimType.INSTRUCTION,
        evidence=EvidenceSpan(start=start, end=start + len(quote), quote=quote),
    )
    result = evidence_trail.check(NOTE, SummarizerOutput(draft_summary=claim.text, claims=[claim]))
    assert result.passed, result.details


def test_unmapped_claim_fails():
    claim = ClinicalClaim(
        text="Try smaller, more frequent meals.",
        claim_type=ClaimType.INSTRUCTION,
        evidence=None,
    )
    result = evidence_trail.check(NOTE, SummarizerOutput(draft_summary=claim.text, claims=[claim]))
    assert not result.passed
    assert "unmapped" in result.details[0]


def test_fabricated_span_fails_even_though_evidence_is_present():
    """The dishonest-model case: a claim carries an evidence span with valid,
    in-bounds offsets and a plausible-looking quote — but the quote does not
    actually match what's at those offsets in the note. This must fail
    independent of how the draft was assembled, proving the check inspects
    the note itself rather than trusting the claim's own say-so.
    """
    start = NOTE.index("RTC day-30 for scheduled review.")
    claim = ClinicalClaim(
        text="Take ibuprofen 400 mg for pain.",
        claim_type=ClaimType.MEDICATION,
        evidence=EvidenceSpan(
            start=start,
            end=start + len("RTC day-30 for scheduled review."),
            quote="Take ibuprofen 400 mg for pain as needed.",
        ),
    )
    result = evidence_trail.check(NOTE, SummarizerOutput(draft_summary=claim.text, claims=[claim]))
    assert not result.passed
    assert "does not match" in result.details[0]


def test_out_of_bounds_span_fails():
    claim = ClinicalClaim(
        text="Some claim.",
        claim_type=ClaimType.OTHER_CLINICAL,
        evidence=EvidenceSpan(start=len(NOTE) - 2, end=len(NOTE) + 50, quote="won't matter"),
    )
    result = evidence_trail.check(NOTE, SummarizerOutput(draft_summary=claim.text, claims=[claim]))
    assert not result.passed
    assert "out-of-bounds" in result.details[0]
