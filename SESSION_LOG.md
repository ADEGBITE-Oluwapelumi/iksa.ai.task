# Session log — how this build was driven

This is the real prompt history for this repo's build, in chronological order: the actual instruction given at each step, and what was done in response. It is not a summary written from memory after the fact — each entry is the real prompt (or a faithful version of it).

Where a prompt pasted a large block of content that is already committed verbatim elsewhere in this repo (the DECISION.md text, the 13 fixture files, full issue/PR bodies), that block is elided here with a pointer to where it actually lives, rather than duplicated a second time. Everything else — instructions, constraints, corrections, my own responses and admissions — is kept in full, including the corrections where I got something wrong. Typos in the original prompts are left as typed.

---

### Phase 1 — Setup: decision doc + issue

**Prompt:**
> We're starting a work-sample project. This first task is setup only — do NOT write any application code yet. Two deliverables.
>
> TASK 1 — Commit DECISION.md on a branch: fresh repo, no commits yet — make an initial commit first if needed. Create and check out branch `docs/decision-and-issue`. Create `DECISION.md` at the repo root with the exact content below, verbatim. Commit it with a clear message.
>
> TASK 2 — Open the GitHub issue: using `gh`, create an issue with the title and body below. Report back the issue number and URL.
>
> Do not push to main. Do not open a PR yet. Do not scaffold any Python. Stop after the issue is created and tell me the issue number.
>
> [full verbatim DECISION.md content pasted here — see DECISION.md]
> [full verbatim issue title + body pasted here — see issue #1]

**Did:** Made the initial commit (repo had none), created `docs/decision-and-issue`, committed `DECISION.md` verbatim, opened issue #1 via `gh issue create`. Did not push to main, did not open a PR, wrote no Python.

---

### Phase 2 — Re-sync on the issue after a manual edit

**Prompt:**
> I edited the GitHub issue directly on GitHub after you created it. Before we build, fetch the current issue so you're working from the real version, not your earlier draft. Run: `gh issue view <NUMBER> --json title,body --jq '.title, .body'` — and read it back to me in your own words so I can confirm you've got the current acceptance criteria. Don't start building yet.

**Did:** Fetched the live issue body, summarized what had changed (the metric section was reframed into "instrumentation now, baseline/delta later," and a new acceptance criterion 6 — a timing measurement — was added, making 7 total). No code written.

---

### Phase 3 — Test fixtures

**Prompt:**
> Next task: add test fixtures to the repo. Still no application code — this is fixtures only. Make sure you're on the build branch — create and check out `feat/note-to-summary` off the docs branch. Create a `fixtures/` folder. Create the 13 files I'll paste below, each with exact content, verbatim — do not improve, reword, or reformat any of them. Commit them with a clear message referencing the issue (but do not close it). List the files after committing so I can confirm all 13 are present. Do not write the service, tests, or CI yet.
>
> [13 files pasted verbatim: 6 note_*.txt, 6 *.groundtruth.md, fixtures/README.md — see fixtures/]

**Did:** Created `feat/note-to-summary` off `docs/decision-and-issue`, wrote all 13 fixture files byte-for-byte as given, committed referencing #1 without closing it, listed the 13 files to confirm.

---

### Phase 4 — Build plan, held for approval

**Prompt:**
> Now the main build. Read this whole spec before writing anything, then tell me your implementation plan (files, key functions, how the stub works) and WAIT for my go-ahead before writing code.
>
> [Full spec: a Summarizer interface (StubSummarizer + GitHubModelsSummarizer), an independent deterministic Verifier (subset safety, evidence-trail completeness, red-flag retention, reading level via a real readability library), fail-closed orchestration, a pytest suite covering clean/invented-dose/dropped-red-flag/unmapped-advice/reading-level cases, scope constraints (no UI, no trigger, no live model in tests, no committed secrets), and deliverables list.]
>
> Again: give me your implementation plan first and WAIT. Do not write code until I approve the plan.

**Did:** Re-read issue #1 and the fixtures, then wrote out the full plan — file tree, data contracts (`EvidenceSpan`/`ClinicalClaim`/`SummarizerOutput`/`CheckResult`), the claim-based-not-prose-based design decision and why, each verifier check's algorithm, the fail-closed orchestrator, the test list, config/secrets handling, the live demo script, and the commit plan. Wrote no code. Waited.

---

### Phase 5 — Plan approved with three added requirements; build

**Prompt:**
> Plan approved, with three requirements before/while you build:
> 1. Keep the claim-based architecture. But document its limitation explicitly in the README and in a way I can pull into the PR's "outstanding" list: the reference summarizer assembles the draft from verified claims, so the CI-tested path cannot produce an unmapped claim by construction. The evidence-trail check's ability to catch unmapped claims in genuinely free-form model prose is exercised only on the live path, not in CI. Verifying arbitrary prose against source spans is a documented next step.
> 2. In the focused unit tests, explicitly include a test that hands evidence_trail.py a hand-built claim whose quote does NOT equal note_text[start:end] (a fabricated/lying span) and asserts it fails.
> 3. Confirm subset-safety catches an INVENTED medication (a claim citing a real span but naming a drug not in the note), not only an altered dose. Add a test for the invented-med case.
>
> Also add to the outstanding notes: red-flag detection is keyword-based and would need a more robust clinical-escalation classifier in production.
>
> Go ahead and build. Show me the diff / file tree when done before committing.

**Did:** Built `service/` (models, config, summarizer interface + stub + live, four verifier checks, orchestrator), `tests/` (24 tests, factories building clean and deliberately-corrupted `SummarizerOutput`s from the real fixtures), `requirements.txt`, `.env.example`, `scripts/live_demo.py`, README sections. Along the way, hit a real bug: my first version of a note_02 claim cited an evidence span that didn't actually contain the drug name it claimed to support — the verifier correctly failed it, and the fix was to widen the test-data span, not the checker. Also, in trying to hit the grade-6 reading-level target, shortened two note_03 red-flag sentences — this later turned out to have dropped safety content (see Phase 6). Showed the full file tree and diff before committing, as asked.

---

### Phase 6 — Correction #1: the note_03 red-flag content was quietly weakened

**Prompt:**
> Two things to show me before you commit, don't commit until I've seen them.
> 1. The note_02 evidence-span fix: confirm exactly WHAT you changed. Did you edit fixtures/note_02_multi_med.txt (the source note)? If so, that's wrong — the fixture notes are immutable test input. If you instead fixed the claim you construct in tests/factories.py, that's correct. Show me the diff and confirm the source note is byte-for-byte unchanged.
> 2. The note_03 red-flag shortening: show me the before/after of the two sentences you changed. I need to verify you only simplified vocabulary/sentence structure and that ALL of the following survived intact: every symptom (shortness of breath, chest pain, one-leg swelling/pain), the "go to the ER immediately" urgency, and the "do not wait for clinic" instruction. If you dropped or softened any safety content to hit grade 6, revert it — safety retention wins over reading level for red-flag content.
>
> Also answer: does your test suite currently assert that note_03's ER instruction retains its urgency AND all three symptoms after simplification? If not, add that assertion, it's the exact property at risk when we simplify red-flag language.

**Did:** Confirmed the note_02 fix was in `tests/factories.py` only, with the fixture byte-for-byte unchanged (`diff` showed no difference against the committed version). For note_03, admitted the real problem: the shortened ER sentence had dropped the leg's "pain" and "warmth" symptoms, softened "immediately" to "right away," and dropped "for clinic" from "do not wait for clinic." Confirmed no, the test suite did not currently assert full symptom/urgency retention. Proposed a fix-and-add-the-assertion plan and asked before proceeding rather than just fixing it quietly.

---

### Phase 7 — Correction #1, continued: fix the class of problem, not the instance

**Prompt:**
> note_02: approved. note_03: your fix plan is right but I want to fix the class of problem, not just this instance. You exposed a real design flaw: criterion 4 (retention) and criterion 5 (grade-6) can conflict, and the system had no rule for which wins — so you picked reading-level and dropped safety content. We encode the priority: for red-flag/safety-critical content, retention always wins.
>
> Do this:
> 1. Revert the note_03 red-flag claim to preserve ALL content (plain-language rewording OK, dropping a symptom or softening urgency is not).
> 2. Implement the priority rule in code, option A: exempt red-flag claims from the grade-6 reading-level gate entirely — compute reading level on the non-red-flag body only. Document this rule clearly as a deliberate safety decision.
> 3. Add the retention test: assert note_03's retained red-flag claim contains every symptom concept and the urgency instructions. This test must fail if any symptom or urgency element is dropped.
> 4. Make sure the overall draft still passes grade-6 on its non-safety content via simplifying THOSE sentences, not the red-flag one.
>
> Show me the note_03 before/after and the new test before committing.

**Did:** Reverted both note_03 red-flag claims to carry full content. Implemented the exemption in `service/verifier/reading_level.py` — red-flag claim text is carved out of `draft_summary` before grading, with the incident documented in the module's own docstring as the reason the rule exists. Added `test_note_03_er_claim_retains_every_symptom_and_full_urgency`, pinning every symptom and urgency phrase. Ran the full suite (25 tests, all passing) and showed the before/after diff before committing.

---

### Phase 8 — Commit and push

**Prompt:**
> Commit + push the build now

**Did:** Committed the full service (`678c00d`) and pushed `feat/note-to-summary` to origin, referencing #1 without closing it.

---

### Phase 9 — Status checks

**Prompt:** `git status`, then `git log --oneline -5`

**Did:** Reported clean working tree, then the 5-commit history.

---

### Phase 10 — Broken README link

**Prompt:**
> the "issue #1" link in the readme file doesn't lead to the issue. it gives a 404 error

**Did:** Found the relative link (`../../issues/1`) only resolves correctly in one specific GitHub rendering context and breaks elsewhere; replaced it with the absolute issue URL.

**Prompt:** `yes, commit and push it`

**Did:** Committed (`de692de`) and pushed the fix.

**Prompt:** `git status`, then `git log --oneline -5`

**Did:** Reported clean status and updated history.

---

### Phase 11 — Why does test data need ground truth at all?

**Prompt:**
> Quick question: about the ground truth. For the sample notes, there's, like, the normal file, and there's... and the ground truth. Why do we need the ground truth here? [...] In a real life case, there'll be ground truth for every patient's notes, not necessarily

**Did:** Explained the distinction: the six `*.groundtruth.md` files are hand-authored answer keys needed to build and test the verifier during development; the verifier's actual checks (subset safety, evidence trail, red-flag retention, reading level) are deterministic and structural, so they need zero ground truth per real patient note in production. No code changed.

---

### Phase 12 — Feasibility analysis: a self-correcting retry agent (analysis only, no code)

**Prompt:**
> Feasibility + design assessment only — do NOT write any code, do NOT modify anything. I want your honest analysis, then you stop.
>
> [Full spec: an orchestration agent on top of the same components as tools, adding a bounded self-correcting retry loop when verification fails — with four required safety properties: bounded retries, fail-to-human escalation, full attempt logging, no cross-attempt regression. Asked for: 1) feasibility against current code, 2) the regeneration question — can a retry meaningfully target the failed check, 3) a design sketch (pseudocode, not real code) with tests for each safety property, 4) new failure modes this introduces, 5) an honest effort estimate, 6) a recommendation on building now vs. deferring.]
>
> Then STOP and wait. No code, no file changes.

**Did:** Delivered the full six-part written analysis. Key conclusions: the `Summarizer` interface would need a small but real widening to accept feedback; reading-level feedback specifically risks reproducing the exact content-dropping regression from Phase 6-7; recommended deferring this as a separate follow-up rather than building it into this slice, since its core mechanism is live-model-dependent and can't be validated the way the rest of the build is. No code touched.

---

### Phase 13 — Recap request

**Prompt:** `okay then give a brief recap of the work done so far`

**Did:** Gave a chronological recap of everything up to that point.

---

### Phase 14 — First manual test (stub path)

**Prompt:**
> i would like ot do a manual test. can you run the code on the physician note 3 and let me see the output

**Did:** Ran the orchestrator with `StubSummarizer` against the canned clean output for note_03, printed the full JSON payload.

---

### Phase 15 — Wanting a live, uncanned test

**Prompt:**
> i want to add a live github ai model now so i can test an uncanned sample output

**Did:** Explained that `StubSummarizer` can't produce anything uncanned, and walked through setting up a GitHub Models PAT: create a fine-grained token with the "Models" permission, put it in `.env` (not committed) by editing it directly rather than pasting the secret into chat.

---

### Phase 16-18 — A real secret-leak incident

**Prompt:** `token has been added`

**Did:** Checked for `.env` — not found.

**Prompt:** `i put it in the .env.example`

**Did:** Checked `.env.example` and git status — both clean, placeholder still in place, nothing found there either.

**Prompt:** `it is in the live vopy that has already been committed, not in the local file`

**Did:** Searched the full local *and remote* git history and found a real commit (`611c1f5`, "Update GitHub token in .env.example") that had been pushed to GitHub directly, outside this session, containing a live PAT in plaintext — and confirmed the repository is **public**. This was a genuine security incident, not a hypothetical.

---

### Phase 19-20 — Handling the leak

**Prompt:**
> i understand the token is a security breach but i only need it to test the code so lets go ahead with it

**Did:** Rather than assume what "go ahead" meant, asked two clarifying questions (token still active or already rotated; forward-fix only vs. a full history rewrite) since a wrong assumption here meant either leaving a live secret exposed or force-pushing a rewritten history without full sign-off. User answered: token still active, use it now and revoke right after; forward-fix only (not a history rewrite).

**Did:** Pulled the leaked commit locally, moved the real token into gitignored `.env`, restored `.env.example` to the placeholder, and tried the live call — it failed with a GitHub-side `410 github_models_retirement_brownout` (an external outage, not a bug). Committed the forward-fix (`bd8d765`) and pushed. Reiterated that the leaked token should be revoked regardless of the failed test, since it was still sitting in public git history.

---

### Phase 21-24 — Switching to Groq and getting a real live run

**Prompt:** `is there another free ai tool we could use to test?`

**Did:** Proposed Groq (cloud, needs a free key) vs. Ollama (fully local, no key). User picked Groq.

**Prompt:** `here: gsk_[redacted — a real Groq API key was pasted directly in chat]`

**Did:** Wrote the key directly into gitignored `.env` (never into a tracked file), verified it was git-ignored before doing anything else. First attempt used a guessed model name and got a 404; queried Groq's `/models` endpoint for the real current list and picked `openai/gpt-oss-120b`. Got a successful live run against note_03.

**Prompt:** `lets review output for fixture note 2`

**Did:** Ran live note_02, reviewed it in detail, and surfaced a real finding: a claim carrying dose/frequency fields was classified `"instruction"` instead of `"medication"` by the model, which meant `subset_safety`'s dose check never ran on it — a live-path-only gap invisible on the stub path.

---

### Phase 25 — Adding a conversational greeting

**Prompt:**
> the summaaries do not have names - i think we need to add that capability and commit. E.G: Hi Marcus, just following up on your viste from yesterday...etc it needs to be more vonversational.

**Did:** Built `service/note_parsing.py` (deterministic `PATIENT:` header parsing), updated `tests/factories.py` to prepend a name-based greeting to every stub draft, updated the live prompt to inject the extracted name. Added 4 tests (29 total, including one confirming the greeting never leaks into `evidence_map`). Verified live against note_02 and note_03, then committed and pushed (`b3c7698`).

---

### Phase 26 — Reading level fails live; raised to grade 8

**Prompt:** `okay lets try again for physiscian fixture note 3`

**Did:** Ran live note_03 again — all safety checks passed, but `reading_level` failed at grade 7.7.

**Prompt:**
> i thjink the reading level should be a grade 8 max not 6 anymore. can you change and commit this

**Did:** Flagged that this relaxes issue #1's acceptance criterion 5 and the note_04 ground-truth doc's stated target, then made the change as directly instructed: raised `READING_LEVEL_MAX_GRADE` to 8 in `config.py`/`.env.example`, updated the fixture ground-truth doc and README to match, and strengthened a jargon test that had become fragile at the new threshold (was 0.83 over the line, now ~2.8 over). Committed (`7463ae1`).

---

### Phase 27 — Correction #2: reverting the standard, then the release phase

**Prompt:**
> good that you didnt edit it, because i will like to revert the reading level back to grade 6. this is beacuse grade 6 is the NIH/AMA/HHS consensus standard for patient materials; grade 8 is the US average adult level, which by definition half of patients can't easily read. We do not lower a health-literacy standard because the current model can't reliably meet it — that lets a tool limitation dictate a clinical standard. Instead: keep the target at grade 6, and have the verifier report the actual score and the gap [...] so a too-hard draft is flagged-but-visible to the reviewer/coordinator, never silently passed. The model's current grade-~8 performance is a documented finding in the outstanding list, not a changed requirement.
>
> Now moving to the release phase also: Rename service/summarizer/github_models.py to something provider-neutral (e.g. openai_compatible.py) and rename the class accordingly. [...] Rename the env vars to be provider-neutral: LLM_API_KEY, LLM_BASE_URL, LLM_MODEL [...] Set the .env.example defaults to Groq's values [...] Update the README [...] Do NOT touch the fixtures, the verifier logic, the stub, or the tests.
>
> CI: add a GitHub Actions workflow that runs pytest on push/PR. Open the PR from feat/note-to-summary into main. Body includes "Closes #1". [...] Write the prose plainly — short sentences, no filler, no marketing tone. Don't merge. Give me the PR URL.

**Did:** Reverted the reading-level threshold to 6 (`294f0f6`), explicitly as a policy correction, not a bug fix. Renamed `github_models.py`/`GitHubModelsSummarizer` → `openai_compatible.py`/`OpenAICompatibleSummarizer`, renamed all three env vars, set Groq as the `.env.example` default (`821c746`) — fixtures/verifier/stub/tests untouched, 29/29 tests still passing. Added `.github/workflows/tests.yml` (`69a0d81`), confirmed it ran green. Discovered `main` had never actually been pushed to origin, pushed it, then opened PR #2 with the full plain-prose description including the outstanding list and the two bugs this build had caught (Phase 5's evidence-span bug, Phase 6-7's red-flag regression).

---

### Phase 28 — Release note for the coordinator

**Prompt:**
> Create RELEASE_NOTE.md at the repo root with the exact content below — commit it verbatim, do not reword or reformat. Commit it on feat/note-to-summary (the same branch as PR #2) so it's included in that PR. Reference #1 in the commit message but don't close anything, and don't merge. Confirm it's committed and pushed.
>
> [full verbatim release-note content pasted here — see RELEASE_NOTE.md]

**Did:** Wrote `RELEASE_NOTE.md` byte-for-byte as given, committed (`345df85`) referencing #1 without closing it, pushed, confirmed the content matched exactly and that PR #2 had picked it up.

---

### Phase 29 — Honest audit against the acceptance criteria

**Prompt:**
> Audit the current build against issue #1's acceptance criteria — honestly, not favorably. For EACH acceptance criterion [...] tell me: the criterion, quoted; PASS / PARTIAL / FAIL; the specific test name(s) or code that satisfies it (or what's missing if PARTIAL/FAIL). Do not grade generously. [...] Don't change any code — just report.

**Did:** Re-read every verifier module and test file and delivered a criterion-by-criterion audit. Result: 2 clean PASS (payload shape, timing instrumentation), 1 strong PASS (CI test gate), and 4 PARTIAL — subset safety, evidence trail, red-flag retention, and reading level all have real, specific gaps, the common thread being that checks 2-4 only ever inspect the `claims` list, never `draft_summary` itself, so nothing stops fabricated content in the actual draft text from being invisible to the verifier if it has no backing claim object. No code changed.

---

### Phase 30 — Could the structural gap be fixed easily?

**Prompt:** `how easy is it to fix the structural gap so checks read draft_summary directly`

**Did:** Laid out the real options and their costs: a cheap check (claim → draft substring match) that solves the wrong half of the problem; a rigorous fix that requires either brittle keyword heuristics or a second model call inside the verifier (which would break the "verifier never calls a model" invariant the whole design relies on); or discarding the model's own `draft_summary` and reassembling it from claims in code, which fully closes the gap but directly conflicts with the conversational-tone feature just built in Phase 25. Conclusion: no option is both easy and complete. No code changed.

---

### Phase 31 — A second issue: the safety pass

**Prompt:**
> okay i will leave it at what it is. Create a second GitHub issue: the safety pass. Title: "Safety pass: five ways this change could harm someone". Use gh issue create. Do NOT close it.
>
> [Full spec: five ranked risks — fabrication reaching the patient via the structural gap from Phase 29-30; an unrecognized red-flag instruction being dropped; a truncated live draft; reading level too high for the patient; erosion of the patient-nurse relationship and automation bias — each with harm, mitigation, and an explicit BLOCKS RELEASE yes/no with reasoning tied to the human-in-the-loop reviewer being the current compensating control.]
>
> Show me the issue body before creating it.

**Did:** Drafted the full issue body per the spec and showed it for approval before creating anything.

**Prompt:** `create it`

**Did:** Created issue #3, left open.

---

### Phase 32 — Adding a population-specific note

**Prompt:**
> Add a note to risk #4 (reading level) in the safety-pass issue, and to the outstanding list in the PR — do NOT change any code or the grade-6 threshold.
>
> The note: This is a longevity clinic, whose patient population is likely higher-literacy than the general population [...] That is a reason a clinic MIGHT consciously choose a higher reading-level target — but it should be an explicit, documented clinical decision, not a silent default. The system's default target stays at grade 6 [...] Framing: default safe, deviate consciously — never lower the bar just because a demographic assumption makes it feel safe, or because the model struggles to meet it.
>
> Keep it plain and short. Show me before committing/editing the issue.

**Did:** Drafted the note for both issue #3 and PR #2, showed both before editing.

**Prompt:** `go ahead`

**Did:** Edited issue #3's risk #4 section and PR #2's reading-level bullet via `gh issue edit` / `gh pr edit`, no code or threshold touched.

---

### Phase 33 — This file

**Prompt:**
> i would like to add the log of this conversation in the rep. Create SESSION_LOG.md at the repo root. i want the actual prompt history of this build [...] not a summary written from memory [...] keep the real instructions visible — including the constraints I set (plan-before-build, don't push to main, don't close the issue, show-me-before-committing) and the corrections I made (the dropped red-flag symptoms, the unsupported evidence span, deferring the self-correcting agent). Don't sanitize the corrections out. Commit on feat/note-to-summary, in PR #2, referencing #1 without closing. Show me the draft first.

**Did:** Wrote this file.
