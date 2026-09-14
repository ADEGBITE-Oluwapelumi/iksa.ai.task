# iksa.ai.task

Work-sample project. See [DECISION.md](DECISION.md) for the scope decision
and [issue #1](https://github.com/ADEGBITE-Oluwapelumi/iksa.ai.task/issues/1)
for the acceptance criteria this build targets.

## What this is

A backend service that takes a physician note (plain text) and returns
`{ draft_summary, evidence_map, metadata }`: a patient-ready plain-language
summary, a source-mapped evidence trail for every clinical claim in it, and
verification metadata (pass/fail per safety check, a release-readiness
flag, and a timing measurement). See `service/` for the code:

- `service/summarizer/` — the swappable model interface (`Summarizer`), a
  `StubSummarizer` (canned, deterministic, used by all tests) and an
  `OpenAICompatibleSummarizer` (real, used only for manual live runs — works
  against any OpenAI-compatible endpoint, not tied to one provider).
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

## Running a live example (optional, needs an API key)

```
cp .env.example .env
# edit .env: fill in LLM_API_KEY (a free key from console.groq.com/keys)
python scripts/live_demo.py fixtures/note_02_multi_med.txt
```

The live provider is currently [Groq](https://console.groq.com) (free tier,
no credit card) — used here for prototyping. `OpenAICompatibleSummarizer`
isn't tied to Groq: it works against any OpenAI-compatible chat-completions
endpoint. In production, `LLM_BASE_URL` / `LLM_API_KEY` / `LLM_MODEL` would
point at the org's own endpoint instead — a config change, not a code
change. This path is not exercised by any test.

## Known limitations / outstanding work

- **Evidence-trail coverage is only proven end-to-end on the claim-based
  path, not on arbitrary free-form prose.** The reference summarizer
  assembles `draft_summary` directly from its own verified claims, so on
  the CI-tested path it's structurally impossible to produce a clinical
  sentence in the draft that isn't backed by a claim — the "unmapped
  claim" failure mode is real (see `tests/test_evidence_trail.py`), but
  it's exercised as "a claim explicitly has no evidence," not as "the
  model wrote a free sentence no claim accounts for." Only the live path
  (`OpenAICompatibleSummarizer`, source-quote resolution) faces a model
  that produces free-form prose; that path isn't covered by CI. Verifying
  arbitrary prose against source spans — sentence segmentation + claim
  classification — is a documented next step, not attempted here.
- **Red-flag detection is keyword-based.** `service/verifier/red_flag.py`
  matches a fixed list of emergency/urgent phrases. It will miss
  escalation language phrased outside that vocabulary and could
  false-positive on incidental uses of a keyword. Production needs a more
  robust clinical-escalation classifier, not a keyword list.
- **Reading level: the live model doesn't reliably hit grade 6.** Live runs
  against note_03 scored grade 7.4-8.1 on non-red-flag content; note_02
  passed at grade 6. The target stays at 6 (NIH/AMA/HHS standard for
  patient materials) — the check fails closed and reports the actual score
  when a draft exceeds it, rather than the target being lowered to match
  current model output. Closing this gap (better prompting, a stronger
  model, or a simplification pass) is outstanding.
- **`source_quote` truncation on the live path.** In at least one live run,
  the model returned a `source_quote` that was cut off mid-word. Since a
  truncated quote is still a valid (if incomplete) substring of the note,
  `evidence_trail` passed it — the check verifies a span is honest, not
  that it's *sufficient* to support the whole claim. Not reproducible on
  the CI/stub path, where spans are hand-built.
- **Claim-type misclassification can bypass subset-safety's dose check.**
  Observed live on note_02: a claim carrying `dose`/`frequency` fields was
  tagged `claim_type: "instruction"` instead of `"medication"`.
  `subset_safety.py` only validates those fields when `claim_type ==
  MEDICATION` — a misclassified medication claim's dose isn't checked at
  all. Not reproducible on the CI/stub path, where `tests/factories.py`
  always sets the type correctly by construction.
- **Live-model evaluation at scale is outstanding.** The model is stubbed
  in CI; there's no automated eval of the real `OpenAICompatibleSummarizer`
  path against the fixture set or a larger corpus.
- **A self-correcting retry agent was scoped but deliberately not built.**
  Feasibility was assessed (bounded retries, fail-to-human escalation,
  attempt logging, no cross-attempt regression) and the conclusion was to
  defer it: its core mechanism (feedback-conditioned regeneration) is
  live-model-dependent and can't be validated the way the rest of this
  build is, and reading-level feedback specifically risks reintroducing
  the red-flag content-dropping regression this PR already fixed once.
- **Baseline/delta measurement is a separate effort.** This build emits
  the per-summary timing measurement (`metadata.timing_ms`) so median
  time-to-summary is trackable in real use, but establishing the
  hand-authoring baseline and the before/after comparison is a later
  evaluation with the clinic (see issue #1), not part of this PR.
