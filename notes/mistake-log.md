# Mistake Log

Purpose: record learner predictions, actual results, mistake causes, and corrected judgment principles. Do not fill in understanding on behalf of the learner.

## 2026-07-15 - O1 Prompting Baselines

- Initial learner predictions: pending.
- Actual results: smoke-only run on 2026-07-16 produced Category 2 for all three prompts on the first GSM8K test example. This is not a Pilot or Full result.
- Mistake cause: pending learner reflection. Do not infer broad prompt-quality conclusions from one smoke example.
- Corrected judgment principle: smoke tests validate plumbing; Pilot/Full runs are needed before judging accuracy or prompt ranking.


## 2026-07-16 - O1 Pilot Gate

- Initial learner predictions: pending.
- Actual results: Pilot over GSM8K test ids `0-19` produced 0 Category 1 examples across all three prompts. Format rates were 45.0% for `question_only`, 65.0% for `r1_zero`, and 95.0% for `r1_zero_three_shot_gsm8k`.
- Mistake cause: pending learner reflection. Do not infer final prompt ranking from a 20-example Pilot, but do treat repeated truncation, drift, and R1 tag failures as gate findings.
- Corrected judgment principle: an experiment can be technically runnable yet not ready for Full; Pilot gates should inspect raw outputs and measurement validity before scaling.


## 2026-07-16 - O1 Full Attempt 1 Reliability Failure

- Initial learner predictions: pending.
- Actual results: Full Attempt 1 stopped at `question_only` example 55 with `RuntimeError: Empty response for prompt question_only, example 55`; no official Full predictions were produced.
- Mistake cause: the evaluator treated `completion.text == ""` as a hard failure instead of recording it as a legitimate model output and passing it to the grader.
- Corrected judgment principle: empty model outputs should be scored, while missing completions, output-count mismatches, and generation exceptions should remain hard failures.

<!-- full-v2-review-gate-mistake-log -->

## 2026-07-16 - O1 Full Attempt 2 Review Gate

- Initial learner predictions: pending.
- Actual results: Full Attempt 2 completed with exit code `0`; official grader metrics were `1/1319` Category 1 for `question_only`, `1/1319` Category 1 for `r1_zero`, and `235/1319` Category 1 for `r1_zero_three_shot_gsm8k`.
- Mistake cause: pending learner reflection. Do not treat official grader accuracy as human-adjusted accuracy before reviewing Category 2/3 packets.
- Corrected judgment principle: distinguish measured grader outcomes, deterministic format/termination behavior, and human semantic interpretation; only the first two are complete at this gate.

<!-- full-human-review-mistake-log -->

## 2026-07-16 - O1 Human Review Closeout

- Initial learner predictions: pending.
- Actual results: sampled human review found no strict parser bugs in `24` reviewed Category 2/3 examples. Category 2 had `0/12` actual-correct-but-unscored cases. Category 3 had `1/12` actual-correct-but-unscored case and `2/12` correct-intermediate-missing-or-wrong-final cases.
- Mistake cause: pending learner reflection. Do not treat correct intermediate reasoning as final-answer correctness, and do not treat format-invalid human-correct outputs as parser bugs.
- Corrected judgment principle: official metrics, sampled human review, and speculative human-adjusted accuracy are three different levels of evidence; only the first two are available here.
