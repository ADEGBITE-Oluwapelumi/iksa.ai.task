# Fixtures — fabricated physician notes for testing

These are invented physician notes used to test the note-to-summary
service. No real patient data is involved anywhere; all names, MRNs,
dates, and clinical details are fabricated.

Each note has a companion `*.groundtruth.md` file: a human-readable
checklist of what a correct patient-facing draft must contain, must
preserve (e.g. red-flag instructions), and must NOT contain (fabrications).
The automated tests assert the draft against these checklists.

## Coverage — each note targets an acceptance criterion
- note_01_happy_path  — valid payload, simple case (criterion 1)
- note_02_multi_med   — subset safety: no invented/altered doses (crit 2)
- note_03_red_flag    — safety-critical instructions survive (crit 4)
- note_04_dense_jargon— grade-8 reading level from a technical note (crit 5;
  originally grade-6 per issue #1, raised after live testing)
- note_05_ambiguity   — no "over-helpful" hallucinated advice (crit 3)
- note_06_sparse      — no fabrication to pad a thin note (crit 1, 3)

## Caveat (read before relying on these)
The notes follow standard SOAP clinical-documentation conventions. The
note STRUCTURE is authentic. The longevity-clinic clinical specifics
(peptides, hormone protocols, doses, IV therapies) are fabricated for
plausibility and are NOT drawn from real longevity-clinic documentation,
which is not well represented in public sources. Validating against real
de-identified notes from the clinic is a next step, not done here.
