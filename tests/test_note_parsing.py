from service.note_parsing import extract_patient_first_name


def test_extracts_first_name_from_standard_header(note_02_text):
    assert extract_patient_first_name(note_02_text) == "Marcus"


def test_extracts_first_token_even_for_an_initial(note_06_text):
    # "PATIENT: R. Kim" — honest edge case, not worth special-casing.
    assert extract_patient_first_name(note_06_text) == "R."


def test_returns_none_when_no_patient_header_present():
    assert extract_patient_first_name("No header here, just clinical text.") is None
