"""Builders for canned SummarizerOutput objects, used by StubSummarizer in
tests. Each builder is anchored to a real fixture note in fixtures/, so a
"clean" output is a faithful plain-language rendering of that note and a
"corrupted" output is a deliberate, documented mutation of a clean one.

Evidence spans are located by slicing the exact fixture text between two
markers (find_span), rather than hand-transcribing whitespace/newlines —
fixture notes wrap lines mid-quote, so this avoids spans that are subtly
wrong.
"""

from typing import List, Optional

from service.models import ClaimType, ClinicalClaim, EvidenceSpan, SummarizerOutput
from service.note_parsing import extract_patient_first_name


def find_span(note_text: str, start_marker: str, end_marker: Optional[str] = None) -> EvidenceSpan:
    start = note_text.index(start_marker)
    if end_marker is None:
        end = start + len(start_marker)
    else:
        end = note_text.index(end_marker, start) + len(end_marker)
    return EvidenceSpan(start=start, end=end, quote=note_text[start:end])


def _assemble_draft(note_text: str, claims: List[ClinicalClaim]) -> str:
    """Join claim text into a draft, prefixed with a conversational greeting.

    The greeting is plain connective prose, not a clinical claim — it has no
    evidence span and doesn't belong in evidence_map, same as any other
    non-clinical filler (see service/models.py's design note).
    """
    parts = []
    name = extract_patient_first_name(note_text)
    if name:
        parts.append(f"Hi {name}, here's a quick summary from your visit.")
    parts.extend(claim.text for claim in claims)
    return " ".join(parts)


# ---------------------------------------------------------------------------
# note_01_happy_path — clean
# ---------------------------------------------------------------------------

def clean_output_note_01(note_text: str) -> SummarizerOutput:
    claims = [
        ClinicalClaim(
            text="You're doing well one week after treatment, with no new problems.",
            claim_type=ClaimType.OTHER_CLINICAL,
            evidence=find_span(note_text, "Tolerating protocol well at day 7. No adverse effects noted."),
        ),
        ClinicalClaim(
            text="Keep taking your current treatment with no changes.",
            claim_type=ClaimType.INSTRUCTION,
            evidence=find_span(note_text, "Continue current peptide regimen, no changes."),
        ),
        ClinicalClaim(
            text="Come back to the clinic in 30 days for your next check-in.",
            claim_type=ClaimType.INSTRUCTION,
            evidence=find_span(note_text, "RTC day-30 for scheduled review."),
        ),
    ]
    return SummarizerOutput(draft_summary=_assemble_draft(note_text, claims), claims=claims)


# ---------------------------------------------------------------------------
# note_02_multi_med — clean, plus corrupted variants
# ---------------------------------------------------------------------------

def clean_output_note_02(note_text: str) -> SummarizerOutput:
    claims = [
        ClinicalClaim(
            text="You're taking semaglutide, 0.5 mg, as a shot under the skin once a week.",
            claim_type=ClaimType.MEDICATION,
            evidence=find_span(note_text, "Semaglutide 0.5 mg SC weekly"),
            drug_name="Semaglutide",
            dose="0.5 mg",
            frequency="weekly",
        ),
        ClinicalClaim(
            text=(
                "After 4 weeks, if you're tolerating it well, your dose may be "
                "increased to 1 mg weekly."
            ),
            claim_type=ClaimType.MEDICATION,
            evidence=find_span(
                note_text, "Semaglutide 0.5 mg SC weekly; titrate to 1 mg weekly after", "4 weeks if tolerated."
            ),
            drug_name="Semaglutide",
            dose="1 mg",
            frequency="weekly",
        ),
        ClinicalClaim(
            text="You're also getting NAD+ by IV, 500 mg, once a month.",
            claim_type=ClaimType.MEDICATION,
            evidence=find_span(note_text, "NAD+ IV 500 mg, monthly."),
            drug_name="NAD+",
            dose="500 mg",
            frequency="monthly",
        ),
        ClinicalClaim(
            text="Take vitamin D3, 5000 IU, by mouth every day.",
            claim_type=ClaimType.MEDICATION,
            evidence=find_span(note_text, "Vitamin D3 5000 IU PO daily."),
            drug_name="Vitamin D3",
            dose="5000 IU",
            frequency="daily",
        ),
        ClinicalClaim(
            text="Keep taking magnesium glycinate, 400 mg, by mouth at bedtime.",
            claim_type=ClaimType.MEDICATION,
            evidence=find_span(note_text, "Continue magnesium glycinate 400 mg PO qHS."),
            drug_name="magnesium glycinate",
            dose="400 mg",
            frequency="qHS",
        ),
        ClinicalClaim(
            text="Come back to the clinic in 30 days to review your dose.",
            claim_type=ClaimType.INSTRUCTION,
            evidence=find_span(note_text, "RTC 30d for titration review."),
        ),
    ]
    return SummarizerOutput(draft_summary=_assemble_draft(note_text, claims), claims=claims)


def invented_dose_output_note_02(note_text: str) -> SummarizerOutput:
    """Same as clean, but the semaglutide starting dose is altered to 2 mg —
    the note says 0.5 mg. Tests that subset_safety catches an ALTERED dose.
    """
    output = clean_output_note_02(note_text)
    output.claims[0] = ClinicalClaim(
        text="You're taking semaglutide, 2 mg, as a shot under the skin once a week.",
        claim_type=ClaimType.MEDICATION,
        evidence=output.claims[0].evidence,
        drug_name="Semaglutide",
        dose="2 mg",
        frequency="weekly",
    )
    output.draft_summary = _assemble_draft(note_text, output.claims)
    return output


def invented_medication_output_note_02(note_text: str) -> SummarizerOutput:
    """Same as clean, but with an extra medication claim for a drug that
    never appears in the note at all — citing a real span (the magnesium
    line) as if it supported it. Tests that subset_safety catches an
    INVENTED medication, not just an altered dose.
    """
    output = clean_output_note_02(note_text)
    fabricated = ClinicalClaim(
        text="You're also starting ibuprofen 200 mg by mouth as needed for pain.",
        claim_type=ClaimType.MEDICATION,
        evidence=find_span(note_text, "Continue magnesium glycinate 400 mg PO qHS."),
        drug_name="ibuprofen",
        dose="200 mg",
        frequency="as needed",
    )
    output.claims = output.claims + [fabricated]
    output.draft_summary = _assemble_draft(note_text, output.claims)
    return output


# ---------------------------------------------------------------------------
# note_03_red_flag — clean, plus dropped-red-flag variant
# ---------------------------------------------------------------------------

def clean_output_note_03(note_text: str) -> SummarizerOutput:
    claims = [
        ClinicalClaim(
            text="Keep following your treatment plan as your doctor prescribed.",
            claim_type=ClaimType.INSTRUCTION,
            evidence=find_span(note_text, "Continue protocol as prescribed."),
        ),
        ClinicalClaim(
            text=(
                "Go to the ER immediately if you have sudden trouble "
                "breathing, chest pain, or new swelling, pain, warmth, or "
                "redness in one leg. Do not wait for clinic."
            ),
            claim_type=ClaimType.RED_FLAG,
            evidence=find_span(
                note_text, "go to the ER", "swelling, pain, warmth, or redness in one leg"
            ),
        ),
        ClinicalClaim(
            text=(
                "Call the clinic during office hours if you get a headache "
                "that does not get better with your usual medicine. Also "
                "call if the skin around your shot starts to turn red and "
                "the redness is spreading, or if it feels warm, leaks pus, "
                "or if you get a fever."
            ),
            claim_type=ClaimType.RED_FLAG,
            evidence=find_span(
                note_text,
                "Call clinic during hours for",
                "(spreading redness, warmth, pus, fever).",
            ),
        ),
        ClinicalClaim(
            text="Come back to the clinic in 7 days.",
            claim_type=ClaimType.INSTRUCTION,
            evidence=find_span(note_text, "RTC day-7."),
        ),
    ]
    return SummarizerOutput(draft_summary=_assemble_draft(note_text, claims), claims=claims)


def dropped_red_flag_output_note_03(note_text: str) -> SummarizerOutput:
    """Same as clean, but the ER-level red-flag claim is removed entirely.
    Tests that red_flag retention catches a DROPPED escalation instruction.
    """
    output = clean_output_note_03(note_text)
    output.claims = [c for c in output.claims if c.claim_type != ClaimType.RED_FLAG or "ER" not in c.text]
    output.draft_summary = _assemble_draft(note_text, output.claims)
    return output


def downgraded_red_flag_output_note_03(note_text: str) -> SummarizerOutput:
    """Same as clean, but the ER claim's wording is softened to something
    that no longer reads as an emergency. Tests that red_flag retention
    catches an escalation instruction that survives but loses its urgency.
    """
    output = clean_output_note_03(note_text)
    for i, claim in enumerate(output.claims):
        if claim.claim_type == ClaimType.RED_FLAG and "ER" in claim.text:
            output.claims[i] = ClinicalClaim(
                text=(
                    "If you have shortness of breath, chest pain, or leg "
                    "swelling, please contact your provider."
                ),
                claim_type=ClaimType.RED_FLAG,
                evidence=claim.evidence,
            )
    output.draft_summary = _assemble_draft(note_text, output.claims)
    return output


# ---------------------------------------------------------------------------
# note_04_dense_jargon — clean (plain language) and a jargon-verbatim variant
# ---------------------------------------------------------------------------

def clean_output_note_04(note_text: str) -> SummarizerOutput:
    claims = [
        ClinicalClaim(
            text="Your body is handling blood sugar better than before.",
            claim_type=ClaimType.OTHER_CLINICAL,
            evidence=find_span(note_text, "Fasting insulin decreased. HOMA-IR improved 3.1 -> 1.9."),
        ),
        ClinicalClaim(
            text="Your average blood sugar level over the past few months looks good.",
            claim_type=ClaimType.OTHER_CLINICAL,
            evidence=find_span(note_text, "HbA1c 5.4%."),
        ),
        ClinicalClaim(
            text="A marker of body inflammation is going down, which is a good sign.",
            claim_type=ClaimType.OTHER_CLINICAL,
            evidence=find_span(
                note_text, "hsCRP trending down", "inflammation)."
            ),
        ),
        ClinicalClaim(
            text="Keep taking metformin, 500 mg, by mouth twice a day.",
            claim_type=ClaimType.MEDICATION,
            evidence=find_span(note_text, "Continue metformin 500 mg PO BID."),
            drug_name="metformin",
            dose="500 mg",
            frequency="BID",
        ),
        ClinicalClaim(
            text="Keep up your eating plan and strength training.",
            claim_type=ClaimType.INSTRUCTION,
            evidence=find_span(
                note_text,
                "Reinforce continued caloric periodization and resistance",
                "training.",
            ),
        ),
        ClinicalClaim(
            text="Come back in 90 days to repeat your labs.",
            claim_type=ClaimType.INSTRUCTION,
            evidence=find_span(note_text, "RTC 90d with repeat labs."),
        ),
    ]
    return SummarizerOutput(draft_summary=_assemble_draft(note_text, claims), claims=claims)


def jargon_output_note_04(note_text: str) -> SummarizerOutput:
    """Same claims/evidence as clean, but draft_summary dumps the technical
    language verbatim instead of the plain-language claim text. Tests that
    the reading-level check actually fails on jargon rather than always
    passing.
    """
    output = clean_output_note_04(note_text)
    output.draft_summary = (
        "Fasting insulin decreased. HOMA-IR improved 3.1 -> 1.9. HbA1c 5.4%. "
        "hsCRP trending down, suggesting reduced systemic inflammation. "
        "Continue metformin 500 mg PO BID. Reinforce continued caloric "
        "periodization and resistance training. RTC 90d with repeat labs."
    )
    return output


# ---------------------------------------------------------------------------
# note_05_ambiguity — clean, plus unmapped-advice variant
# ---------------------------------------------------------------------------

def clean_output_note_05(note_text: str) -> SummarizerOutput:
    claims = [
        ClinicalClaim(
            text="Keep taking your current treatment without any changes.",
            claim_type=ClaimType.INSTRUCTION,
            evidence=find_span(note_text, "Continue current regimen unchanged."),
        ),
        ClinicalClaim(
            text="Keep an eye on your stomach symptoms.",
            claim_type=ClaimType.INSTRUCTION,
            evidence=find_span(note_text, "Monitor symptoms."),
        ),
        ClinicalClaim(
            text="Follow up in 30 days, or sooner if it gets worse.",
            claim_type=ClaimType.INSTRUCTION,
            evidence=find_span(note_text, "F/U day-30 (sooner if worsening)."),
        ),
    ]
    return SummarizerOutput(draft_summary=_assemble_draft(note_text, claims), claims=claims)


def unmapped_advice_output_note_05(note_text: str) -> SummarizerOutput:
    """Same as clean, but with an extra "helpful" claim that has no source
    evidence at all — the tempting fabrication this fixture exists to catch
    (see fixtures/note_05_ambiguity.groundtruth.md). Tests that
    evidence_trail catches an UNMAPPED clinical claim.
    """
    output = clean_output_note_05(note_text)
    fabricated = ClinicalClaim(
        text="Try eating smaller, more frequent meals to help with the stomach upset.",
        claim_type=ClaimType.INSTRUCTION,
        evidence=None,
    )
    output.claims = output.claims + [fabricated]
    output.draft_summary = _assemble_draft(note_text, output.claims)
    return output
