# Concept Map - GRPO and Variants

Date: 2026-07-15

## Pipeline Overview

1. Prompt and output strings are tokenized into causal LM inputs, shifted labels, and a response-token mask.
2. The policy model scores each response token with conditional log probabilities.
3. A reward function scores each rollout response against the repeated ground truth.
4. Rewards are converted into advantages using group-relative baselines and optional normalizers.
5. Per-token policy-gradient losses are computed from advantages and log probabilities.
6. Losses are aggregated across response tokens and batch elements.
7. The training step composes the above pieces, runs backward passes over microbatches, clips gradients if requested, and steps the optimizer.

## Core Tensor Shapes

- `input_ids`: `(batch_size, sequence_length)`
- `labels`: `(batch_size, sequence_length)`
- `response_mask`: `(batch_size, sequence_length)`
- `policy_log_probs`: `(batch_size, sequence_length)`
- `old_log_probs`: `(batch_size, sequence_length)`
- `raw_rewards`: `(rollout_batch_size,)`
- `advantages`: `(rollout_batch_size,)`
- `per_token_policy_gradient_loss`: `(batch_size, sequence_length)`
- aggregated loss: scalar tensor

## Bottom-Level Components

- `run_tokenize_prompt_and_output`: text to tensors and response mask.
- `run_get_response_log_probs`: model logits to per-token log probabilities and optional entropy.
- `run_compute_rollout_rewards`: reward function outputs to raw reward tensor and logging metadata.
- `run_compute_group_normalized_rewards`: raw rewards to group-relative advantages.

## Middle Components

- `run_compute_policy_gradient_loss`: advantages plus current/old log probabilities to per-token loss.
- `run_aggregate_loss_across_microbatch`: per-token loss plus mask to scalar microbatch loss.

## Top-Level Component

- `run_grpo_train_step`: orchestrates tokenization, reward computation, advantage computation, log-prob scoring, loss computation, aggregation, gradient accumulation, gradient clipping, optimizer step, and metadata.

## Variant Switches

- Standard GRPO: `baseline="mean"`, `advantage_normalizer="std"`, `importance_reweighting_method="none"`, `loss_normalization="sequence"`.
- GRPO constant: standard GRPO advantage, but `loss_normalization="constant"`.
- Dr. GRPO: `baseline="mean"`, `advantage_normalizer="none"`, constant loss normalization.
- RFT: `baseline="none"`, `advantage_normalizer="none"`, constant loss normalization.
- MaxRL: `baseline="mean"`, `advantage_normalizer="mean"`, constant loss normalization.
- Off-policy noclip: importance reweighting without clipping.
- Off-policy GRPO/PPO-style: token-level importance ratio with clipping.
- GSPO: sequence-level geometric-mean importance ratio with clipping over response tokens.

## Recommended Implementation Order

1. `run_compute_group_normalized_rewards`
2. `run_aggregate_loss_across_microbatch`
3. `run_compute_policy_gradient_loss` on-policy mode only
4. `run_tokenize_prompt_and_output`
5. `run_get_response_log_probs`
6. `run_compute_rollout_rewards`
7. `run_grpo_train_step` standard on-policy
8. Extend group normalization for Dr. GRPO, RFT, and MaxRL variants
9. Extend policy-gradient loss for `noclip` and `grpo`
10. Extend policy-gradient loss for `gspo`
11. Extend `run_grpo_train_step` for on-policy variants and off-policy modes

## CPU Unit-Test Surface

These tests should be feasible on CPU with tiny fixtures:

- `test_tokenize_prompt_and_output`
- `test_get_response_log_probs`
- `test_compute_rollout_rewards`
- `test_compute_group_normalized_rewards_grpo`
- `test_compute_group_normalized_rewards_drgrpo`
- `test_compute_group_normalized_rewards_maxrl`
- `test_compute_policy_gradient_loss_on_policy`
- `test_compute_policy_gradient_loss_off_policy`
- `test_compute_policy_gradient_loss_off_policy_gspo`
- `test_aggregate_loss_across_microbatch_sequence`
- `test_aggregate_loss_across_microbatch_constant`
- `test_grpo_train_step_standard_on_policy`
- `test_grpo_train_step_variants_on_policy`
- `test_grpo_train_step_off_policy`

## GPU or Full-Model Experiment Surface

These require Linux GPU, vLLM, Modal, or full model/dataset runs:

- Prompting baselines on OLMo-2-0425-1B and GSM8K.
- Standard on-policy GRPO experiments over four seeds.
- Learning-rate tuning.
- Prompt ablation with `question_only`, `r1_zero`, and `r1_zero_three_shot_gsm8k`.
- On-policy variant comparisons for GRPO constant, Dr. GRPO, RFT, and MaxRL.
- Off-policy GRPO experiments for naive, noclip, clipped token-level GRPO, and GSPO.
- Any vLLM generation/weight-sync workflow through `cs336_alignment/vllm_utils.py`.

## First Learning Target

Start with `run_compute_group_normalized_rewards`.

Why:

- It is the conceptual heart of GRPO: transform multiple sampled completions for the same prompt into relative learning signals.
- It is independent of tokenizer, model forward passes, optimizer behavior, and vLLM.
- It unlocks the clearest comparison among GRPO, Dr. GRPO, RFT, and MaxRL.

Associated tests:

- `test_compute_group_normalized_rewards_grpo`
- `test_compute_group_normalized_rewards_drgrpo`
- `test_compute_group_normalized_rewards_maxrl`

Concepts to master before implementation:

- Grouping layout: `rollout_batch_size = n_prompts_per_rollout_batch * group_size`.
- Per-group mean baseline.
- Per-group standard-deviation normalization.
- No-baseline rewards for RFT.
- Mean-reward normalization for MaxRL.
- Why reward normalization changes optimization difficulty weighting.


## 2026-09-14 — Standard GRPO CPU 链路已实现

reward [B] → 同题 [B/G,G] mean/std advantage → token IDs/labels/mask [B,L] → log_probs [B,L] → -A log p → response 内平均再 batch 平均 → microbatch 加权 backward → 单次裁剪/更新。

全同奖励组无相对信号；空响应不丢弃，损失贡献零；format 仅监控。七个标准测试和额外梯度检查通过，学习者解释仍待确认。

单卡已分开验证两半：HF policy 可做真实 forward/backward/step；vLLM 可生成并评分。两者未同时驻留，箭头 `optimizer step → sync → updated rollout` 仍未验证，不能称为端到端 GRPO。
