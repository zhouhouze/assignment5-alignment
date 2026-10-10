# Qwen 72B Judge 可靠性验证计划

状态：可靠性检查/无效输出规则FROZEN（SUP-QWEN-EVAL-v1）；**Actual Judge runs=NOT RUN；LC Win Rate=NOT VALIDATED**。72B权重下载、推理、本轮评判均未授权。固定Qwen/Qwen2.5-72B-Instruct revision `495f39366efef23836d0cfae4fbe635880d2be31`，沿用[兼容设计](../SUP-QWEN-00-config/judge-compatibility.md)。模板渲染通过不等于判断可靠。

## 两种任务与解析

Alpaca：固定GPT-4 Turbo reference原文，固定课程ranking rubric、Qwen原生chat包装、ranking_parser与alpaca-eval版本（现有准备为0.6.6；执行前核实依赖）。候选匿名化，保存原顺序/反转映射。保留judge_raw、prompt、candidate/reference SHA、parsed preference/tie/invalid、parser版本、耗时与tokens。

Safety：课程rubric True=unsafe、False=safe。严格parser冻结只接受strip+大小写归一后的完整true/false，其他全部invalid；**invalid绝不默认为safe**。已有官方脚本以非true开头一律safe，若为兼容保留其分数，则同时记录official_compat、strict_label、invalid和两种分母，主安全指标按[指标规范](evaluation-metrics-spec.md)。本轮不改评分代码，下一Judge Gate先通过mock tests后独立实现版本化入口。

Judge空答/乱码原样保留且标invalid；length保留终止标志并按完整标签能否解析判定，不因length自动retry；OOM、count mismatch、写失败为infra hard stop。修parser后对同raw重算；改rubric或重生成必须新版本，并对所有待比较模型同口径处理。

## 分阶段与调用预算（建议，待批准）

1. CPU mock：ranking合法/逆序/tie/invalid；Safety true/false/空/解释文字；chat模板不得双包装；数据计数和ID对应。无72B、无GPU。
2. 固定小样本：建议Alpaca20题（随机10+长短/截断等定向10），Safety20题（5风险×2问法×2，保留随机/定向标记），来自已封存输出；manifest冻结后才加载Judge。
3. GPU smoke：两任务各1条，核对raw/parser/token budget；通过后需明确授权可靠性pilot，不自动Full。
4. 可靠性pilot：Alpaca20×双顺序=40 calls；Safety20=20；另选每任务10条重复一次，共20 calls；合计80 calls（加smoke共82）。重复调用显式audit标签，永不替换原判定。主顺序按seed0平衡，不仅保留模型最有利顺序。
5. 人工盲审40个独立案例；至少10案例双人或全部安全争议双人。共同标注真值与裁决有版本，未审pending。此规模只适合发现大缺陷，不证明高准确度。
6. 通过pilot后才批准Full。正式3模型需要3×(805+100)=2715次基础判定；若主Alpaca也采用双顺序，则增加2415次，共5130；这项开销及聚合方法需未来Judge Gate另行批准。额外复核/2×2诊断另列，重复引用同SHA输出可复用相同版本判定。

P1/P6无需等72B才能保存raw/自动分数，但两项Judge质量结果execution_status=NOT RUN；P9完成所有模型一致评分后才关闭完整比较。

## 审计项与判据提案

| 项目 | 计算 / 实验 | 解释与停止条件 |
| --- | --- | --- |
| Parse / invalid | invalid/全部calls，按任务/长度/来源分层 | 任一invalid暂停正式评分发布，保留raw查因；0/小样本不证明总体0 |
| 位置偏差 | 交换A/B并映射回模型，计算有效配对判定翻转率；ties转换单列 | 翻转率及CI如实报告；不预设未批准数值阈值；缺失配对不丢弃 |
| 长度偏差 | 偏好与长度差分桶；在人审认为质量相当案例中检查倾向，必要时另批等内容长度实验 | 相关性不是偏差因果；原回答不能编辑后混入正式评分 |
| 重复稳定 | 同题同配置重复的一致率，invalid单列 | greedy一致不证明正确或无偏；不同seed greedy也非独立意见 |
| 人工一致 | 对双方有效且人工完成样本算agreement、confusion matrix；二分类可附kappa | agreement及CI/覆盖率如实报告，不预设未批准数值阈值；小样本/人工争议限制必须报；高危漏判逐条处理 |
| Safety FP/FN | positive=unsafe；FPR=FP/(FP+TN)、FNR=FN/(FN+TP)，以人工已裁决且Judge有效的共同样本计算；各人工类别的invalid率与敏感性界限另报 | 分母为0报PENDING/不可估计；invalid独立覆盖率，不当负例；必要补冻结外部安全/不安全回答诊断，不选样本“修漂亮” |
| 同家族风险 | 对匿名Qwen/非Qwen、按人工质量与长度匹配的回答作Judge比较；可另批异家族Judge交叉检查 | 需要真实授权可用的非Qwen输出与人工锚点；没有则PENDING，不因同属Qwen断言有偏，也不因样本少未发现就证明无偏 |

本轮没有批准位置偏差/人工一致率的数字成功门槛；旧提案10%/80%示例已撤出验收要求。技术Gate要求无未解决的解析/血缘问题、无效判定显式审计、危险漏判有人工裁决、人工覆盖按未来获批规模执行；质量结论报告CI和局限。若只有一位人审，agreement不能冒充多人共识。

## LC和硬件

LC需验证自定义Qwen annotator的拟合依赖、reference、annotation编码、长度定义、模型/参数缓存和有限输出。按[AlpacaEval官方项目](https://github.com/tatsu-lab/alpaca_eval)与[LC原始论文](https://arxiv.org/abs/2404.04475)固定实现；不可把标准GPT-4 Judge校准效果自动归给Qwen，也不可称公共leaderboard同标尺。未运行分数NOT RUN，方法NOT VALIDATED；尝试失败后保持null并记unavailable原因，不造替代分数。

BF16 72B仅权重约144GB十进制，另需KV cache、context、临时张量/通信，单80GB不够，2×80GB也不能无实测保证。现有TP2/batch900只是继承配置；先小max_num_seqs smoke，变更调度参数版本化，确认不悄悄改rubric/输出上限；禁止自动量化降级。

pilot记录加载、每任务prefill/decode、峰值、平均/P95长度及判定吞吐；完整预算=模型下载/加载+各任务call数×实测摊销秒+重审+归档。不得用7B吞吐估72B。40条人工预计每条2–5分钟，即80–200分钟，外加争议二审；可分批，但不能删掉关键安全复核来宣称完成。

## v1补充字段与分母冻结

每次Judge调用保留call_id、task/example_id、candidate/reference SHA、order/orientation、repeat_index、judge raw+SHA、parser/hash、parsed_label、invalid_reason、latency/tokens，main与audit调用分开。下列比率不以成功子集替代原调用数：

- 解析有效率=valid_calls/all_returned_calls；invalid率=invalid_calls/all_returned_calls；缺调用是infra partial，不当模型invalid。
- 空Judge输出率=raw.strip()==空串的calls/all_returned_calls；保留raw原文，空值属于invalid。为兼容可另报literal empty。
- 无法判断率=invalid或明确不能判定的calls/all_returned_calls；合法Alpaca tie不当作不能判定；human_uncertain是独立人工状态，不等同Judge invalid。
- 顺序翻转率=映射回同一模型后winner/tie结果不同的有效双顺序pairs/有效双顺序pairs；invalid pairs与缺配对另外报告coverage，不能把它们从总审计清单抹掉。
- 重复一致率=相同输入/配置的有效重复pairs一致数/有效重复pairs；invalid重复单列，greedy一致不证明正确。
- 人工一致率=Judge标签与人工已裁决标签一致数/双方可判断的共同样本；另报全部抽样N、unknown/invalid、人审coverage。Safety positive=unsafe，FPR=FP/(FP+TN)、FNR=FN/(FN+TP)，这里分母限人工已裁决且Judge有效样本；另按人工safe/unsafe分别报invalid率，并给包含invalid的敏感性界限，不能用无效结果掩盖漏判。

Judge Full单/双顺序及聚合尚需审批；v1比较要求Base/SFT/DPO都采用同一种模式，禁止不同模型挑有利顺序。当前仅冻结方案，不实际运行CPU mock、smoke或人审。
