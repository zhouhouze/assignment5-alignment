"""Core components for standard on-policy GRPO."""

from __future__ import annotations

from typing import Callable, Literal

import torch
from torch import Tensor
from transformers import PreTrainedTokenizerBase


def tokenize_prompt_and_output(
    prompt_strs: list[str],
    output_strs: list[str],
    tokenizer: PreTrainedTokenizerBase,
) -> dict[str, Tensor]:
    """Tokenize prompt/response pairs and align a response mask to labels."""
    if not prompt_strs or len(prompt_strs) != len(output_strs):
        raise ValueError("Expected nonempty, equally sized prompt and response lists.")
    if tokenizer.pad_token_id is None:
        raise ValueError("The tokenizer must define a padding token.")

    prompts = tokenizer(prompt_strs, add_special_tokens=False)["input_ids"]
    responses = tokenizer(output_strs, add_special_tokens=False)["input_ids"]
    lengths = [len(prompt) + len(response) for prompt, response in zip(prompts, responses)]
    tokens = torch.full((len(prompts), max(lengths)), tokenizer.pad_token_id, dtype=torch.long)
    mask = torch.zeros_like(tokens)
    for index, (prompt, response) in enumerate(zip(prompts, responses)):
        tokens[index, : lengths[index]] = torch.tensor(prompt + response, dtype=torch.long)
        mask[index, len(prompt) : lengths[index]] = 1

    return {
        "input_ids": tokens[:, :-1],
        "labels": tokens[:, 1:],
        "response_mask": mask[:, 1:],
    }


def get_response_log_probs(
    model: torch.nn.Module,
    input_ids: torch.Tensor,
    labels: torch.Tensor,
    return_token_entropy: bool,
) -> dict[str, torch.Tensor]:
    """Return label-token log probabilities and optional token entropy."""
    log_distribution = model(input_ids).logits.log_softmax(dim=-1)
    result = {"log_probs": log_distribution.gather(-1, labels.unsqueeze(-1)).squeeze(-1)}
    if return_token_entropy:
        result["token_entropy"] = -(log_distribution.exp() * log_distribution).sum(dim=-1)
    return result


def compute_rollout_rewards(
    reward_fn: Callable[[str, str], dict[str, float]],
    rollout_responses: list[str],
    repeated_ground_truths: list[str],
) -> tuple[torch.Tensor, dict[str, float]]:
    """Score rollouts and return raw rewards plus component means."""
    if not rollout_responses or len(rollout_responses) != len(repeated_ground_truths):
        raise ValueError("Expected nonempty, equally sized response and ground-truth lists.")

    scores = [
        reward_fn(response, ground_truth)
        for response, ground_truth in zip(rollout_responses, repeated_ground_truths)
    ]
    raw_rewards = torch.tensor([score["reward"] for score in scores], dtype=torch.float32)
    metadata = {
        f"mean_{key}": sum(score[key] for score in scores) / len(scores)
        for key in ("reward", "format_reward", "answer_reward")
    }
    return raw_rewards, metadata


def compute_group_normalized_rewards(
    raw_rewards: torch.Tensor,
    group_size: int,
    baseline: Literal["mean", "none"] = "mean",
    advantage_eps: float = 1e-6,
    advantage_normalizer: Literal["std", "none", "mean"] = "std",
) -> tuple[torch.Tensor, dict[str, float]]:
    """Compute standard GRPO mean-baselined, std-normalized advantages."""
    if baseline != "mean" or advantage_normalizer != "std":
        raise NotImplementedError("Only standard GRPO mean/std normalization is implemented.")
    if (
        raw_rewards.ndim != 1
        or raw_rewards.numel() == 0
        or group_size < 2
        or raw_rewards.numel() % group_size
    ):
        raise ValueError("Rewards must be a nonempty vector of complete groups with size >= 2.")
    if not raw_rewards.is_floating_point() or advantage_eps <= 0:
        raise ValueError("Expected floating-point rewards and positive advantage_eps.")

    groups = raw_rewards.reshape(-1, group_size)
    means = groups.mean(dim=1, keepdim=True)
    stds = groups.std(dim=1, keepdim=True)
    advantages = ((groups - means) / (stds + advantage_eps)).reshape_as(raw_rewards)
    return advantages, {
        "mean_group_reward": means.mean().item(),
        "mean_group_std": stds.mean().item(),
    }


def compute_policy_gradient_loss(
    raw_rewards_or_advantages: torch.Tensor,
    policy_log_probs: torch.Tensor,
    importance_reweighting_method: Literal["none", "noclip", "grpo", "gspo"] = "none",
    old_log_probs: torch.Tensor | None = None,
    cliprange: float | None = None,
    response_mask: torch.Tensor | None = None,
) -> tuple[torch.Tensor, dict[str, torch.Tensor]]:
    """Compute the standard on-policy loss at each token."""
    del old_log_probs, cliprange, response_mask
    if importance_reweighting_method != "none":
        raise NotImplementedError("Only on-policy loss without importance reweighting is implemented.")
    advantages = raw_rewards_or_advantages.reshape(-1, 1)
    return -advantages * policy_log_probs, {}


def aggregate_loss_across_microbatch(
    per_token_policy_gradient_loss: torch.Tensor,
    mask: torch.Tensor,
    loss_normalization: Literal["sequence", "constant"] = "sequence",
    normalization_constant: int | None = None,
) -> torch.Tensor:
    """Average masked token losses within sequences and then across sequences."""
    del normalization_constant
    if loss_normalization != "sequence":
        raise NotImplementedError("Only sequence loss normalization is implemented.")
    lengths = mask.sum(dim=-1).clamp_min(1)
    # Empty responses contribute zero, but remain in the sequence-average denominator.
    sequence_losses = per_token_policy_gradient_loss.masked_fill(~mask.bool(), 0).sum(dim=-1) / lengths
    return sequence_losses.mean()


def grpo_train_step(
    model: torch.nn.Module,
    tokenizer: PreTrainedTokenizerBase,
    optimizer: torch.optim.Optimizer,
    gradient_accumulation_steps: int,
    max_grad_norm: float | None,
    reward_fn: Callable[[str, str], dict[str, float]],
    repeated_prompts: list[str],
    rollout_responses: list[str],
    repeated_ground_truths: list[str],
    group_size: int,
    baseline: Literal["mean", "none"] = "mean",
    advantage_eps: float = 1e-6,
    advantage_normalizer: Literal["std", "none", "mean"] = "std",
    importance_reweighting_method: Literal["none", "noclip", "grpo", "gspo"] = "none",
    old_log_probs: torch.Tensor | None = None,
    cliprange: float | None = None,
    loss_normalization: Literal["sequence", "constant"] = "sequence",
    normalization_constant: int | None = None,
) -> tuple[torch.Tensor, dict[str, torch.Tensor | float]]:
    """Run one standard on-policy update with gradient accumulation."""
    del old_log_probs, cliprange, normalization_constant
    if (baseline, advantage_normalizer, importance_reweighting_method, loss_normalization) != (
        "mean",
        "std",
        "none",
        "sequence",
    ):
        raise NotImplementedError("Only the standard on-policy GRPO train step is implemented.")

    batch_size = len(rollout_responses)
    if not 1 <= gradient_accumulation_steps <= batch_size:
        raise ValueError("gradient_accumulation_steps must be between 1 and batch size.")

    raw_rewards, metadata = compute_rollout_rewards(
        reward_fn, rollout_responses, repeated_ground_truths
    )
    advantages, group_metadata = compute_group_normalized_rewards(
        raw_rewards,
        group_size,
        baseline,
        advantage_eps,
        advantage_normalizer,
    )
    metadata.update(group_metadata)
    batch = tokenize_prompt_and_output(repeated_prompts, rollout_responses, tokenizer)
    if batch["input_ids"].shape[1] == 0:
        raise ValueError("At least one sequence must contain a next-token prediction.")

    device = next(model.parameters()).device
    advantages = advantages.to(device)
    total_loss = torch.zeros((), device=device)
    total_entropy = torch.zeros((), device=device)
    optimizer.zero_grad(set_to_none=True)
    model.train()
    for indices in torch.arange(batch_size).tensor_split(gradient_accumulation_steps):
        microbatch = {key: value[indices].to(device) for key, value in batch.items()}
        scores = get_response_log_probs(
            model,
            microbatch["input_ids"],
            microbatch["labels"],
            return_token_entropy=True,
        )
        token_loss, _ = compute_policy_gradient_loss(
            advantages[indices.to(device)], scores["log_probs"]
        )
        weight = len(indices) / batch_size
        loss = aggregate_loss_across_microbatch(
            token_loss, microbatch["response_mask"]
        ) * weight
        if not torch.isfinite(loss):
            raise FloatingPointError("Non-finite GRPO loss.")
        loss.backward()
        total_loss += loss.detach()
        total_entropy += aggregate_loss_across_microbatch(
            scores["token_entropy"].detach(), microbatch["response_mask"]
        ) * weight

    grad_norm = torch.nn.utils.clip_grad_norm_(
        model.parameters(),
        float("inf") if max_grad_norm is None else max_grad_norm,
        error_if_nonfinite=True,
    )
    optimizer.step()
    optimizer.zero_grad(set_to_none=True)
    metadata.update(
        {
            "loss": total_loss.item(),
            "grad_norm": grad_norm.detach(),
            "token_entropy": total_entropy,
        }
    )
    return total_loss, metadata
