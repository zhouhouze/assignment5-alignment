# Standard On-Policy GRPO 组件实现与测试

日期：2026-09-14。仅 standard mean/std、none importance weighting、sequence normalization。核心算法位于 `cs336_alignment/grpo.py`；`tests/adapters.py` 只保留测试 hook。官方测试、快照、评分器、数据、提示词、依赖文件均未修改。

## 来源与最小实现选择

已阅读 Spring 2026 讲义 4.2 的接口与公式、七个 adapter docstring、完整 `tests/test_grpo.py`、直接相关 fixture、`checkpoint.py` 和 `vllm_utils.py`。七个正式实现位于 `cs336_alignment/grpo.py`；`tests/adapters.py` 保留官方接口 docstring 和参数转发，只承担测试 hook。没有实现后续 variants。

本轮按用户最新指令逐个实现、逐个 targeted test，全部通过后才执行完整 suite。每项开工前在对话说明了输入/输出、形状、公式、边界和最小修改。未宣称学习者已掌握；学习检查仍待其回答。

## 各组件

以下表中 B 为响应数、L 为拼接后右移序列长度、V 为词表大小、G 为同题响应数。targeted 命令前缀为 `uv run --no-sync pytest tests/test_grpo.py -k`，后缀为 `-vv`。

| 组件 / targeted 选择器 | 数学操作与形状 | 测试 |
| --- | --- | --- |
| `test_tokenize_prompt_and_output` | prompt/response 单独分词再拼接；input_ids、labels、mask 均为 CPU int64 [B,L]，L=max拼接长度−1 | 1 passed，0.03s |
| `test_get_response_log_probs` | logits [B,L,V] → log_softmax → gather labels → log_probs [B,L]；可选 entropy=−Σp log p，[B,L]，保留浮点类型、device、梯度 | 1 passed，0.09s |
| `compute_rollout_rewards` | 每条调用 reward_fn；raw_rewards 为 CPU float32 [B]，统计 total/format/answer 均值 | 1 passed，0.01s |
| `compute_group_normalized_rewards_grpo` | [B] → [B/G,G]；A=(r−组均值)/(组样本标准差+eps) → [B]；保留奖励浮点类型和设备 | 1 passed，0.01s |
| `test_compute_policy_gradient_loss_on_policy` | 优势 [B] 或 [B,1] 广播到 [B,L]；逐 token loss=−A log p | 1 passed，0.02s |
| `test_aggregate_loss_across_microbatch_sequence` | [B,L] 先按 response mask 做序列内平均，再对 B 求平均 → 可微标量 | 1 passed，0.01s |
| `test_grpo_train_step_standard_on_policy` | 整批奖励/优势，分 microbatch forward/backward，按样本比例累积，一次裁剪/step/清梯度，返回日志标量 | 1 passed，0.08s |

所有 targeted 均是在已有本地 CPU venv 上运行，19 个测试中选择 1 个、排除 18 个。`--no-sync` 保持已装环境。完整测试第一次被 uv 默认缓存写入权限拦截，尚未进入 pytest；改用 `UV_CACHE_DIR=/tmp/o2-uv-cache` 后成功执行，无代码改动。

## 最小分词例子与边界

词表例子：Hello=3、world=4、a=7、test=8、pad=0。

```text
prompt:   Hello world      response: a test
拼接:     [3,4,7,8]
input:    [3,4,7]
labels:   [4,7,8]
mask:     [0,1,1]
```

空 response 的 mask 全为 0，不过滤该样本。有效 token 为零时，把分母夹到至少 1，损失贡献为零，仍保留在 batch 平均分母中。这是明确记录的空回答约定，不由现有快照单独验证。

不插 BOS/EOS/separator；不推断空 prompt 缺失的上下文 token；mask 与 labels 一起去掉第一列。缺少 pad token、列表长度不匹配或空批次明确报错。全批没有任何 next-token 位置时 train step 报错。

G 必须至少 2，奖励是浮点且为完整分组；G=1 的样本标准差无定义，不能靠 eps 修复 NaN。std 使用默认 correction=1，不替换为总体标准差。未实现的策略明确抛 `NotImplementedError`，没有补做 variants。

## 优势手算验证

eps=1e-6，G=8，样本标准差分母为 G−1。

| raw reward | mean | std | advantage（约值） |
| --- | ---: | ---: | --- |
| 全 0 | 0 | 0 | 全 0 |
| 全 1 | 1 | 0 | 全 0 |
| [1,0,0,0,0,0,0,0] | 0.125 | 0.353553 | 成功 +2.474867，失败 −0.353552 |
| [1,0,1,0,1,0,0,0] | 0.375 | 0.517549 | 成功 +1.207612，失败 −0.724567 |

全同奖励的 r−mean 为零，组内无法区分哪条更好；mixed 组则提升相对成功回答的对数概率、降低相对失败回答的对数概率。这是组内相对学习信号，不保证单次 optimizer step 会提高验证准确率。

## 额外确定性检查

命令：

```sh
PYTHONPATH=. UV_CACHE_DIR=/tmp/o2-uv-cache uv run --no-sync python notes/experiments/O2-standard-grpo/component_sanity.py
```

结果：PASS，输出保存为 `component-sanity-results.json`。

- 四组优势与独立 Python 手算一致；全部 finite，组内和近似零。
- 实际 r1_zero grader 对正确、格式正确但答错、空回答返回 total reward [1,0,0]；mean format=2/3，mean total=1/3，格式分未加到总奖励。
- 短响应与空响应的 shifted labels/mask 符合预期；CPU int64。
- 不等长/空序列的 sequence 平均与手算一致，prompt/pad 的梯度为零。
- [B] 与 [B,1] 优势广播一致；正优势的 loss 对 log_prob 梯度为负，负优势相反。
- return_token_entropy=False 时只有 log_probs 键，且梯度仍存在。
- 无 dropout 的相同 tiny GPT2，拆成 1、2、3 个 microbatch 后 loss 都约 0.01205245，裁剪前梯度范数约 1.561647；最终参数之间最大绝对差为 1.8626451e-9，在容差内一致，包括非整除划分。
- 标准训练真实改变参数，且梯度清空为 None；全零奖励组、无权重衰减 SGD 的参数完全不变。

Tiny GPT2 会提示 padding 未提供 attention_mask。这里遵循官方 `model(input_ids).logits` 接口与右 padding；有效的响应位置不会看到右侧 padding，padding loss 已屏蔽。未为消除提示修改官方接口或测试。

## 完整测试分类

结构迁移后本地：`UV_CACHE_DIR=/tmp/o2-uv-cache uv run --no-sync pytest tests/test_grpo.py -q --tb=short` → **7 passed / 12 failed，0.20s**。

云端正式 checkout：`uv run --no-sync pytest tests/test_grpo.py -q --tb=short` → **7 passed / 12 failed，0.24s**。fixture 模型在 CPU 上，非 GPU smoke。

| 分类 | 数量 | 说明 |
| --- | ---: | --- |
| 标准功能应通过但失败 | 0 | 七个标准功能均通过 |
| 后续变体未实现 | 12 | DrGRPO/MaxRL normalization 2；off-policy loss/GSPO 2；constant aggregation 1；variant train step 4；off-policy train step 3 |
| 环境/依赖测试失败 | 0 | uv 启动权限问题另记，重试已解决 |

12 项全部为明确的 NotImplementedError，未更新快照、跳过测试或削弱断言。全套命令按预期退出码为 1，不标为“全套测试通过”。

## 工程与产品解释

七项连接的是“输出 → 可验证奖励 → 同题相对信号 → token 概率 → 一个参数更新”。不使用 GSM8K rationale 作为 target，也不逐步评分 reasoning。元数据中的 format 指标可帮助区分交付质量与解题能力，但它不贡献 total reward。

常见错误包括 mask 错位、跨题归一化、把标准差改成方差、优势广播到错误轴、按全 batch token 平均导致长回答占更大权重、每个 microbatch 都 optimizer.step，以及错误 detach log_probs。

这些检查验证局部数学与 CPU 更新，不验证 rollout 新鲜度、NCCL 权重同步、真实 OLMo 显存、CUDA 训练或多种子收益。下一步仍需两张可用 GPU及独立阶段授权。

学习检查待用户回答：组件如何把奖励变成概率更新？为什么全零组没有信号？一个可能的 mask/梯度错误是什么？格式提升为何不等同于产品能力提升？
