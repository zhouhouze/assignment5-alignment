# Supplement概念图谱

Base + zero-shot提示 → 四类baseline（知识/数学/assistant quality/安全）。

SFT：instruction-response demonstrations → packed next-token训练 → 观察指令遵循、风格、能力和安全变化。

DPO：固定SFT reference + chosen/rejected pair → 提升相对偏好概率 → 检查偏好收益与能力损失。

评估证据：raw输出 → 可复算parser/judge → 指标 → 人工复核 → 有边界的结论。标签格式、外层prompt与judge错误均可能成为混杂因素。

2026-10-02：运行代码commit → manifest（配置/版本/hash）→ immutable raw → 新版scored → metrics → report → Git归档commit。归档成功与实验成功分别记录，partial/failed不能冒充full。

## 2026-10-02 Qwen adapted preflight

Adapted reproduction → 固定policy/judge/tokenizer/data revision → CPU验收 → baseline → Alpaca+EOS SFT → 同SFT checkpoint policy/reference DPO；模型/评估标尺与prompt confounder必须披露。数据schema / 内容质量 / 人工复核为不同Gate。

## 2026-10-02 Qwen Baseline CPU Gate

新增qwen_baseline runner、独立Gate配置与7B限定下载脚本；四任务CPU准备通过，42项测试通过。raw逐请求独立封存，scored按版本派生；合法空答保留，pending/infra失败阻断自动恢复。无训练核心变更，学习解释pending。下一步按已授权范围进行SMOKE→PILOT。

## Qwen Baseline GPU Gate（2026-10-03）

配置/来源冻结 → 权重验收 → SMOKE链路验收 → PILOT行为诊断 → immutable raw → versioned scoring → 独立复算 → AI分析与human review分离 → Git证据。GSM906：分项正确≠给出要求总数；Alpaca111：流畅文本≠完成指令。stop标记被剥离≠模型未尝试续写下一题。小样本pilot≠正式benchmark。理解状态pending。

## 2026-10-10 Evaluation / Data Flywheel

固定模型/数据/Prompt/Judge协议 → immutable raw → 同题配对与Prompt 2×2 → 能力/偏好/解析/安全错误分离 → 人工复核 → 独立SFT示范或DPO偏好候选 / regression / evaluator fix → 来源、隐私、去重、holdout隔离与准入 → 下一轮单变量实验。训练loss、Judge偏好、用户满意度不是同一指标。当前仅规划，理解状态pending。

## 2026-10-10 P0 freeze

协议身份/版本/hash冻结 → 全量输入CPU核验 → 实现ready与运行现场条件分别验收 → candidate输出/自动评分 → Judge与人审独立状态。P95/empty口径须由实际实现与协议对照；产品阈值缺失不妨碍描述性评估，但不能宣称产品上线合格。

## 2026-10-10 P1A evidence chain

固定协议/config/data/Prompt → CPU全量selection+tokenization → batch intent → fsync+exclusive atomic raw commit → 已提交ID集合 → 显式恢复缺失ID（未持久化推理可能重复）→ 两套磁盘复算 → 原子final bundle → SHA与独立持久副本。80项工程测试和16266条Mock通过≠真实Full完成，RAW_COMPLETE≠模型质量达标。学习确认pending。

P1B-0：代码/协议一致 ≠ 当前GPU/权重可用 ≠ 数据可持久恢复 ≠ 预算与执行获批。SSH断开前已提交raw的可靠性和云实例释放后数据保留是不同的保证；两者均需明确证据。

P1B-0.5：生成提交边界 → Raw稳定捕获 → SHA内容对象 → 原子snapshot/LATEST → 独立恢复验证 → ack续期。备份RPO不为零；guard只减少失联后继续产出的窗口，不保证释放实例后的未同步数据。quiescent事故pending与有效Raw是两个集合。

## 2026-10-11 P1B-1 full evidence

冻结协议 → REAL16,266条不可变raw → v1评分 → 独立磁盘复算 → quiescent/SHA/独立恢复 → Git证据索引。parse成功≠语义答案一致；length终止≠语义截断；错分≠已知能力归因；AI初析≠人审。holdout错误只指导独立来源候选，不复制或改写进入训练。Judge/人审/训练仍独立未完成。学习确认PENDING。

## 2026-10-16 Human Evaluation Round01

不可变44条source packet → (task,id,run,raw SHA) join → 用户裁决append-only sidecar → human COMPLETED与adjudication UNCERTAIN/PENDING正交 → confirmed/candidate/auxiliary分别计数 → Safety父子标签单事件 → 样本内PM复盘，holdout禁止训练。reviewed_at UNKNOWN≠recorded_at；Codex记录身份≠用户人工审核身份。

## 2026-10-16 PM-04 preregistration

不可变Full/人审证据（含UNKNOWN）→ H1约束/完成、H2助手、H3安全+帮助、H4能力、H5训练×Prompt → 固定指标/完整分母/配对人审 → paired CI与unknown界限 → 条件式PM调查/继续/暂停建议 → P2未来审计需求。Design Complete≠PM Review Approved≠P2 execution；threshold/预算/新样本仍待批。

## 2026-10-28 P2-A.1

Pinned Raw SHA → schema hard stop → exclusive reasons per field → unique row identity → measured counts/report. Raw PASS ≠ Derived acceptance ≠ training quality. Learner explanation PENDING.

## 2026-10-28 P2-A.2

Raw fingerprint → approved empty-field decision → retained bytes + excluded source IDs + complete mapping → independent count/content/SHA verification → exact split overlap → machine acceptance. Sample/train inclusion is expected; exact overlap0 does not exclude semantic contamination. Data Admission and learner explanation remain PENDING.

## 2026-10-28 P2-B.1

Frozen identity → transient normalized/5-gram index → exact/normalized/anchor-retrieved candidates → independent emitted-hit validation → pending human/context disposition. Field hits ≠ unique record pairs ≠ contamination prevalence; shared quotation containment1 can coexist with low Jaccard. Zero lexical hits ≠ semantic clearance.
