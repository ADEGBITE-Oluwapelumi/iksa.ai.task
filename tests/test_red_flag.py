from service.models import ClaimType, ClinicalClaim, EvidenceSpan, SummarizerOutput
from service.verifier import red_flag
from tests import factories

NOTE = (
    "P: - Continue protocol as prescribed.\n"
    "   - RETURN PRECAUTIONS: go to the ER immediately if chest pain.\n"
    "   - Call clinic during hours for persistent headache.\n"
)


def _claim(text, quote, claim_type=ClaimType.RED_FLAG):
    start = NOTE.index(quote)
    return ClinicalClaim(
        text=text,
        claim_type=claim_type,
        evidence=EvidenceSpan(start=start, end=start + len(quote), quote=quote),
    )


def test_retained_emergency_and_urgent_instructions_pass():
    claims = [
        _claim(
            "Go to the ER right away if you have chest pain.",
            "go to the ER immediately if chest pain.",
        ),
        _claim(
            "Call the clinic during office hours for a headache that won't go away.",
            "Call clinic during hours for persistent headache.",
        ),
    ]
    result = red_flag.check(NOTE, SummarizerOutput(draft_summary=" ".join(c.text for c in claims), claims=claims))
    assert result.passed, result.details


def test_dropped_emergency_instruction_fails():
    """No claim at all covers the ER-level instruction."""
    claims = [
        _claim(
            "Call the clinic during office hours for a headache that won't go away.",
            "Call clinic during hours for persistent headache.",
        ),
    ]
    result = red_flag.check(NOTE, SummarizerOutput(draft_summary=claims[0].text, claims=claims))
    assert not result.passed
    assert any("emergency-level" in d for d in result.details)


def test_downgraded_emergency_instruction_fails():
    """A claim covers the ER-level instruction's source span, but its
    wording no longer carries emergency urgency — it reads like routine
    advice. Must fail even though the span IS covered.
    """
    claims = [
        _claim(
            "If you have chest pain, please contact your provider.",
            "go to the ER immediately if chest pain.",
        ),
        _claim(
            "Call the clinic during office hours for a headache that won't go away.",
            "Call clinic during hours for persistent headache.",
        ),
    ]
    result = red_flag.check(NOTE, SummarizerOutput(draft_summary=" ".join(c.text for c in claims), claims=claims))
    assert not result.passed
    assert any("downgraded" in d for d in result.details)


def test_dropped_urgent_instruction_fails():
    claims = [
        _claim(
            "Go to the ER right away if you have chest pain.",
            "go to the ER immediately if chest pain.",
        ),
    ]
    result = red_flag.check(NOTE, SummarizerOutput(draft_summary=claims[0].text, claims=claims))
    assert not result.passed
    assert any("urgent instruction" in d for d in result.details)


def test_note_03_er_claim_retains_every_symptom_and_full_urgency(note_03_text):
    """Regression test for a real incident: an earlier draft of this claim,
    rewritten to hit the grade-6 reading-level target, silently dropped the
    leg "pain"/"warmth" symptoms and softened "immediately"/"do not wait for
    clinic". Retention must never lose to reading level for red-flag
    content (see service/verifier/reading_level.py's exemption for exactly
    this reason) — this test pins the fixture's claim text so that class of
    regression can't happen again unnoticed.
    """
    output = factories.clean_output_note_03(note_03_text)
    er_claims = [c for c in output.claims if c.claim_type == ClaimType.RED_FLAG and "ER" in c.text]
    assert len(er_claims) == 1
    text = er_claims[0].text.lower()

    # Every symptom concept from the note must survive (plain-language
    # rewording of "shortness of breath" is fine; dropping it is not).
    assert "trouble breathing" in text or "shortness of breath" in text
    assert "chest pain" in text
    assert "swelling" in text
    assert "warmth" in text
    assert "redness" in text
    assert "one leg" in text
    # "pain" must appear a second time beyond "chest pain" — i.e. leg pain
    # is still listed, not just chest pain.
    assert text.count("pain") >= 2

    # Full urgency, not softened.
    assert "immediately" in text or "right away" in text
    assert "do not wait for clinic" in text
    assert "go to the er" in text
