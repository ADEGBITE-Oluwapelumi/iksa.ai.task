from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures"


def _load(name: str) -> str:
    return (FIXTURES_DIR / name).read_text()


@pytest.fixture
def note_01_text() -> str:
    return _load("note_01_happy_path.txt")


@pytest.fixture
def note_02_text() -> str:
    return _load("note_02_multi_med.txt")


@pytest.fixture
def note_03_text() -> str:
    return _load("note_03_red_flag.txt")


@pytest.fixture
def note_04_text() -> str:
    return _load("note_04_dense_jargon.txt")


@pytest.fixture
def note_05_text() -> str:
    return _load("note_05_ambiguity.txt")


@pytest.fixture
def note_06_text() -> str:
    return _load("note_06_sparse.txt")
