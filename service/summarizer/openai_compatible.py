"""The real implementation: any OpenAI-compatible chat-completions endpoint.

Not tied to one provider — configured entirely via LLM_BASE_URL / LLM_API_KEY
/ LLM_MODEL (service/config.py). .env.example ships Groq's free-tier values
as the default for prototyping; production would point this at the org's own
OpenAI-compatible endpoint by changing those three values — no code change.

This class is used only by scripts/live_demo.py for manual runs. It is never
imported by the test suite: tests must not call a live model or require a
key.
"""

import json
from typing import Any, Dict, List, Optional

from openai import OpenAI

from service import config
from service.models import ClaimType, ClinicalClaim, EvidenceSpan, SummarizerOutput
from service.note_parsing import extract_patient_first_name
from service.summarizer.base import Summarizer

SYSTEM_PROMPT = """You turn a physician's clinical note into a patient-facing, \
plain-language summary (6th-grade reading level or below).

Respond with ONLY a JSON object of this exact shape:
{
  "draft_summary": "<the full patient-facing summary, plain language>",
  "claims": [
    {
      "text": "<the plain-language claim, as it appears in draft_summary>",
      "claim_type": "medication" | "instruction" | "red_flag" | "other_clinical",
      "source_quote": "<verbatim substring copied from the note that supports this claim>",
      "drug_name": "<only for medication claims, else null>",
      "dose": "<only for medication claims, e.g. '0.5 mg', else null>",
      "frequency": "<only for medication claims, e.g. 'weekly', else null>"
    }
  ]
}

Rules:
- Every clinical claim (medication, instruction, red-flag/escalation, or other
  clinical fact) must have a "source_quote" copied VERBATIM from the note —
  do not paraphrase the quote, only the "text".
- Never state a medication, dose, frequency, or instruction that is not in
  the note.
- Any safety-critical / escalation instruction in the note (e.g. "go to the
  ER if...") must appear in a red_flag claim with its urgency intact.
- Do not include claims for non-clinical filler (greetings, sign-offs).
"""


def _resolve_span(note_text: str, quote: Optional[str]) -> Optional[EvidenceSpan]:
    """Locate a model-provided quote in the note text.

    Tries an exact match first, then a whitespace-normalized match. If the
    quote can't be located, returns None — the evidence-trail check will then
    correctly fail this claim closed, rather than us guessing at an offset.
    """
    if not quote:
        return None

    start = note_text.find(quote)
    if start != -1:
        return EvidenceSpan(start=start, end=start + len(quote), quote=quote)

    normalized_quote = " ".join(quote.split())
    normalized_note = " ".join(note_text.split())
    idx = normalized_note.find(normalized_quote)
    if idx == -1:
        return None

    # Best-effort mapping back from the normalized note to real offsets: walk
    # the original text counting non-whitespace-collapsed characters until we
    # cover `idx` characters of normalized text, then take len(normalized_quote)
    # more from there. This is approximate for note_text containing irregular
    # whitespace, which is exactly why exact-match is tried first.
    count = 0
    real_start = None
    for i, ch in enumerate(note_text):
        if real_start is None and count >= idx:
            real_start = i
        if not ch.isspace() or (i > 0 and not note_text[i - 1].isspace()):
            count += 1
    if real_start is None:
        return None
    real_end = min(len(note_text), real_start + len(normalized_quote))
    return EvidenceSpan(start=real_start, end=real_end, quote=note_text[real_start:real_end])


class OpenAICompatibleSummarizer(Summarizer):
    name = "openai-compatible"

    def __init__(self) -> None:
        if not config.LLM_API_KEY:
            raise RuntimeError(
                "LLM_API_KEY is not set. Copy .env.example to .env and fill in "
                "an API key for your chosen provider."
            )
        self._client = OpenAI(
            base_url=config.LLM_BASE_URL,
            api_key=config.LLM_API_KEY,
        )

    def summarize(self, note_text: str) -> SummarizerOutput:
        user_content = note_text
        patient_first_name = extract_patient_first_name(note_text)
        if patient_first_name:
            user_content += (
                f"\n\n(The patient's first name is {patient_first_name}. Open "
                f"draft_summary with a brief, warm greeting using this name, "
                f"e.g. 'Hi {patient_first_name}, ...'. The greeting itself is "
                f"not a clinical claim and needs no source_quote.)"
            )

        response = self._client.chat.completions.create(
            model=config.LLM_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
            response_format={"type": "json_object"},
            temperature=0,
        )
        payload: Dict[str, Any] = json.loads(response.choices[0].message.content)

        claims: List[ClinicalClaim] = []
        for raw_claim in payload.get("claims", []):
            evidence = _resolve_span(note_text, raw_claim.get("source_quote"))
            claims.append(
                ClinicalClaim(
                    text=raw_claim.get("text", ""),
                    claim_type=ClaimType(raw_claim.get("claim_type", "other_clinical")),
                    evidence=evidence,
                    drug_name=raw_claim.get("drug_name"),
                    dose=raw_claim.get("dose"),
                    frequency=raw_claim.get("frequency"),
                )
            )

        return SummarizerOutput(
            draft_summary=payload.get("draft_summary", ""),
            claims=claims,
        )
