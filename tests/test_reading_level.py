from service.verifier import reading_level
from tests import factories


def test_plain_language_draft_passes_reading_level(note_04_text):
    output = factories.clean_output_note_04(note_04_text)
    result = reading_level.check(note_04_text, output)
    assert result.passed, result.details


def test_jargon_verbatim_draft_fails_reading_level(note_04_text):
    output = factories.jargon_output_note_04(note_04_text)
    result = reading_level.check(note_04_text, output)
    assert not result.passed
    assert result.details
