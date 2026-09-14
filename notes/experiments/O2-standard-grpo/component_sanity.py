"""Deterministic CPU checks; run from the repo root with PYTHONPATH=."""
import copy
import json
import math

import torch

from tests import adapters as a
from tests.conftest import tokenizer, tiny_train_model
from tests.test_grpo import _train_step_inputs, _train_step_reward_fn
from cs336_alignment.drgrpo_grader import r1_zero_reward_fn


torch.manual_seed(0)
report = {"device": "cpu", "seed": 0, "groups": []}
for values in ([0] * 8, [1] * 8, [1, 0, 0, 0, 0, 0, 0, 0], [1, 0, 1, 0, 1, 0, 0, 0]):
    rewards = torch.tensor(values, dtype=torch.float32)
    advantages, _ = a.run_compute_group_normalized_rewards(rewards, 8)
    mean = sum(values) / 8
    std = math.sqrt(sum((r - mean) ** 2 for r in values) / 7)
    expected = torch.tensor([(r - mean) / (std + 1e-6) for r in values])
    torch.testing.assert_close(advantages, expected)
    assert torch.isfinite(advantages).all()
    assert abs(advantages.sum().item()) < 1e-5
    report["groups"].append({"rewards": values, "mean": mean, "std": std, "advantages": advantages.tolist()})

raw, metadata = a.run_compute_rollout_rewards(
    r1_zero_reward_fn, ["</think> <answer>18</answer>", "</think> <answer>19</answer>", ""], ["18"] * 3
)
torch.testing.assert_close(raw, torch.tensor([1., 0., 0.]))
assert metadata["mean_format_reward"] == 2 / 3 and metadata["mean_reward"] == 1 / 3
report["real_grader_no_format_bonus"] = True

tok = tokenizer.__wrapped__()
batch = a.run_tokenize_prompt_and_output(["Hello world", "Hello"], ["a test", ""], tok)
assert batch["labels"].tolist() == [[4, 7, 8], [0, 0, 0]]
assert batch["response_mask"].tolist() == [[0, 1, 1], [0, 0, 0]]
assert all(t.dtype == torch.long and t.device.type == "cpu" for t in batch.values())
report["token_example"] = {k: t.tolist() for k, t in batch.items()}

losses = torch.tensor([[2., 4., 99.], [99., 99., 6.], [99., 99., 99.]], requires_grad=True)
mask = torch.tensor([[1, 1, 0], [0, 0, 1], [0, 0, 0]])
loss = a.run_aggregate_loss_across_microbatch(losses, mask)
torch.testing.assert_close(loss, torch.tensor(3.))  # (3 + 6 + 0) / 3
loss.backward()
torch.testing.assert_close(losses.grad, torch.tensor([[1/6, 1/6, 0.], [0., 0., 1/3], [0., 0., 0.]]))
report["empty_response_and_mask_gradient"] = True

log_probs = torch.full((2, 3), -1., requires_grad=True)
advantages = torch.tensor([1., -1.])
token_loss, _ = a.run_compute_policy_gradient_loss(advantages, log_probs)
column_loss, _ = a.run_compute_policy_gradient_loss(advantages[:, None], log_probs)
torch.testing.assert_close(token_loss, column_loss)
token_loss.sum().backward()
torch.testing.assert_close(log_probs.grad, torch.tensor([[-1.] * 3, [1.] * 3]))
report["broadcast_and_gradient_sign"] = True

base = tiny_train_model.__wrapped__(tok)
scores = a.run_get_response_log_probs(base, batch["input_ids"], batch["labels"], False)
assert set(scores) == {"log_probs"} and scores["log_probs"].requires_grad
assert scores["log_probs"].shape == batch["labels"].shape
prompts, responses, truths, _ = _train_step_inputs(tok)
states = []
report["accumulation"] = []
for steps in [1, 2, 3]:
    model = copy.deepcopy(base)
    optimizer = torch.optim.SGD(model.parameters(), lr=1e-3)
    loss, meta = a.run_grpo_train_step(
        model, tok, optimizer, steps, 1.0, _train_step_reward_fn, prompts, responses, truths, 2
    )
    assert torch.isfinite(loss) and torch.isfinite(meta["grad_norm"]) and torch.isfinite(meta["token_entropy"])
    assert all(p.grad is None for p in model.parameters())
    states.append({k: v.detach().clone() for k, v in model.state_dict().items()})
    report["accumulation"].append({"microbatches": steps, "loss": loss.item(), "grad_norm": meta["grad_norm"].item()})
max_parameter_difference = 0.0
for state in states[1:]:
    for key in state:
        max_parameter_difference = max(
            max_parameter_difference,
            (state[key] - states[0][key]).abs().max().item(),
        )
        torch.testing.assert_close(state[key], states[0][key], atol=1e-7, rtol=1e-5)
assert any(not torch.equal(states[0][key], base.state_dict()[key]) for key in states[0])
report["accumulation_max_parameter_difference"] = max_parameter_difference

zero_model = copy.deepcopy(base)
zero_reward = lambda response, truth: {"reward": 0., "format_reward": 0., "answer_reward": 0.}
zero_loss, zero_meta = a.run_grpo_train_step(
    zero_model, tok, torch.optim.SGD(zero_model.parameters(), lr=1e-3), 2, None,
    zero_reward, prompts, responses, truths, 2
)
assert zero_loss.item() == 0 and zero_meta["grad_norm"].item() == 0
for key, value in base.state_dict().items():
    torch.testing.assert_close(zero_model.state_dict()[key], value, atol=0, rtol=0)
report["zero_reward_no_sgd_update"] = True
report["result"] = "PASS"
print(json.dumps(report, ensure_ascii=False, indent=2))
