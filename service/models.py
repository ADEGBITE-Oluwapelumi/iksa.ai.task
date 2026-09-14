"""Data contracts shared by the summarizer and verifier layers.

Design note: evidence is keyed by *claim*, not by character offsets into the
draft. Only clinical content becomes a ClinicalClaim (connective prose like a
greeting doesn't need one). This lets the verifier do exact, deterministic
checks instead of needing sentence segmentation / NLP to map arbitrary draft
prose back onto claims. See README "Known limitations" for the tradeoff this
implies for the evidence-trail check.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class ClaimType(str, Enum):
    MEDICATION = "medication"
    INSTRUCTION = "instruction"
    RED_FLAG = "red_flag"
    OTHER_CLINICAL = "other_clinical"


@dataclass(frozen=True)
class EvidenceSpan:
    """A pointer into the source note text.

    `quote` is stored redundantly (rather than re-sliced from the note on
    demand) so the evidence-trail check can independently verify that
    note_text[start:end] == quote — catching a span whose offsets don't
    actually match its claimed quote.
    """

    start: int
    end: int
    quote: str

    def to_dict(self) -> Dict[str, Any]:
        return {"start": self.start, "end": self.end, "quote": self.quote}


@dataclass
class ClinicalClaim:
    """One clinical statement in the draft, mapped to its source evidence."""

    text: str
    claim_type: ClaimType
    evidence: Optional[EvidenceSpan]
    drug_name: Optional[str] = None
    dose: Optional[str] = None
    frequency: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "claim_type": self.claim_type.value,
            "evidence": self.evidence.to_dict() if self.evidence else None,
            "drug_name": self.drug_name,
            "dose": self.dose,
            "frequency": self.frequency,
        }


@dataclass
class SummarizerOutput:
    """What a Summarizer implementation returns."""

    draft_summary: str
    claims: List[ClinicalClaim] = field(default_factory=list)


@dataclass
class CheckResult:
    """The result of one deterministic verifier check."""

    name: str
    passed: bool
    details: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {"name": self.name, "passed": self.passed, "details": self.details}
