"""End-to-end tests through the orchestrator, using StubSummarizer against
the real fixture notes. These are the tests the issue (#1) asks for
directly: a clean draft passes and is release-ready, and each of the three
documented failure modes is caught and blocks release.
"""

from service.orchestrator import generate_summary
from service.summarizer.stub import StubSummarizer
from tests import factories


def _checks_by_name(payload):
    return {c["name"]: c for c in payload["metadata"]["checks"]}


def test_clean_draft_passes_all_checks_and_is_release_ready(note_02_text):
    summarizer = StubSummarizer(factories.clean_output_note_02(note_02_text))
    payload = generate_summary(note_02_text, summarizer)

    checks = _checks_by_name(payload)
    assert all(c["passed"] for c in checks.values()), checks
    assert payload["metadata"]["release_ready"] is True
    assert payload["draft_summary"]
    assert payload["evidence_map"]


def test_invented_dose_fails_subset_safety_and_blocks_release(note_02_text):
    summarizer = StubSummarizer(factories.invented_dose_output_note_02(note_02_text))
    payload = generate_summary(note_02_text, summarizer)

    checks = _checks_by_name(payload)
    assert checks["subset_safety"]["passed"] is False
    assert payload["metadata"]["release_ready"] is False


def test_invented_medication_fails_subset_safety_and_blocks_release(note_02_text):
    summarizer = StubSummarizer(factories.invented_medication_output_note_02(note_02_text))
    payload = generate_summary(note_02_text, summarizer)

    checks = _checks_by_name(payload)
    assert checks["subset_safety"]["passed"] is False
    assert payload["metadata"]["release_ready"] is False


def test_dropped_red_flag_fails_and_blocks_release(note_03_text):
    summarizer = StubSummarizer(factories.dropped_red_flag_output_note_03(note_03_text))
    payload = generate_summary(note_03_text, summarizer)

    checks = _checks_by_name(payload)
    assert checks["red_flag_retention"]["passed"] is False
    assert payload["metadata"]["release_ready"] is False


def test_downgraded_red_flag_fails_and_blocks_release(note_03_text):
    summarizer = StubSummarizer(factories.downgraded_red_flag_output_note_03(note_03_text))
    payload = generate_summary(note_03_text, summarizer)

    checks = _checks_by_name(payload)
    assert checks["red_flag_retention"]["passed"] is False
    assert payload["metadata"]["release_ready"] is False


def test_unmapped_advice_fails_evidence_trail_and_blocks_release(note_05_text):
    summarizer = StubSummarizer(factories.unmapped_advice_output_note_05(note_05_text))
    payload = generate_summary(note_05_text, summarizer)

    checks = _checks_by_name(payload)
    assert checks["evidence_trail"]["passed"] is False
    assert payload["metadata"]["release_ready"] is False


def test_metadata_includes_timing_measurement(note_01_text):
    summarizer = StubSummarizer(factories.clean_output_note_01(note_01_text))
    payload = generate_summary(note_01_text, summarizer)

    assert "timing_ms" in payload["metadata"]
    assert payload["metadata"]["timing_ms"] >= 0


def test_all_clean_fixtures_pass(note_01_text, note_02_text, note_03_text, note_05_text):
    cases = [
        (note_01_text, factories.clean_output_note_01),
        (note_02_text, factories.clean_output_note_02),
        (note_03_text, factories.clean_output_note_03),
        (note_05_text, factories.clean_output_note_05),
    ]
    for note_text, builder in cases:
        summarizer = StubSummarizer(builder(note_text))
        payload = generate_summary(note_text, summarizer)
        assert payload["metadata"]["release_ready"] is True, payload["metadata"]["checks"]
