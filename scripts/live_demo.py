#!/usr/bin/env python3
"""Minimal manual harness: run the real (OpenAI-compatible) summarizer
against a note file and print the resulting payload. Not used by tests or
CI — needs LLM_API_KEY set (see .env.example).

Usage:
    python scripts/live_demo.py fixtures/note_02_multi_med.txt
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from service.orchestrator import generate_summary
from service.summarizer.openai_compatible import OpenAICompatibleSummarizer


def main() -> None:
    if len(sys.argv) != 2:
        print(f"usage: {sys.argv[0]} <path-to-note.txt>", file=sys.stderr)
        sys.exit(1)

    note_text = Path(sys.argv[1]).read_text()
    summarizer = OpenAICompatibleSummarizer()
    payload = generate_summary(note_text, summarizer)
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
