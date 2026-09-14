"""Fail-closed orchestration: summarizer -> verifier -> payload.

If ANY verifier check fails, release_ready is False and metadata names the
failing checks. The draft is still returned (so a reviewer can see and fix
it) but is explicitly not presented as ready-to-send.
"""

import time
from typing import Any, Dict

from service.models import SummarizerOutput
from service.summarizer.base import Summarizer
from service.verifier import run_all


def generate_summary(note_text: str, summarizer: Summarizer) -> Dict[str, Any]:
    start = time.perf_counter()
    output: SummarizerOutput = summarizer.summarize(note_text)
    timing_ms = (time.perf_counter() - start) * 1000

    results = run_all(note_text, output)
    release_ready = all(result.passed for result in results)

    return {
        "draft_summary": output.draft_summary,
        "evidence_map": [claim.to_dict() for claim in output.claims],
        "metadata": {
            "checks": [result.to_dict() for result in results],
            "release_ready": release_ready,
            "timing_ms": timing_ms,
            "summarizer": summarizer.name,
        },
    }
