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
