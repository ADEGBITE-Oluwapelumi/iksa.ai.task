"""A deterministic, network-free Summarizer used by every test.

StubSummarizer is deliberately dumb: it returns whatever SummarizerOutput it
was constructed with. "Deliberately bad" drafts (invented dose, dropped
red-flag, unmapped advice, ...) are produced by callers — see
tests/factories.py — not by branching logic inside this class.
"""

from service.models import SummarizerOutput
from service.summarizer.base import Summarizer


class StubSummarizer(Summarizer):
    name = "stub"

    def __init__(self, canned_output: SummarizerOutput):
        self._canned_output = canned_output

    def summarize(self, note_text: str) -> SummarizerOutput:
        return self._canned_output
