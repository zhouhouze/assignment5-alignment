# Supplement parser前置验证（PREPARATION，非Baseline结果）

## Objective

实现官方MMLU与GSM8K答案提取，独立于Main boxed/R1 grader。架构：模型文本 → supplement_metrics → parsed_answer/None → 未来评估器比较gold；本轮仅完成提取节点与adapter连接。

## Configuration

在Supplement worktree使用本地Python3.12.13，HF/Transformers offline；未调用生成。输入str，输出str或None，无tensor、dtype、device或梯度操作。

## Dataset

官方tests/test_metrics.py的固定例子及新边界测试；未在MMLU/GSM8K全量模型输出上评测。新增16个测试覆盖冲突声明、词边界、gold泄漏、负数、小数、千分位、Unicode减号、空答等。

## Model

解析测试不加载8B/70B。Supplement全套中的DPO测试仅加载仓库tiny GPT2夹具。

## Evaluation Method

- MMLU：官方句式“The correct answer is X”（大小写不敏感）提取A-D；也接受单独字母，可带句点/右括号。重复同一声明可解析，多个不同明确声明返回None。不猜选项文字，不读取gold。
- GSM8K：按顺序提取带符号十进制数字，返回最后一个；去除合法千分位逗号，Unicode减号转ASCII。不会运算表达式、解释文字数字或用boxed定位。
- 官方handout §3.1/§3.2与adapter docstring为准；未修改官方tests或snapshot。

## Results

依次执行 `pytest tests/test_metrics.py -k mmlu -q --tb=short` → 2 passed；`-k gsm8k` → 2 passed。完整命令及解释器见test-results.json。

`pytest tests/test_data.py tests/test_dpo.py tests/test_metrics.py tests/test_supplement_metrics_edges.py -q --tb=short` → **20 passed / 3 failed**。其中官方Supplement为4 passed/3 failed，额外边界16 passed。3个失败均为尚未实现的SFT dataset（2）和DPO loss（1），不是parser故障；batching尚未独立触达。

按项目要求另跑完整tests/test_grpo.py：19 failed，均为本分支官方Main脚手架NotImplementedError。该分支刻意未带入个人Main实现，因此不是Main O2历史测试回归，也不能用来推翻O2既有记录。

## Raw Artifact Paths

`artifacts/pa5-supplement/audit/20261002-preflight/`：mmlu-tests.txt、gsm8k-tests.txt、supplement-tests.txt、official-grpo-scope-check.txt、test-results.json。所有日志均为本轮真实测试输出，不是实验generation raw。

## Error Analysis

MMLU采用较严格协议，对“option B”、选项全文或复杂markdown可能返回None；其后应在pilot按parse failure分析，若改规则需版本化重评分，不能覆盖raw。GSM8K最后数字可能来自附加叙述而非答案；这是手册指定规则的已知限制。

## Representative Examples

- “A is tempting, but the correct answer is D.” → D，避免误取最先出现的A。
- “The correct answer is A. The correct answer is B.” → None，避免静默猜测。
- “The amount is $1,234.50.” → 1234.50。
- “First 72, correction 73.” → 73。

这些是测试文本，不是模型实际生成或人工评测结果。

## Limitations

未证明全量评估质量；fraction/scientific notation不作为整体数学数值解释，示例“1/2”提取最后数字2，“1e3”提取3，不能将其当作正确数值归一化。后续遇到此类输出应单列错误类型，必要时提出新版本协议，避免悄悄改变实验定义。字符串是否与gold等价由后续评估逻辑负责，本轮未实现完整scorer。

## Reproducibility

代码：cs336_alignment/supplement_metrics.py；adapter只转发。来源与hash随preflight manifest归档；测试使用固定输入，无采样。禁止把本轮20个通过测试写成20题模型答对。

## Product Interpretation

解析器决定产品评估“看到什么答案”。严格协议提高可追溯性，但也可能低估不遵循输出格式的模型；必须同时报告accuracy与parse failure。标准答案不可参与提取，避免评估泄漏。

## Next Gate

Next task：环境/HF权限与来源审计完成后，等待批准开发baseline runner及小样本generation；不在此轮执行。学习检查待用户回答：最后一个数字为什么可能不是最终答案，parse failure与能力失败有何区别？
