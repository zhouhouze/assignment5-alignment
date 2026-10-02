# CS336 PA5统一实验索引

本索引是Main与Supplement的证据入口。长期规则见[archive-policy.md](archive-policy.md)。Main内容通过固定提交链接引用，未移动历史文件或混入Supplement实现。

| Experiment | Status | Report | Artifacts | Commit |
| --- | --- | --- | --- | --- |
| O1 Prompt Baselines（历史） | FULL报告完成；旧raw缺失 | [历史结果](https://github.com/zhouhouze/assignment5-alignment/blob/2267287678062eefe5a2bd5f0e5f6a3a03f37565/notes/experiments/O1-prompting-baselines/full-results.md) | 旧AutoDL完整raw不可恢复；不能逐题复现 | `2267287` |
| O1归档复现 | FULL自动归档完成；24条人工复核待填 | [复现报告](https://github.com/zhouhouze/assignment5-alignment/blob/96b14809b08927516cfd049cfc6ddb33cd3f115c/notes/experiments/O1-prompting-baselines/reproduction-report.md) | [raw/metrics/review/checksum](https://github.com/zhouhouze/assignment5-alignment/tree/96b14809b08927516cfd049cfc6ddb33cd3f115c/artifacts/O1-prompting-baselines-reproduction) | `96b1480` |
| O2 Standard GRPO | 单卡独立SMOKE完成；双卡闭环/PILOT/FULL未完成 | [单卡报告](https://github.com/zhouhouze/assignment5-alignment/blob/9321c61d2814fa3db464690ccfe68b199057d39d/notes/experiments/O2-standard-grpo/single-gpu-smoke.md) | [smoke证据](https://github.com/zhouhouze/assignment5-alignment/tree/9321c61d2814fa3db464690ccfe68b199057d39d/artifacts/O2-standard-grpo/single-gpu) | `9321c61` |
| SUP-00 Environment | 环境/kernel验收PASS；HF访问BLOCKED | [初审](SUP-00-environment/environment.md)、[本轮前置报告](SUP-00-environment/preflight-report.md) | [初审](../../artifacts/pa5-supplement/audit/20261002/)、[本轮](../../artifacts/pa5-supplement/audit/20261002-preflight/) | 初审`36de0b7`；本轮归档提交见文件Git历史 |
| SUP-01 Baseline | parser完成；模型生成/评分未开始 | [计划](SUP-01-baseline/baseline-plan.md)、[parser报告](SUP-01-baseline/parser-report.md) | 本轮测试日志，非模型raw | parser `4b6014e` |
| SUP-02 SFT | 仅调查数据来源；未审样本/训练 | [数据源调查](SUP-02-sft/dataset-source-investigation.md) | [来源元数据](../../artifacts/pa5-supplement/audit/20261002-preflight/sft-sources.json) | 本轮归档提交见文件Git历史 |
| SUP-03 DPO | NOT STARTED | [Gate H–L计划](SUP-00-environment/execution-plan.md) | 无run，无模型结果 | — |
| SUP-final | 持续分析框架；无最终比较结果 | [数据飞轮](SUP-final/data-flywheel.md) | 待后续证据 | — |

准确的提交哈希与分支可由GitHub每个文件的History查询；不在commit内写自身SHA。代码执行来源和产物hash见各manifest。全部大小/位置/SHA登记见[artifact-registry.json](artifact-registry.json)。旧记录不因新索引而被补标为完全合规。

当前授权只覆盖环境修复、HF检查、parser、测试分类、SFT来源调查与归档/push；不开放baseline full、SFT、DPO或70B judge。
