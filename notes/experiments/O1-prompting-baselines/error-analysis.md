# O1 Prompting Baselines - Error Analysis

Status: Smoke, Pilot, and Pilot audit observations recorded. Full error analysis has not been run.

## Manual Review Requirements

- Review at least 10 Category 2 examples if available.
- Review at least 10 Category 3 examples if available.
- Count outputs that are actually correct but not parsed properly.
- Save representative prompts/responses.

## Categories

- Category 1: formatted and correct.
- Category 2: formatted but incorrect.
- Category 3: unformatted and incorrect.
- Unexpected: unformatted but answer-correct; record separately if observed.

## Notes

Do not fill parser false-negative counts before Pilot or Full generation outputs exist.

## Smoke Samples Observed

All smoke samples used the first GSM8K test example. The extracted ground truth was `18`.

### `question_only`

- Category: 2.
- Finish reason: `length`.
- Observed behavior: the response contained boxed fragments but did not produce the correct final answer before hitting `max_tokens=512`.
- Interpretation: validates that the prompt path and grader run, but does not establish the prompt's real failure rate.

### `r1_zero`

- Category: 2.
- Finish reason: `stop`.
- Observed behavior: the output retained `</answer>` and was formatted, but the answer content was not correct.
- Interpretation: validates stop-string retention and the `r1_zero_reward_fn` path for a formatted incorrect response.

### `r1_zero_three_shot_gsm8k`

- Category: 2.
- Finish reason: `stop`.
- Observed behavior: the output retained `</answer>` and was formatted, but answered `$120` instead of `18`.
- Interpretation: validates few-shot prompt rendering and stop-string retention, not model quality.

## Not Yet Done

- No Full GSM8K run.
- No Full GSM8K run yet in this notes commit.


## Pilot Preliminary Error Analysis

Output directory: `/root/autodl-tmp/cs336/results/O1-prompting-baselines/20260716-142558/pilot`

Observed:

- `question_only`: 9 Category 2, 11 Category 3, 8 length-terminated responses.
- `r1_zero`: 13 Category 2, 7 Category 3, 1 length-terminated response.
- `r1_zero_three_shot_gsm8k`: 19 Category 2, 1 Category 3, 0 length-terminated responses.
- No Category 1 examples were observed in the Pilot.
- Sampled Category 2/3 outputs did not reveal a `strict_parser_bug`.
- R1 close-tag inclusion was not universal: `r1_zero` missing close tag on ids 4 and 18; `r1_zero_three_shot_gsm8k` missing close tag on id 1.

Inference:

- The dominant failure mode in this Pilot is answer/model behavior, with additional format instability for `question_only` and a few R1 outputs.
- Three-shot R1 improved formatting but not answer correctness on this sample.

Hypothesis:

- OLMo-2-0425-1B at `temperature=1.0` may need a different evaluation strategy or additional constraints before a useful Full baseline.

## Pilot Audit Taxonomy Clarification

Definitions used after the Pilot Audit Gate:

- `strict_parser_bug`: output follows the required answer format and the final answer is correct, but the parser still extracts or grades it incorrectly. Pilot count: 0.
- `human_correct_but_unscorable`: human can identify a correct final answer, but the output does not follow the required format. Pilot example: `question_only` id 19.
- `correct_intermediate_missing_or_wrong_final`: reasoning includes the correct value, but the final answer region is empty, unclosed, or gives a wrong answer. Pilot example: `r1_zero_three_shot_gsm8k` id 1.

Do not describe `question_only` id 19 as a parser bug, and do not describe the three-shot id 1 reasoning value as a correct final answer.
