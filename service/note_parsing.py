"""Deterministic parsing of the one piece of note structure we rely on: a
leading "PATIENT: <name>" header, as seen in every fixtures/note_*.txt.

This is intentionally narrow — not general note parsing. It exists only to
extract a first name for a conversational greeting, and returns None rather
than guessing when the expected header isn't there.
"""

import re
from typing import Optional

_PATIENT_LINE_RE = re.compile(r"^PATIENT:\s*(\S+)", re.MULTILINE)


def extract_patient_first_name(note_text: str) -> Optional[str]:
    match = _PATIENT_LINE_RE.search(note_text)
    if not match:
        return None
    return match.group(1)
