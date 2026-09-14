"""Configuration loaded from environment variables — never hardcoded.

Swapping providers (currently Groq, free-tier) for an org's own
OpenAI-compatible endpoint in production is a config change (LLM_BASE_URL +
LLM_API_KEY + LLM_MODEL), not a code change.
"""

import os

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    # python-dotenv is a convenience for local live runs; tests and CI never
    # need it, so its absence must not break anything.
    pass

LLM_BASE_URL = os.environ.get("LLM_BASE_URL", "https://api.groq.com/openai/v1")
LLM_API_KEY = os.environ.get("LLM_API_KEY")
LLM_MODEL = os.environ.get("LLM_MODEL", "openai/gpt-oss-120b")

READING_LEVEL_MAX_GRADE = float(os.environ.get("READING_LEVEL_MAX_GRADE", "6"))
