# O1 Prompt Baselines 历史实验数据归档复现报告

日期：2026-09-14。实验 ID：`20260914-190540`。状态：自动复现和归档完成，人工复核待填写。

## 环境与执行

- 云端：智星云，1 × NVIDIA GeForce RTX 5090 32,607 MiB
- Python 3.12.7；Torch 2.10.0+cu129；CUDA runtime 12.9
- Transformers 5.7.0；vLLM 0.19.1；FlashAttention 2.8.3
- 独立分支：`learning/o1-reproduction-20260914`
- 历史生成代码：`a75ef3db48e3bbf293def0441f0229f6d1371254`
- 模型 revision：`a1847dff35000b4271fa70afc5db10fd29fedbdf`

预检中的数据、三份 prompt、grader 和生成脚本 SHA-256 均与历史记录一致。可靠性测试结果为 `5 passed`。1-example smoke 共 3 条，20-example pilot 共 60 条，均通过数量、ID、落盘和 grader 重算检查。Pilot 指标与历史 Pilot 一致。

Full 从 19:11:55 开始，约 19:23:58 完成。三组各产生 1,319 条记录，共 3,957 条；不存在残留 partial 文件。48 个完整归档文件的 SHA-256 复验全部通过。GPU 在生成结束后回到约 15 MiB。

## Full 结果

| Prompt | Cat1 | Cat2 | Cat3 | Accuracy | Format | Avg tokens | Empty | Length | Runtime |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `question_only` | 1 | 222 | 1,096 | 0.08% | 16.91% | 258.4 | 30 | 449 | 389.6s |
| `r1_zero` | 1 | 839 | 479 | 0.08% | 63.68% | 94.3 | 0 | 10 | 144.4s |
| `r1_zero_three_shot_gsm8k` | 245 | 996 | 78 | 18.57% | 94.09% | 111.7 | 0 | 8 | 156.6s |

`question_only` 和 `r1_zero` 的 Cat1/2/3 数量与历史 Full 完全一致。three-shot 相比历史结果：Cat1 `+10`、Cat2 `-24`、Cat3 `+14`；accuracy `+0.76` 个百分点，format rate `-1.06` 个百分点。

## 复现判断

- Configuration reproduction：**PASS**。历史生成 commit、模型名称、数据、prompt、grader 和采样参数均已固定并核对。
- Aggregate-result reproduction：**PASS with expected stochastic variation**。前两组类别分布完全一致，three-shot 汇总指标接近但不相同。
- Sample-level reproduction：**NOT VERIFIABLE**。旧 AutoDL 的逐题 raw JSONL 不存在，不能进行逐题比较，也不声称响应逐 token 一致。

相同 seed 不保证跨机器、驱动和 GPU kernel 的逐 token 确定性。本次 three-shot 差异不覆盖 2026-07-16 的历史正式结果。

## 人工复核状态

已使用固定 review seed `20260914` 生成 Category 2 和 Category 3 各 12 条 review packet；每个类别从每种 prompt 抽取 4 条。packet 保留题目、完整 response、ground truth、parsed answer、grader 结果、finish reason 和 token count。

人工字段仍为空。自动归档完成不等于人工复核完成，不能把 grader 结果称为人工结论。

## 归档

- 规范化 raw JSONL：`artifacts/O1-prompting-baselines-reproduction/20260914-190540/raw/`
- Metrics：`artifacts/O1-prompting-baselines-reproduction/20260914-190540/metrics/`
- Manifests：`artifacts/O1-prompting-baselines-reproduction/20260914-190540/manifests/`
- Logs：`artifacts/O1-prompting-baselines-reproduction/20260914-190540/logs/`
- Review packets：`artifacts/O1-prompting-baselines-reproduction/20260914-190540/review/`
- 完整运行压缩包：`artifacts/O1-prompting-baselines-reproduction/archives/20260914-190540.tar.gz`
- 压缩包 SHA-256：`407ae5d2170994816ee4bcc15d5278ac59191bf3423458b82e00164ac2330607`

原始生成脚本只持久化 response token 数量，没有持久化 token IDs；规范化 schema 将 `response_token_ids` 明确设为 `null`。这不影响 response、reward、类别和长度指标的复算。
