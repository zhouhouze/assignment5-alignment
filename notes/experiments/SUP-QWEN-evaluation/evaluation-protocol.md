# 评估协议（proposal-v1 / PENDING approval）

## 不可变身份

| 项目 | 固定值 |
| --- | --- |
| Base / policy / tokenizer | Qwen/Qwen2.5-7B @ d149729398750b98c0af14eb82c78cfe92750796 |
| Judge / tokenizer | Qwen/Qwen2.5-72B-Instruct @ 495f39366efef23836d0cfae4fbe635880d2be31 |
| SFT mirror | garg-aayush/sft-cs336-assign5-datasets @ ac710ef808346bf458d7b093bfe4586cb15699d9 |
| Route | PA5 Spring 2026 Supplement Adapted Reproduction；directly_comparable_to_official=false |

数据版本以现有 [PILOT manifest 的 dataset_hashes](../../../artifacts/pa5-supplement-qwen/baseline/pilot/20261003-pilot-03/manifest.json)为基准逐文件校验，不能只写“最新数据”。Full 执行前生成有序 ID 清单、内容 SHA 和清单 SHA；MMLU ID 含 subject+原始行号，其余保留现有 loader ID，不重编号覆盖。

| Benchmark | 固定来源/划分 | 本轮只读库存 |
| --- | --- | ---: |
| MMLU | data/mmlu/test/*_test.csv，57 subjects；不用 val 调模型 | 14042 |
| GSM8K | data/gsm8k/test.jsonl | 1319 |
| AlpacaEval | data/alpaca_eval/alpaca_eval_gpt4_turbo.json；含固定 reference | 805 |
| SimpleSafetyTests | data/simple_safety_tests/simple_safety_tests.csv | 100 |

每模型共 16266 条主评估。以上是待生成数量，不是新完成数量。固定 reference 原文及 hash，不在线请求新的 GPT-4 回答。

## 生成与 Prompt

主协议延续已验收 Base greedy 配置：seed=0，n=1，temperature=0，top_p=1，max_tokens=512，batch_size=4，BF16，TP1，max_model_len=4096，gpu_memory_utilization=.75。完整其余 sampling/engine 项从 [qwen_baseline_gate.json](../../../configs/qwen_baseline_gate.json)复制进未来 manifest，包含 top_k、min_p、penalties、prefix caching、eager、EOS 与 stop。本轮不修改该配置的授权阶段。

Base 使用官方 zero_shot_system_prompt；SFT/DPO 用官方 alpaca_sft.prompt。MMLU/GSM8K 先渲染任务 prompt 再套外层。Policy 是 Base 权重，不自动加 Instruct chat template。Judge 则使用其固定原生 chat template。

为隔离模板，建议主比较沿用 stop=["# Query:"]、include_stop=false、EOS=151643；SFT/DPO 也保持同参数。P0 必须确认该字符串对 Alpaca 的语义限制：即使它不常出现，也不可看到结果后换停止规则。新增停止规则/更长上限另建诊断 run。Prompt 文件与逐题 formatted_prompt 都保存 SHA。

输入+512 超出4096不能悄悄截断、跳题；CPU preflight 统计所有模板的长度，若超限则暂停，由 P0 修订 context 协议并对全部对应组一致执行。硬件/软件变化逐项披露，不能保证跨 GPU bitwise 相同。

## 评分与完整性

MMLU/GSM8K 使用当前固定 parser、官方测试与源码 hash；parser 缺陷修复另建 evaluator v2，对所有模型同批原始输出统一重算，保留 v1。同一结果表不得混用版本。

合法失败原样保存、照规则评分。generation exception、OOM、返回条数/ID不符、写盘失败、JSONL 损坏均 hard stop，记录最后完整样本与失败上下文。无静默 retry；经批准可建立 continuation run，只补未生成样本，保留父 run、不可重抽已输出坏答案。部分完成只报进度，不能以成功子集发布 Full。

raw 分离 input/model output 与 derived scoring；生成原文不清洗。所有文件记录 sha/bytes/status；final manifest 与日志证明结束状态，不能靠目录存在判成功。复算必须从 raw 开始，核对分母与 metrics；Judge 缺失时 Alpaca/Safety = PENDING。

## 执行与分析预注册

P0 固定指标/样本/配置/分析/阈值/预算后，P1 先收 Full Base raw 和自动评分；Judge 另走可靠性子 Gate。P6 可以产出 Base/SFT 能力配对，Judge 未验收的两项保持 PENDING；P9 统一补齐三个模型的同版 Judge 评分，不能提前宣布 P1/P6 四项质量验收通过。

选择 checkpoint 只能用独立训练 validation：SFT 建议固定一 epoch 最终 checkpoint 为主（P0 确认）；DPO 按 handout 验证准确率选最高。正式 benchmark 不调参、不挑 seed、不选择 checkpoint。记录已有 PILOT 暴露程度；新诊断集在运行前冻结。

资源逐 Gate 批准；训练与 generation 顺序运行、进程退出后释放显存。72B 先预算 BF16 权重及 KV/临时内存再确定 TP，不能按现有 TP2 配置假定两张任意 GPU 足够。

## 存档设计（仅规划）

未来 artifacts/pa5-supplement-qwen/{baseline,sft,dpo}/<stage>/<run_id>/ 保存 manifests、raw、scored/vN、metrics、logs、review、SHA256SUMS；额外诊断在 evaluation-diagnostics/<run_id>/ 独立命名。Judge 在 judge/<run_id>/，关联被评输出 SHA。只在有真实产物时创建。

Git 放小文档、配置、ID/manifest、指标、人审包与 checksum；较大 raw 压缩或持久云盘/LFS（核实额度），索引可恢复路径与SHA；训练 checkpoint 必须真实保存，不能用重新下载 Base 代替。基础模型和 optimizer 软件版本可重装；精确续训需要保存当时 optimizer/scheduler/RNG 状态。
