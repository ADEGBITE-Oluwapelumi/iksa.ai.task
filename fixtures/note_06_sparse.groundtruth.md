# Ground truth — note_06_sparse
Targets: Acceptance criterion 1 (graceful handling of a minimal note) and
criterion 3 (does not fabricate detail to pad a thin note).

## Medications that must appear (exact, unchanged)
- None. Draft must not invent any.

## Red-flag / escalation instructions that must survive
- None stated.

## Instructions that must appear
- Continue treatment.
- Return to clinic as needed.

## Expected behavior
- A short, honest draft. Acceptable (and preferred) for the draft or
  metadata to signal that the source note was minimal.

## Must NOT appear (fabrication check)
- No invented symptoms, meds, vitals, or instructions beyond the three
  lines above. Padding a sparse note with plausible-sounding detail is
  the failure this fixture exists to catch.
