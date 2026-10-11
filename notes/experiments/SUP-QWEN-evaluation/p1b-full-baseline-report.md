# P1B-1 — Qwen2.5-7B Full Base Baseline

日期：2026-10-11。实验身份：PA5 Supplement Adapted Reproduction；`directly_comparable_to_official=false`。这是 Spring 2026 Supplement 路线，不是 Main O1/O2，也不替代官方 Llama 结果。

状态：`GENERATION_SCORING_RESTORE=COMPLETE`；GitHub归档等待实际push/远端核对，本轮收尾回执将分别记录run_code_commit与archive_commit。

## Objective

在冻结 SUP-QWEN-EVAL-v1 下完成 Base 全量输出，建立后续 SFT/DPO 的逐题比较起点，并实际验收周期备份、全量评分和独立恢复。假设是现有单卡 Runner 能在预算内保留全部真实输出并给出可复算指标；本轮没有训练收益假设或模型间因果结论。

## Configuration

执行分支 `learning/pa5-supplement`；四任务实际 clean run_code_commit=`47ae79f3f1c5fdf390ef23bfc9f8bd41b23d2726`。独立归档提交由本文件 Git History / 最终同步回执定位，不把后来的文档提交写成推理源码。

协议 commit=`09c18e7d4e966264f994f8ce2fc5deb1b385a937`；协议 SHA256=`879764bf6f0286439cdf9527a7c9bdda93d064d4a157676851d79cf69145bcd3`。本轮不改数据、Prompt、Parser、采样或模型版本。

采样：seed=0、n=1、temperature=0、top_p=1、top_k=-1、min_p=0、max_tokens=512、min_tokens=0；stop=["# Query:"]、stop_token_ids=[151643]、include_stop_str_in_output=false、ignore_eos=false；presence/frequency penalty=0、repetition_penalty=1；detokenize=true、skip_special_tokens=true、spaces_between_special_tokens=true。四任务 batch_size=4。

vLLM：BF16、TP=1、max_model_len=4096、gpu_memory_utilization=0.75、max_num_seqs=4、max_num_batched_tokens=4096、enforce_eager=true、prefix_caching=false、generation_config=vllm、trust_remote_code=false。使用正式 textual prompt，不套 chat template；add_special_tokens=false。完整配置以各任务原始 manifest 为准。

## Dataset

MMLU test 14,042（57 学科）、GSM8K test 1,319、AlpacaEval 805、SimpleSafetyTests 100，总计16,266。每个任务独立 run/manifest，顺序运行；这些 task-subset run 的并集覆盖全量，不能将单个 manifest 称为四任务 run。60个数据文件、8项 tokenizer/config 及渲染 ID/prompt inventory 逐项由原 Runner 验证。版本、SHA、split、Prompt/hash 见各 manifest，不混用 Pilot 的20例分数。

## Model

`Qwen/Qwen2.5-7B` Base；模型与 tokenizer revision=`d149729398750b98c0af14eb82c78cfe92750796`。四个权重分片及3项配置/index共15,231,300,464 bytes现场SHA通过，无重新下载。可下载的模型/环境只保存版本、依赖锁、恢复脚本与校验记录，不提交权重。

硬件：1×RTX5090，32,607MiB；driver595.84；Python3.12.13、Torch2.10.0+cu129/CUDA runtime12.9、vLLM0.19.1、Transformers5.7.0、FA2.8.3、tokenizers0.22.2。Mac备份与恢复是CPU验证，不加载模型。峰值及结束资源见 runtime/cost 报告。

## Evaluation Method

MMLU使用冻结选项Parser；GSM8K使用冻结 final-number Parser。正确率分母包括全部样本，合法空答/错答/length结果不跳过、不重采样。MMLU主指标是题目加权micro accuracy；57学科等权macro仅诊断。

四任务原始输出均作版本化派生 scored/metrics。AlpacaEval/Safety只有候选回答：Win Rate=NOT RUN，LC=NOT VALIDATED，Safety Rate=NOT RUN。解析成功不等于语义正确；最终答案正确也不验证推理过程。

原 Runner完整性验证→score v1→独立磁盘读取/frozen parser复算→Mac独立恢复后再次 Runner验证/复算。没有因分析发现而改 v1 gold、Parser或正式分数。

## Results

| Task | Actual/Expected | Correct / Accuracy | Parse failures | Empty | Avg / P95 tokens | length | Examples/s |
| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| mmlu | 14042/14042 | 9813/14042 = 69.8832% | 0 | 0 | 18.85 / 33 | 0 | 9.3209 |
| gsm8k | 1319/1319 | 929/1319 = 70.4321% | 0 | 0 | 196.98 / 369 | 3 | 0.9400 |
| alpaca_eval | 805/805 | Judge NOT RUN | N/A | 0 | 275.61 / 512 | 97 | 0.6573 |
| simple_safety_tests | 100/100 | Judge NOT RUN | N/A | 0 | 104.20 / 257 | 0 | 1.5293 |

总计16,266/16,266；四个REAL/FULL run均完成。GSM8K length=3/1319=0.2274%，AlpacaEval length=97/805=12.0497%。finish distribution、token histogram、batch latency和逐学科结果见Git证据analysis/；mean/median/P95与原Runner一致，CI未计算（null）。

## Raw Artifact Paths

run_id统一前缀 `qwen-full-20261011T034800Z`，后接 `-mmlu` / `-gsm8k` / `-alpaca_eval` / `-simple_safety_tests`。ID时间只是标识，实际起止时间以attempt记录为准。

- 云端：`/root/pa5-supplement-setup/full/<run_id>`；系统盘，不保证释放实例后恢复。
- Mac CAS：`/Users/hr/Documents/Lesson/pa5-experiment-backups/full/<run_id>`，需保留 objects、snapshots 和 LATEST。
- Mac独立恢复：`/Users/hr/Documents/Lesson/pa5-experiment-backups/restored/<run_id>`。
- 完整便携压缩包、bytes/SHA、恢复命令见 [portable-archive.json](../../../artifacts/pa5-supplement-qwen/baseline/full/20261011-p1b1/portable-archive.json)。
- Git小型证据见 [Full evidence](../../../artifacts/pa5-supplement-qwen/baseline/full/20261011-p1b1/README.md)；登记在 [artifact registry](../artifact-registry.json)。原始单条sealed JSONL与完整scored未复制进Git；仍完整保存在上述已验证副本。

## Error Analysis

全部4,619条自动判错（MMLU4,229/GSM390）都有taxonomy/routing记录。未经逐题归因的条目明确UNKNOWN/PENDING，不把wrong score自动转成Capability Error。抽样标签均为 **AI INITIAL ANALYSIS**，human_review_status=**PENDING**；审阅数量、抽样seed/stratum和原文见 review packet。

GSM抽中的10条wrong中，5条明确算到gold对应答案，但最后又提到题目中的数字，使last-number Parser提取其他数。这是语义答案与提取契约不一致的评估设计候选，并非已确认 Parser实现偏离规范；Prompt也未明确要求“最后数字必须是答案”。不能从该样本推算总体修正分数。正式70.43%保持不变。

其他抽样可见漏条件、混淆所求量、计算不一致。MMLU virology:81另有参考答案与ICTV原始资料不一致的候选；需人审裁决，正式计分不变。具体证据与产品解释见 [Base行为画像](qwen-base-behavior-profile.md)。

## Representative Examples

| Case | 原始评分/现象 | AI初步诊断（待人审） |
| --- | --- | --- |
| GSM605 | parsed=6，gold=42，wrong | 算到42美元，末句又写6小时；提取契约/语义不一致 |
| GSM656 | parsed=20，gold=10，wrong | 20天是读完所需时长，遗漏30−20求提前天数 |
| GSM1215 | wrong | 先算出864与偏差36，随后混用总数/类别，并把3000−864写成100 |
| MMLU college_mathematics:50 | B，gold A | 正数域中两边取log后恒等；选择错误，内部原因未知 |
| MMLU virology:81 | B，gold C，wrong | ICTV描述丝状，支持B；参考争议待裁决 |
| Alpaca0 | length/512；Judge NOT RUN | 流畅列表中的可核实事实错误、重复Viola Davis、句中终止 |

原始全文、formatted prompt、gold/frozen score和raw SHA保留于复核包；此表只是导航。Primary source：[ICTV Filoviridae](https://ictv.global/report/chapter/filoviridae/filoviridae)、[IBDB Three Days of Rain](https://www.ibdb.com/broadway-production/three-days-of-rain-403589)，2026-10-11访问。非经人工裁决结论。

## Limitations

单seed/单模型/单硬件；不作模型优越性或训练改善结论。未运行Judge、LC验证、人工复核和独立benign false-refusal集；不能报告偏好胜率、正式安全率或上线质量合格。length是机器终止原因，只有读到语义未完成才标provisional Truncation。吞吐按unique batch wall-time汇总，排除load/write，不是用户请求端到端延迟。

样本分类不是总体错误构成；原Benchmark错误也不能直接进入SFT/DPO。Mac CAS、独立目录和tar都在同一Mac磁盘，虽独立于云实例，仍不等于异地容灾。释放实例后的保留期限/恢复能力未知，绝不以此作为唯一证据保障。

## Reproducibility

缺失/重复/额外ID/损坏记录/manifest mismatch均为0，四任务原Runner验证与OFFLINE_RECOMPUTATION=PASS。四次quiescent备份均deferred=[]；SOURCE_SHA256=BACKUP_SHA256=RESTORED_SHA256。

| Task | Final snapshot | Files | Restored raw |
| --- | --- | ---: | ---: |
| mmlu | `327c92e711bd46288c9637dede910792` | 21081 | 14042 |
| gsm8k | `22a9ac4678474a5e805acaf415eb6203` | 1996 | 1319 |
| alpaca_eval | `5d42fa8483ed400486ea78b781cf23fc` | 1227 | 805 |
| simple_safety_tests | `e0ae261c4b9a4fd4a56a5417f8f0a438` | 168 | 100 |

便携归档 27,342,802 bytes（约26.08MiB），解压逻辑总量237,170,700 bytes；24,472个成员SHA逐一复核PASS。tar SHA256=`c9167497a800d803f2510f55201654465e376b905154e796f9c587150777b6a9`。44条复核包原文保留，human completed=0；4,619条wrong路由中12条AI初步归因、4,607条UNKNOWN，全部holdout禁止训练准入。

未修改核心源码、正式测试或冻结协议。工程测试前置证据：P1A 80项CPU tests、P1B-0.5 Mac/Linux各24项已通过；本轮实际验收以四真实run的完整性/独立复算/恢复及tar逐成员SHA为准，没有用历史CPU Mock冒充模型Full。

CPU分析时曾用Unicode str.splitlines读取JSONL，使字符串内Unicode行分隔符被误切；已在外部分析脚本中改为按物理LF逐行读取。原JSONL与Runner验证本来有效，没有修改原文或Parser、没有generation重试。该问题不计作模型或GPU infra failure。

## Product Interpretation

Base表现同时受能力、输出行为、长度上限和评估契约影响。后续应对同题固定协议比较Base/SFT/DPO，并保留独立Prompt对照Gate；不能把不同Prompt下的分数变化全部归因训练。流畅列表不保证事实可靠，正确中间结果不保证评分器选到了语义答案。

## Next Gate

仅建议 **P2 SFT Dataset Acceptance**，其后 **P3 SFT CPU Pipeline Implementation**。现有SFT24条空字段的准入/人审问题仍待按已批准策略验收。本轮不执行过滤、SFT、DPO、72B Judge、2×2 Prompt Control或Main O1/O2；完成归档后停止。
