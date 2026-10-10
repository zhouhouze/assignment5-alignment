# P1A — CPU 可靠性与回归验收

日期：2026-10-10。全部新生成内容为 **MOCK / TEST_ONLY**，不加载 GPU 权重。证据目录：[20261010-p1a](../../../artifacts/pa5-supplement-qwen/baseline/gate-audit/20261010-p1a/)。

## 实际命令与结果

在 Supplement worktree 使用既有本地 Python 3.12：

```bash
export PYTHONDONTWRITEBYTECODE=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
PY=/Users/hr/Documents/Lesson/assignment5-alignment/.venv/bin/python
"$PY" -m pytest tests/test_qwen_full.py tests/test_qwen_baseline.py tests/test_qwen_preflight.py tests/test_metrics.py tests/test_supplement_metrics_edges.py -q -p no:cacheprovider --tb=short
"$PY" scripts/verify_qwen_full_cpu.py --report /tmp/pa5-p1a-full-report.json
"$PY" -m pytest tests/test_data.py tests/test_dpo.py tests/test_grpo.py -q -p no:cacheprovider --tb=short
```

- 改动前已有相关测试：**43 passed in 1.68s**。
- Full selection 最窄测试：**2 passed in 0.06s**。
- 第一轮新增工程测试：**30 passed in 17.95s**。
- 实际 CLI 顺序验收：prepare（full/mock）→ run → score → validate → resume，**5/5 命令退出0**，见 `cli-acceptance.json`。
- 最终相关回归：**80 passed in 28.84s**，其中新增 37 项。详见 `tests-regression.txt`。
- 独立 Supplement 未实现项：**22 failed in 0.89s**，全部 `NotImplementedError`：SFT data 2、DPO 1、GRPO 19。详见 `tests-unimplemented.txt`，不是 Full runner 失败。单独 GRPO suite 亦重跑过，19 项同样未实现。官方 tests、snapshots、adapters 均未改。
- 首次 CLI 检查因误写指标文档路径 `metrics-spec.md` 停在 prepare，修正为 `evaluation-metrics-spec.md`；尚未产生 raw，随后完整 CLI 测试通过。

## 故障注入矩阵

| 场景 | 实测行为 | 结果 |
| --- | --- | --- |
| 正常 100 条 Safety mock | raw 唯一、完整 schema、candidate 序列化、final status/commit、二次评分原 raw 不变 | PASS |
| 第 7 条提交后 KeyboardInterrupt | 7 条逐字节保留，显式恢复只提交剩余 93 条，保存事故/可能重推理声明 | PASS |
| 子进程第 7 条后 `os._exit(77)` | 无 end/异常清理也可发现已提交 7 条，显式恢复后完整 | PASS |
| 第 100 条提交后异常 | 不允许直接 finalize；显式 resume 核对后完成，不再调用模型 | PASS |
| duplicate ID | 即使另一个文件摘要有效也停止 | PASS |
| 半行、非法 JSON、字段缺失、摘要错、token count 错、未知 ID、prompt 不符 | 返回具体 `.jsonl:1` 位置，停止评分/恢复 | PASS |
| model / tokenizer / prompt / sampling / dataset / protocol 漂移 | 拒绝 resume 合并 | PASS |
| empty / whitespace / malformed / parse failure / length / repetition | 全部原样保存一次，保留分母；不因模型表现 retry | PASS |
| generation exception（模拟 OOM）、返回数量/身份不符、raw 写失败 | FAILED/部分状态，未发布 COMPLETED | PASS |
| metrics / SHA256SUMS / final manifest 写失败 | 仅留下失败 staging，没有已发布 completed bundle | PASS |
| rename 后父目录 fsync 报错 | 撤回到 staging，未保留 completed 发布目录 | PASS |
| 原子写 link 失败、重复写 | 未提交残片保留；已有 raw 不可覆盖 | PASS |
| 同 run 第二写进程 | flock 拒绝 | PASS |
| 预算已到/已耗尽 | 批边界停，旧上限不能静默重新获得额度 | PASS |
| mock 放入正式 full 目录、真实/Mock mode 混用、dry-run 调用生成 | 在模型加载前拒绝 | PASS |
| final bundle 被篡改 | validate 检出 artifact SHA 不符 | PASS |
| 独立 MMLU/GSM 聚合 | 手算分母/parse failure/最后数字；批时间只计一次；人为改 runner score 后与独立结果不一致 | PASS |

故障注入是在本地文件系统完成，不能代替云端驱动/模型/云盘验收。模拟 OOM 测试的是异常处理链路，不是测量真实 VRAM。

## 全量 CPU 与 Mock 规模

| Task | Expected | Verified | 最大 prompt tokens |
| --- | ---: | ---: | ---: |
| MMLU | 14042 | 14042 | 1186 |
| GSM8K | 1319 | 1319 | 330 |
| AlpacaEval | 805 | 805 | 624 |
| SimpleSafetyTests | 100 | 100 | 164 |
| Total | 16266 | 16266 | — |

60 文件 dataset inventory=`8ae5c03b4f261bd7c10dd31056efde8c87b34cf580ee90f4c6aaf856ab684e55`。每任务有序 ID 和渲染 inventory SHA 均与 P0 相等；最大 prompt+512 <=4096。两次输入准备（dry 和 mock）、16266 条 Mock raw 提交、评分、独立磁盘复算、candidate schema 和最终完整性全部 PASS；`vllm_imported=false`。

实测：dry prepare 9.43s、mock prepare 7.67s、mock capture 14.76s、评分/复算/finalize/validate 13.97s。总约 46s；这是本机 CPU/磁盘吞吐，**不外推成云端 GPU 生成时间**。

Mock run：220,796,651 bytes / 24,422 files；raw 59,244,671 bytes、attempts 3,218,642 bytes、finalized 65,764,734 bytes，其余主要为 selected token IDs。Mock 每条仅 3 个合成 token，不是正式输出空间上界。临时目录位置、摘要、源码 SHA 和运行时间保存在 `full-cpu-report.json`；这些临时产物不耐久，可用脚本重新构建，不是实验数据。仅小型报告/日志提交 Git。

## 保护对象

历史 baseline **239/239 SHA** 通过；冻结协议、decision log、metrics spec、配置、parser、6 个 Prompt 共 11 文件与 P0 逐字节一致；SFT 三个原始文件的 bytes/SHA 未变；Main HEAD 未改。见 `protected-artifacts.json`。27 条既有 human review 仍 pending，正式 Full scorecard 仍 NOT RUN。
