# P1A — Full Runner 实现与学习说明

日期：2026-10-10。范围：CPU 工程实现；真实模型 Full、SFT、DPO、Judge 均 **NOT RUN**。沿用 `cs336_alignment.qwen_baseline`，没有建立第二套模型 runner。

## Goal / Relevant Official Sources

为 Stanford CS336 **Spring 2026 Supplement** Base 四任务建立可恢复、可复算的 Full 数据链路。依据仓库 2026 handout §3、原 runner docstrings/tests、[SUP-QWEN-EVAL-v1](evaluation-protocol-v1.md) @ `09c18e7d4e966264f994f8ce2fc5deb1b385a937`、[归档规范](../archive-policy.md)和用户本轮 P1A 执行授权。Qwen 改编始终 `directly_comparable_to_official=false`。

## Concept and Formula / Tensor Shapes

```text
固定数据 + 配置 + 官方 Prompt + 本地 tokenizer
    → FULL source-order requests（复用 loader/render/select）
    → 同一个 baseline CLI → vLLM 或明确的 CPU MOCK
    → 批次 intent → 原子单条 raw → 批次 saved / progress
    → 两套从磁盘读取的聚合 → 指标一致检查
    → 原子发布 finalized/vN（scored / exports / metrics / checks / manifest / SHA）
```

输入为 Python record、UTF-8 字符串、`List[int]` token IDs；一个 batch 最多 4 个变长 token 序列，每个输入返回 1 条 completion。CPU 工程层没有训练张量、dtype/device 迁移、梯度或 optimizer。未来 vLLM 仍按冻结 BF16/TP=1 配置运行。

完成条件：`expected_ID_set == committed_ID_set`，且每个复合 `(task, example_id)` 唯一。accuracy=`correct/N`，parse failure/empty/wrong/length 全留在 N。例如 4 题只有 1 题正确、2 题无法解析，accuracy 仍为 1/4，而不是 1/2。P95 为排序后第 `ceil(.95*N)` 项；batch wall time 按 `(run, attempt, task, batch)` 去重求和。

## Planned Change / Changes Made

- `qwen_baseline.py` 增加大小写兼容 FULL、任务选择、run ID、输出父目录、数据根目录、完整模型/生成配置 JSON、dry-run/mock、显式 resume、预算和离线 score。SMOKE/PILOT 原调用保留，不迁移历史 schema 1.0。
- `qwen_baseline_storage.py` 只负责 POSIX 写入/锁/封装校验。raw schema 2.0 为**每条一个 JSONL 文件**，payload 与 `record_sha256` 一起提交，避免 raw 与独立 checksum 之间的中断窗口。
- `qwen_baseline_audit.py` 为独立磁盘复算器；只共享冻结 parser 和 sealed-file reader，不调用 runner 的 score/聚合函数。
- `scripts/verify_qwen_full_cpu.py` 可复跑全部 16,266 条输入和 MOCK IO；只归档小型工程摘要，不把 Mock 数值写入正式 scorecard。

Full 配置通过 `--config` 传入，模型 revision、tokenizer revision、sampling、engine 必须等于 P0；仅允许 tokenizer 文件位置变化。默认 tokenizer/config/data 路径以仓库相对位置记录，便于迁移；外部绝对路径需在恢复机重新挂载到相同位置。冻结配置文件中的旧 `authorized_stages` 原样保留；新 Full 真实执行另有 `--approve-full` 和正数 `--max-seconds` 门槛。这些参数不是 P1B 自动授权。

## Raw 与生命周期

Raw 保留用户要求的 schema/experiment/run/stage/task/ID/split、model/tokenizer revisions、原始 input/gold、formatted prompt/hash/token count、原文/token IDs/count、finish/stop reason、完整 generation config、request/attempt/batch、实际 execution commit 与 immutable manifest SHA。evaluator 的 parsed/correct/parse_failure 不写进 raw，而放入新版 scored，附 raw 引用、文件 SHA 和 parser SHA。

初始化 `manifest.json` 不改写，`run_code_commit/start/end` 初值 null；每次**实际启动的 Git HEAD**与软硬件、开始时间写入 `attempts/<id>/start.json`，结束/错误写入 end。最终 manifest 汇总真实 execution commit（多 commit 则列清单，不编造一个）、开始/结束时间、expected/completed/status。`archive_commit` 由归档文件 Git 历史定位，与运行 commit 分开。所有本轮 CPU 验收在 P0 HEAD 的 dirty 开发树执行，已保存准确 source SHA，不能说是在后来的归档 commit 上运行。

`progress.json` 只是原始采集进度：PREPARED / PARTIAL / FAILED / RAW_COMPLETE；**RAW_COMPLETE 不等于整个实验 COMPLETED**。唯一最终完成标志是通过 SHA/引用核验的 `finalized/vN/manifest-final.json`。finalize 在隐藏 staging 中完成 scored、候选导出、两套复算、完整性、source inventory、最终 manifest 和 SHA，全部成功后一次 rename 发布。失败 staging 保留；同版本发布后不可覆盖，新评分使用新版本。

## Resume / 用户本轮明确的恢复决定

P0 §9 曾要求对“已生成但未持久化/是否生成不明”保持保守，需明确恢复决定。本轮用户 Gate E **明确允许该崩溃边界重算，并要求不承诺 exactly-once inference**。据此实现本次 scoped 执行决定；P0 协议原文件、Prompt、parser、指标口径均未修改。

运行期间遇 infra failure 立即停止，不自动 retry。操作者明确使用 `--resume` 后，先逐条验 manifest/config/data/prompt/tokenizer/源码、raw schema/摘要/ID，然后保存事故文件摘要、已提交与缺失 ID 清单，再仅生成缺失 ID。原始有效记录不可覆盖；推理已完成但未落盘的 ID 可能被再次推理，批组成也可能变化。尚未提交的 `.pending-*` 写入残片不是 raw，不自动提升为有效结果；保留并纳入恢复证据。已命名提交的 `.jsonl` 损坏、重复或冲突则 hard stop。

例如 batch 的第 5–8 条已经推理，但只保存到第 7 条后崩溃：恢复保留 1–7 条原字节，重新处理 8 及之后的 ID；不能声称第 8 条只推理过一次。最后一条已保存但进程报错，也需显式恢复核对后才允许 finalize。

## Risks and Edge Cases

- 保证建立在支持 fsync、hard link、原子 rename 和 flock 的 POSIX 文件系统上；本地测试不证明智星云挂载已满足，P1B 要在目标持久目录重做 CPU 验收。不能直接把输出写入对象存储 URL。
- 一把进程锁阻止同 run 并发写；配置/来源在启动、恢复、采集结束和 finalize 核验。单批不再重扫全部历史，规模为边界处 O(N) 审计，加增量写入。
- 断电/磁盘实际损坏仍须依赖独立持久副本；checksum 检出损坏，不负责恢复丢失字节。
- 空答可包含非零返回 token 数；保留文本和实际 token IDs，不按显示字符推算 token。literal empty 与 whitespace-only 分开统计。
- `batch_seconds` 不是每请求延迟；已丢失且无任何 raw 的批耗时无法从 raw 恢复。attempt 耗时另外保留，避免把已知生成时间当总计费时间。
- `max-seconds` 为累计 attempt 的下一批准入预算，不能保证正在执行的批/模型加载在某一秒终止；崩溃且无 end 的 attempt 保守扣除其全部预留预算。不得通过盲目重复命令绕过预算审查。
- Full schema 2.0 与旧 schema 1.0 不混跑。历史 Smoke/Pilot 如需重评分，使用对应历史代码/既有 restore 指南；本轮不重写历史 manifest 中的源码 SHA。

## Tests Run / Result / Explanation for the Learner

见[可靠性测试](p1a-reliability-tests.md)和[readiness](p1a-readiness-report.md)。结果保存可靠、指标可复算，才使后续模型比较有可用证据；它们不证明模型能力提高，也不代表人工复核。

## Learning Check

Learner explanation status：**pending**，没有代签理解。学习检查：为什么“每个 ID 最终只保存一条有效结果”不等于“每个 ID 只做过一次推理”？为什么 empty/parse failure 必须留在 accuracy 分母中？

Next task：仅在 P1B 现场资源、持久化和预算核验并获执行授权后，运行真实 Full。
