# Model Evaluation Scorecard — Base FULL / SFT-DPO未执行

状态：Base真实Full16,266/16,266已验收；SFT/DPO/Judge NOT RUN，人审PENDING，Git同步见Full报告。directly_comparable_to_official=false。这张表只接受相同固定benchmark版本、逐题IDs、明确Prompt、统一评分协议的Full结果；**不填入现有20例PILOT分数**。

协议与指标见[metrics spec](../SUP-QWEN-evaluation/evaluation-metrics-spec.md)、[protocol](../SUP-QWEN-evaluation/evaluation-protocol.md)。单元格未来需携带num/den、unit、CI、artifact引用，不能只有百分数。

| Metric | Base | SFT | DPO | SFT−Base | DPO−SFT |
| --- | --- | --- | --- | --- | --- |
| MMLU Accuracy | 9813/14042 = 69.8832% | NOT RUN | NOT RUN | PENDING | PENDING |
| GSM8K Accuracy | 929/1319 = 70.4321% | NOT RUN | NOT RUN | PENDING | PENDING |
| AlpacaEval Win rate | NOT RUN | NOT RUN | NOT RUN | PENDING | PENDING |
| AlpacaEval LC Win rate | NOT RUN / NOT VALIDATED | NOT RUN / NOT VALIDATED | NOT RUN / NOT VALIDATED | PENDING | PENDING |
| Strict safety rate | NOT RUN | NOT RUN | NOT RUN | PENDING | PENDING |
| Invalid Judge output rate | NOT RUN | NOT RUN | NOT RUN | PENDING | PENDING |
| MMLU Parse failure rate | 0/14042 = 0% | NOT RUN | NOT RUN | PENDING | PENDING |
| GSM8K Parse failure rate | 0/1319 = 0% | NOT RUN | NOT RUN | PENDING | PENDING |
| Empty response rate（per task） | MMLU0/14042; GSM0/1319; Alpaca0/805; Safety0/100 | NOT RUN | NOT RUN | PENDING | PENDING |
| Max-length rate（per task） | MMLU0/14042; GSM3/1319; Alpaca97/805; Safety0/100 | NOT RUN | NOT RUN | PENDING | PENDING |
| Avg response tokens（per task） | MMLU18.85; GSM196.98; Alpaca275.61; Safety104.20 | NOT RUN | NOT RUN | PENDING | PENDING |
| P95 response tokens（per task） | MMLU33; GSM369; Alpaca512; Safety257 | NOT RUN | NOT RUN | PENDING | PENDING |
| Instruction completion（diagnostic） | NOT RUN | NOT RUN | NOT RUN | PENDING | PENDING |
| Constraint pass rate（diagnostic） | NOT RUN | NOT RUN | NOT RUN | PENDING | PENDING |
| Unsafe compliance（diagnostic） | NOT RUN | NOT RUN | NOT RUN | PENDING | PENDING |
| False refusal（guardrail，独立benign集） | NOT RUN | NOT RUN | NOT RUN | PENDING | PENDING |
| Generation throughput（per task） | examples/s: MMLU9.3209; GSM0.9400; Alpaca0.6573; Safety1.5293 | NOT RUN | NOT RUN | PENDING | PENDING |

## 证据与状态模板

| 项目 | Base | SFT | DPO |
| --- | --- | --- | --- |
| Run IDs / code commit / checkpoint SHA | 4×qwen-full-20261011T034800Z-task; code47ae79f; Base revision d149729 | PENDING | PENDING |
| Dataset / selection / reference SHA | 四manifest与inventory；16,266固定ID；60数据SHA PASS | PENDING | PENDING |
| Prompt hash / sampling / environment | SUP-QWEN-EVAL-v1；完整manifest；seed0 greedy BF16/5090 | PENDING | PENDING |
| Evaluator/Judge/rubric/version | 冻结MMLU/final-number parser；Judge NOT RUN；taxonomy v1 | PENDING | PENDING |
| Generation completeness / invalid coverage | 16,266/16,266；missing/duplicate/corrupt=0 | PENDING | PENDING |
| Raw / derived / logs / checksum / archive | Verified Mac CAS/restore/tar + Git小型证据；同步见Full报告 | PENDING | PENDING |
| Human review coverage / status | 12/44 COMPLETED；32待审；075 Safety UNCERTAIN；060严重度细化PENDING | PENDING | PENDING |

比例差值写pp；relative另报百分比且基线0时undefined。Judge尚未运行统一NOT RUN；LC方法兼容性NOT VALIDATED；实际尝试后有未决项才用PENDING并写原因。主任务指标与补充诊断不能合并当总成绩。

Base证据：[Full报告](../SUP-QWEN-evaluation/p1b-full-baseline-report.md)、[逐任务metrics/manifests](../../../artifacts/pa5-supplement-qwen/baseline/full/20261011-p1b1/README.md)。主指标为micro；CI未计算/null。Scope=四个task-subset REAL/FULL run的并集；run_code_commit47ae79f，协议SUP-QWEN-EVAL-v1，model/tokenizer d149729；human12/44 COMPLETED，32待审；075专项真值待定。Instruction/constraint/unsafe诊断没有正式量化，不能用AI抽样标签填正式rate。吞吐范围为unique batch生成，排除load/write。SFT−Base/DPO−SFT均无结果，不能填差值。

2026-10-16人审更新仅作用于复核覆盖率/状态：[Round01 sidecar报告](../SUP-QWEN-evaluation/human-evaluation-round01-report.md)。没有修改正式Base自动分数、Judge状态或其他模型成绩；原44条包中PENDING按历史快照保留。
