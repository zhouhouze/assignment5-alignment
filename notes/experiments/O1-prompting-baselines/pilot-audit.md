# O1 Prompting Baselines - Pilot Audit

Status: Pilot Audit Gate complete. No new GPU inference, Full run, GRPO, commit, or push was performed in this audit stage.

## Scope

- Pilot result directory: `/root/autodl-tmp/cs336/results/O1-prompting-baselines/20260716-142558/pilot`
- Commit under audit: `4af419ed9694301fa4a82b86de6c0e55b585e271`
- Model id: `allenai/OLMo-2-0425-1B`
- Dataset slice: GSM8K test ids `0-19`
- Total generations audited: 60
- Generation parameters: `temperature=1.0`, `top_p=1.0`, `max_tokens=512`, `seed=0`, `batch_size=4`

## Data Integrity

Observed:

- `pilot_metrics.json`, `pilot_review_samples.json`, all three `predictions.jsonl`, summaries, preflight, and manifests were readable.
- Each prompt has exactly 20 rows; total rows equal 60.
- All prompts use identical example ids `0-19`.
- Questions and ground-truth answers match the first 20 rows of `data/gsm8k/test.jsonl`.
- Responses are non-empty.
- Category counts match summary files.
- Rewards/categories recompute to the stored values using `question_only_reward_fn` and `r1_zero_reward_fn`.
- Recorded generation and stop parameters match the Pilot plan.

## Model And Prompt Identity

Observed:

- Run manifest and vLLM log identify `allenai/OLMo-2-0425-1B`.
- vLLM log records tokenizer `allenai/OLMo-2-0425-1B`, served model name `allenai/OLMo-2-0425-1B`, and architecture `Olmo2ForCausalLM`.
- Hugging Face cache config path: `/root/autodl-tmp/cs336/hf-cache/hub/models--allenai--OLMo-2-0425-1B/snapshots/a1847dff35000b4271fa70afc5db10fd29fedbdf/config.json`.
- Cached config records `model_type=olmo2`, `architectures=["Olmo2ForCausalLM"]`, `hidden_size=2048`, `num_hidden_layers=16`, `vocab_size=100352`.
- Script uses raw string prompts with `LLM.generate`; no chat template path was observed.
- Prompt files have no git diff.
- `formatted_prompt` exactly equals the prompt file with `{question}` substituted.

Prompt SHA256:

- `question_only`: `bff41d4d354078f7c7adde76fabf70c086aa54a29fd4fb0e15a8f32b3ed27501`
- `r1_zero`: `56213732da87e12ace60a2b88a16df0af18280fb0563a957cbecc938a6a2ac0e`
- `r1_zero_three_shot_gsm8k`: `91788d4fb0e8d81ec17066dc122572f02a6d2ec3ed762174c7b70fcf5fdf6193`

## Aggregate Metrics

| Prompt | Total | Cat1 | Cat2 | Cat3 | Accuracy | Format rate | Avg tokens | Median tokens | Finish reasons | Strict parser bug | Human-correct but unscorable |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | ---: |
| `question_only` | 20 | 0 | 9 | 11 | 0.0% | 45.0% | 323.6 | 385.0 | {'length': 8, 'stop': 12} | 0 | 1 |
| `r1_zero` | 20 | 0 | 13 | 7 | 0.0% | 65.0% | 123.6 | 84.0 | {'stop': 19, 'length': 1} | 0 | 0 |
| `r1_zero_three_shot_gsm8k` | 20 | 0 | 19 | 1 | 0.0% | 95.0% | 104 | 99.0 | {'stop': 20} | 0 | 1 |

## Error Taxonomy

Counts include both primary and secondary error labels.

| Prompt | Arithmetic | Reasoning | No numeric | Multiple answers | Topic drift | Length truncation | Unclosed tag | Correct intermediate/wrong final | Example copying | GT literal anywhere |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `question_only` | 0 | 4 | 10 | 7 | 11 | 8 | 0 | 0 | 0 | 3 |
| `r1_zero` | 4 | 13 | 4 | 0 | 2 | 1 | 2 | 0 | 0 | 2 |
| `r1_zero_three_shot_gsm8k` | 8 | 7 | 0 | 0 | 0 | 0 | 1 | 1 | 0 | 4 |

Primary-error distributions:

- `question_only`: `{'format_missing': 4, 'length_truncation': 8, 'multiple_answers': 4, 'question_misunderstanding': 1, 'topic_drift': 3}`
- `r1_zero`: `{'arithmetic_error': 4, 'format_missing': 3, 'length_truncation': 1, 'no_numeric_answer': 2, 'question_misunderstanding': 2, 'reasoning_error': 6, 'topic_drift': 1, 'unclosed_tag': 1}`
- `r1_zero_three_shot_gsm8k`: `{'arithmetic_error': 7, 'question_misunderstanding': 5, 'reasoning_error': 7, 'unclosed_tag': 1}`

## Audit Taxonomy Clarification

Definitions used for interpreting the Pilot audit:

- `strict_parser_bug`: output follows the required answer format and the final answer is correct, but the parser still extracts or grades it incorrectly.
- `human_correct_but_unscorable`: human can identify a correct final answer, but the output does not follow the required format, so the official grader cannot award credit.
- `correct_intermediate_missing_or_wrong_final`: reasoning includes the correct value, but the final answer region is empty, unclosed, or gives a different/wrong answer.

## Strict Parser Bugs And Unscorable Correct Answers

Observed:

- `strict_parser_bug`: 0/60.
- `human_correct_but_unscorable`: 1/60 (`question_only` id 19).
- `correct_intermediate_missing_or_wrong_final`: 1/60 (`r1_zero_three_shot_gsm8k` id 1).
- Ground-truth literal appeared somewhere in response: 9/60.

Inference:

- The 0% official answer accuracy is not explained by a systematic strict parser bug in this Pilot.
- Some outputs contain the correct number somewhere, but usually not as the final answer in the expected format.
- A correct number in reasoning is not counted as a correct final answer when the answer region is empty, unclosed, or wrong.

## Representative Cases

- `question_only` id 0: primary `length_truncation`, human final `(15* ?)+\cdot\cdot\cdot`, grader `(15* ?)+\\cdot\\cdot\\cdot`, notes: hit max_tokens; several boxed fragments; final boxed expression unrelated/wrong
- `question_only` id 5: primary `length_truncation`, human final `no clear final answer`, grader `None`, notes: hit max_tokens while drifting through unrelated text
- `question_only` id 6: primary `topic_drift`, human final `no clear final answer; empty boxed answers`, grader ``, notes: unrelated generated QA/material; no clear final answer
- `question_only` id 7: primary `length_truncation`, human final `no clear final answer; empty boxed answer`, grader ``, notes: hit max_tokens after cloud-storage educational drift
- `question_only` id 8: primary `topic_drift`, human final `no clear final answer`, grader `None`, notes: long continuation without final GSM8K answer
- `question_only` id 9: primary `topic_drift`, human final `no clear final answer`, grader `None`, notes: drifted from original problem and did not provide final answer
- `question_only` id 10: primary `length_truncation`, human final `no clear final answer`, grader `None`, notes: hit max_tokens without final answer
- `question_only` id 12: primary `length_truncation`, human final `\frac{9}{1.5}`, grader `\frac{9}{1.5}`, notes: hit max_tokens; last extracted answer evaluates to 6, not 13
- `question_only` id 13: primary `length_truncation`, human final `no clear final answer`, grader `None`, notes: hit max_tokens without final answer
- `question_only` id 15: primary `length_truncation`, human final `no clear final answer; empty boxed answer`, grader ``, notes: hit max_tokens; unstable/empty boxed answer
- `question_only` id 16: primary `length_truncation`, human final `no clear final answer`, grader `None`, notes: hit max_tokens; no correct final answer
- `question_only` id 19: primary `format_missing`, human final `6`, grader `None`, notes: human-visible final A: 6 is correct but not boxed, so official format failed

## Full Cost Estimate

Based only on Pilot actual runtimes, throughput, token counts, and output sizes:

- Full examples: 1319.
- Full generations: 3957.
- Estimated generation runtime excluding fixed overhead: 13.94 minutes.
- Estimated runtime including observed model-load/fixed overhead: 15.27 minutes.
- `question_only` estimated response tokens: 426828.4.
- `r1_zero` estimated response tokens: 163028.4.
- `r1_zero_three_shot_gsm8k` estimated response tokens: 137176.0.
- Estimated total response tokens: 727032.8.
- Estimated predictions JSONL size: 8.78 MiB.

Assessment:

- Disk is sufficient for JSONL outputs given the observed 69G free after Pilot.
- `batch_size=4` completed Pilot without OOM; it is reasonable to keep for Full only if preflight checks pass.
- Full should stop on low disk, OOM, empty response, unreadable JSONL, ID mismatch, dependency diff, unexpected model/commit, or residual vLLM after failure.

## What This Pilot Does Not Prove

- It does not prove the true model accuracy is exactly 0.
- It does not establish a statistically significant prompt ranking.
- It is not a formal GSM8K benchmark result.
- It should not be used to justify changing official parameters merely to improve the number.
- With 0 successes in 20 examples, a rough 95% binomial upper bound is about 15%; this is only an uncertainty illustration, not a performance claim.

## Notes Review

Observed before this audit note:

- Pilot notes described the run as Pilot-only and did not claim Full results.
- Notes separated observations, inferences, and hypotheses.
- Notes did not claim three-shot improved accuracy.
- No dependency file, grader, or prompt diff was observed.

## Artifacts

- Full audit table, using the older JSON field names plus the clarified note taxonomy: `/root/autodl-tmp/cs336/results/O1-prompting-baselines/20260716-142558/pilot/pilot_all_responses_audit.jsonl`
- Error taxonomy: `/root/autodl-tmp/cs336/results/O1-prompting-baselines/20260716-142558/pilot/pilot_error_taxonomy.json`
- Full cost estimate: `/root/autodl-tmp/cs336/results/O1-prompting-baselines/20260716-142558/pilot/pilot_full_cost_estimate.json`
- Pilot metrics: `/root/autodl-tmp/cs336/results/O1-prompting-baselines/20260716-142558/pilot/pilot_metrics.json`

## Recommendation

Stop at the Pilot Audit Gate. Do not run Full until the learner/reviewer decides whether the current baseline is still useful despite 0/20 official accuracy and two format-correctness edge cases.
