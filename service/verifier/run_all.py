from typing import List

from service.models import CheckResult, SummarizerOutput
from service.verifier import evidence_trail, reading_level, red_flag, subset_safety


def run_all(note_text: str, output: SummarizerOutput) -> List[CheckResult]:
    return [
        subset_safety.check(note_text, output),
        evidence_trail.check(note_text, output),
        red_flag.check(note_text, output),
        reading_level.check(note_text, output),
    ]
