# iksa.ai.task

Work-sample project. See [DECISION.md](DECISION.md) for the scope decision
and [issue #1](../../issues/1) for the acceptance criteria this build
targets.

## What this is

A backend service that takes a physician note (plain text) and returns
`{ draft_summary, evidence_map, metadata }`: a patient-ready plain-language
summary, a source-mapped evidence trail for every clinical claim in it, and
verification metadata (pass/fail per safety check, a release-readiness
flag, and a timing measurement). See `service/` for the code:

- `service/summarizer/` — the swappable model interface (`Summarizer`), a
  `StubSummarizer` (canned, deterministic, used by all tests) and a
  `GitHubModelsSummarizer` (real, used only for manual live runs).
- `service/verifier/` — four deterministic, model-free checks: subset
  safety, evidence-trail completeness, red-flag retention, reading level.
- `service/orchestrator.py` — runs summarizer → verifier → payload,
  fail-closed: any failing check sets `release_ready: false` and names the
  failing checks, but the draft is still returned for a reviewer to see.

## Running the tests (no key needed)

```
pip install -r requirements.txt
pytest
```

All tests use `StubSummarizer` against the real notes in `fixtures/` —
no network calls, no secrets, safe to run in CI.

## Running a live example (optional, needs a GitHub PAT)

```
cp .env.example .env
# edit .env: fill in GITHUB_MODELS_TOKEN (a PAT with the "models" permission)
python scripts/live_demo.py fixtures/note_02_multi_med.txt
```

GitHub Models (`https://models.github.ai/inference`) is free/prototyping-only
and rate-limited. In production, `GITHUB_MODELS_BASE_URL` /
`GITHUB_MODELS_TOKEN` / `GITHUB_MODELS_MODEL` would point at the org's own
OpenAI-compatible endpoint instead — a config change, not a code change.
This path is not exercised by any test.

## Known limitations / outstanding work

- **Evidence-trail coverage is only proven end-to-end on the claim-based
  path, not on arbitrary free-form prose.** The reference summarizer
  assembles `draft_summary` directly from its own verified claims, so on
  the CI-tested path it's structurally impossible to produce a clinical
  sentence in the draft that isn't backed by a claim — the "unmapped
  claim" failure mode is real (see `tests/test_evidence_trail.py`), but
  it's exercised as "a claim explicitly has no evidence," not as "the
  model wrote a free sentence no claim accounts for." Only the live path
  (`GitHubModelsSummarizer`, source-quote resolution) faces a model that
  produces free-form prose; that path isn't covered by CI. Verifying
  arbitrary prose against source spans — sentence segmentation + claim
  classification — is a documented next step, not attempted here.
- **Red-flag detection is keyword-based.** `service/verifier/red_flag.py`
  matches a fixed list of emergency/urgent phrases. It will miss
  escalation language phrased outside that vocabulary and could
  false-positive on incidental uses of a keyword. Production needs a more
  robust clinical-escalation classifier, not a keyword list.
- **Live-model evaluation at scale is outstanding.** The model is stubbed
  in CI; there's no automated eval of the real `GitHubModelsSummarizer`
  path against the fixture set or a larger corpus.
- **Baseline/delta measurement is a separate effort.** This build emits
  the per-summary timing measurement (`metadata.timing_ms`) so median
  time-to-summary is trackable in real use, but establishing the
  hand-authoring baseline and the before/after comparison is a later
  evaluation with the clinic (see issue #1), not part of this PR.
