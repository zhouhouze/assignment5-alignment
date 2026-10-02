# CS336 Spring 2026 Assignment 5: Alignment

Personal experiment records: [PA5 experiment index](notes/experiments/README.md)
and [archival policy](notes/experiments/archive-policy.md). This branch tracks the
independent Supplement; Main experiment evidence is linked by its original commits.

For a full description of the assignment, see the assignment handout at
[cs336_spring2026_assignment5_alignment.pdf](./cs336_spring2026_assignment5_alignment.pdf)

We will include a supplemental (and completely optional) assignment on safety alignment, instruction tuning, and RLHF at [cs336_spring2026_assignment5_supplement_safety_rlhf.pdf](./cs336_spring2026_assignment5_supplement_safety_rlhf.pdf)

If you see any issues with the assignment handout or code, please feel free to
raise a GitHub issue or open a pull request with a fix.

## Setup

As in previous assignments, we use `uv` to manage dependencies.

1. Install all packages except `flash-attn`, then all packages (`flash-attn` is weird)
```
uv sync --no-install-package flash-attn
uv sync
```

2. Run the required unit tests:

``` sh
uv run pytest tests/test_grpo.py
```

Initially, all tests should fail with `NotImplementedError`s.
To connect your implementation to the tests, complete the
functions in [./tests/adapters.py](./tests/adapters.py).

## PA5 Supplement: Official / Adapted tracks

Official configuration keeps Llama 3.1 8B and Llama 3.3 70B Instruct. The separate **Qwen Adapted Reproduction** uses Qwen2.5-7B Base and Qwen2.5-72B-Instruct Judge, with a pinned third-party SFT mirror. `directly_comparable_to_official=false`; compare Base→SFT→DPO within the Qwen track, with prompt confounders disclosed.

See the [Qwen preflight report](notes/experiments/SUP-QWEN-00-config/preflight-report.md), [configuration](configs/pa5_supplement_qwen.json), and [experiment index](notes/experiments/README.md). No Qwen model generation or training has started.
