"""Configuration loaded from environment variables — never hardcoded.

Swapping GitHub Models (free/prototyping) for an org's own OpenAI-compatible
endpoint in production is a config change (base_url + api_key + model), not
a code change.
"""

import os

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    # python-dotenv is a convenience for local live runs; tests and CI never
    # need it, so its absence must not break anything.
    pass

GITHUB_MODELS_BASE_URL = os.environ.get(
    "GITHUB_MODELS_BASE_URL", "https://models.github.ai/inference"
)
GITHUB_MODELS_TOKEN = os.environ.get("GITHUB_MODELS_TOKEN")
GITHUB_MODELS_MODEL = os.environ.get("GITHUB_MODELS_MODEL", "openai/gpt-4o-mini")

READING_LEVEL_MAX_GRADE = float(os.environ.get("READING_LEVEL_MAX_GRADE", "6"))
