# What I'm shipping, and why

## The seat
The nurse coordinator sits between the doctor and the patient for the length of a multi-month protocol. She runs the day-1, day-7, and day-30 check-ins, fields symptom questions that arrive by text and email at all hours, works from the doctor's note in the EHR, and gets a plain-language summary back to the patient. She is expected to be off her screen with a patient and on her screen for everyone else at the same time.

That last part is the real problem. Her core difficulty isn't any single task — it's attention fragmentation, the constant pull between the person in front of her and the queue behind her. So the question I asked wasn't "what's broken," it was "which single change gives her the most attention back, and can I take it all the way to releasable in a weekend?"

## What I looked at
Four frictions make up that fragmentation. The scheduled check-ins are a timing and tracking burden. The inbound symptom questions are unstructured and need triage. The doctor's note has to be turned into language the patient understands, by hand, every time. And the sum of all three is the fragmentation itself.

I set the fragmentation aside as the reason, not the target — you can't ship "less fragmentation," you ship something that removes a piece of it. That left three real candidates.

I didn't pick the check-ins. It's a genuine burden, but its failure mode is a missed check-in — a correctness problem, not a safety one. The strongest test I could write for it would be weak, and this is a healthcare screen where the test is the point.

I didn't pick symptom triage either, and this one I want to be clear about: it's probably the biggest problem of the three. But mis-triaging a symptom message can downgrade a real emergency, and doing it responsibly means clinical validation and guardrails I can't stand up on my own over a weekend. The honest version I could ship in the time would be a thin assist layer — smaller than the problem it claims to solve. Pretending otherwise would be exactly the wrong answer to the safety questions this exercise asks. It's out of scope here, not out of reach.

## What I'm building
The note-to-summary translation. When the platform holds a new physician note for a patient, it generates a patient-ready, plain-language summary — and alongside it, an evidence trail that ties every clinical claim in the draft back to the exact span in the note it came from. The coordinator opens the patient, reviews a draft instead of writing from scratch, and sends.

I picked this for three reasons. It's felt on every patient, so the time it saves compounds daily rather than at the edges. Its failure mode and its test are the same object — the danger is a hallucinated dose or a dropped safety instruction reaching a patient, and the evidence trail turns that danger into something both the coordinator and an automated check can catch. And it stands on its own: the note is the input, so I don't have to lean on EHR integration the case never promises.

There's a quieter reason too. Moving her from "write it" to "check it and send" is the most direct way to hand attention back to the patient in front of her, which is the whole point.

## What I'm assuming
I'm taking the case at its word that the platform already surfaces the doctor's note to the coordinator and already owns the patient-messaging channel. What it doesn't do yet is turn that note into a patient-facing draft — that's the layer I'm adding. And since the exercise says to invent everything, no real patient information is involved anywhere; every note and patient is fabricated.

## The number I'm moving
The primary outcome is the median time to produce a patient-ready summary for a completed treatment. The thing I'm actually moving is time saved: the gap between writing one by hand and editing a generated draft.

I'm not going to assume a baseline. Measuring it is part of the work — the evaluation instruments how long the current hand-authored process takes first, then measures the review-and-send time against it, and the difference is the result. Median rather than average, because a few complex notes will always run long and shouldn't be allowed to define the typical experience.

## What this sets up
The obvious next step is context. A day-7 summary is better when it knows what day-1 said, and pulling in prior notes, past check-ins, and the patient's message history would give a longitudinal picture instead of a per-note one. I'm deliberately not building that this weekend. It changes the safety model from "every claim maps to this note" to "every claim maps to somewhere across several documents," which weakens the exact guardrail that makes this slice safe to ship. It's the right next thing — which is where it belongs, as the next thing.
