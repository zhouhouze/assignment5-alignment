# Qwen Baseline CPU dry-run

directly_comparable_to_official=false。日期2026-10-02。用户新批准CPU→每任务1条SMOKE→每任务20条PILOT；无FULL/SFT/DPO/Judge权限。

## Goal / Official Sources

建立四个官方Supplement benchmark的可审计Base推理链路。依据本仓库Spring2026 Supplement handout第3节、官方prompts_safety、test_metrics与已通过的Supplement parsers。未更改benchmark/prompt/parser。

## Concept / Shapes / Planned Change

官方数据→固定ID/seed抽样→任务prompt→纯文本system wrapper→token IDs列表→vLLM单completion→逐条raw→独立scored→指标。无训练tensor/backward/optimizer；输入为各长度L_i的int token列表，最多4条组成batch。MMLU字母比较；GSM8K用既有final-number parser抽取，再Decimal精确数值比较，格式不可解析计错误。Alpaca/Safety评分null、等待Judge。
新增独立qwen_baseline模块、单独Gate配置与7B限定下载脚本；不接触SFT/DPO核心hooks。

## CPU Result / Tests

PASS：四任务各1条真实输入已完成加载、tokenization、prompt、ID、manifest、JSON序列化与parser路径探测，未进行模型生成。正式数据数量14042/1319/805/100。
`python -m pytest tests/test_qwen_baseline.py tests/test_qwen_preflight.py tests/test_metrics.py tests/test_supplement_metrics_edges.py -q --tb=short`：42 passed，原30项不退化。
新增覆盖固定抽样、MMLU20科目、Safety10个分层单元、gold不泄露、无chat包装、评分规则、空答保留、排除Judge假分数、原始文件不可覆盖、pending恢复阻断、manifest/raw损坏、ID漂移。

## Reliability / Resume

raw每个request独立JSONL，exclusive创建、fsync并配SHA；manifest、selected_examples、代码、prompt、数据hash在批前验证。模型调用前写pending，整批输出确认/逐条落盘后才移除pending。恢复只接受已封存记录，不重采样；pending、failed、数量/ID/hash/JSON/写入错误hard stop。中断发生在批间可从已确认ID后继续；批内状态未知必须人工解决，不能自动重试。score版本独立目录，raw不修改。

## Configuration / Hypothesis

Qwen2.5-7B Base，model/tokenizer revision d149729398750b98c0af14eb82c78cfe92750796；greedy0/top_p1/seed0、max_tokens512、stop # Query:、EOS151643、BF16、TP1、batch4、max_model_len4096、显存0.75、enforce_eager=true、禁用prefix cache。eager/prefix设置为本次工程选择，后续对比固定。
假设：官方纯文本prompt可被Base接受；pilot用于检验输出/解析/终止/长度，而非证明准确率。MMLU跨20科目；Safety每harm_area/category抽2条；其他固定随机20条。smoke取各任务pilot第一条，之后pilot仍独立生成；不把这种设计成的重叠误称失败重试。

## Artifacts / Next Gate / Learning Check

CPU evidence：artifacts/pa5-supplement-qwen/baseline/cpu-dry-run/20261002-01；tests日志在preparation-20261002。无模型raw/metric冒充dry-run结果。
下一步已授权：固定代码提交，云端CPU复核，下载指定7B完整权重与hash；先4条SMOKE，通过infra验收后80条PILOT。遇到列明infra故障立即停止，不自动绕过。人审字段pending。
学习检查待答：为什么空答可以是合法模型结果，而返回数量不符必须停止？为什么batch耗时不能直接当逐请求latency？
