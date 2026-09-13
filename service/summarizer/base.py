"""The swappable model interface.

Everything downstream (orchestrator, verifier) depends only on this
interface, never on a specific provider.
"""

from abc import ABC, abstractmethod

from service.models import SummarizerOutput


class Summarizer(ABC):
    name: str = "summarizer"

    @abstractmethod
    def summarize(self, note_text: str) -> SummarizerOutput:
        """Turn a physician note into a draft summary + evidence-mapped claims."""
        raise NotImplementedError
