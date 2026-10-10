# Model Evaluation Scorecard — FULL 模板

状态：NOT RUN。directly_comparable_to_official=false。这张表只接受相同固定benchmark版本、逐题IDs、明确Prompt、统一评分协议的Full结果；**不填入现有20例PILOT分数**。

协议与指标见[metrics spec](../SUP-QWEN-evaluation/evaluation-metrics-spec.md)、[protocol](../SUP-QWEN-evaluation/evaluation-protocol.md)。单元格未来需携带num/den、unit、CI、artifact引用，不能只有百分数。

| Metric | Base | SFT | DPO | SFT−Base | DPO−SFT |
| --- | --- | --- | --- | --- | --- |
| MMLU Accuracy | NOT RUN | NOT RUN | NOT RUN | PENDING | PENDING |
| GSM8K Accuracy | NOT RUN | NOT RUN | NOT RUN | PENDING | PENDING |
| AlpacaEval Win rate | NOT RUN | NOT RUN | NOT RUN | PENDING | PENDING |
| AlpacaEval LC Win rate | NOT RUN | NOT RUN | NOT RUN | PENDING | PENDING |
| Strict safety rate | NOT RUN | NOT RUN | NOT RUN | PENDING | PENDING |
| MMLU Parse failure rate | NOT RUN | NOT RUN | NOT RUN | PENDING | PENDING |
| GSM8K Parse failure rate | NOT RUN | NOT RUN | NOT RUN | PENDING | PENDING |
| Empty response rate（per task） | NOT RUN | NOT RUN | NOT RUN | PENDING | PENDING |
| Max-length rate（per task） | NOT RUN | NOT RUN | NOT RUN | PENDING | PENDING |
| Avg response tokens（per task） | NOT RUN | NOT RUN | NOT RUN | PENDING | PENDING |
| P95 response tokens（per task） | NOT RUN | NOT RUN | NOT RUN | PENDING | PENDING |
| Instruction completion（diagnostic） | NOT RUN | NOT RUN | NOT RUN | PENDING | PENDING |
| Constraint pass rate（diagnostic） | NOT RUN | NOT RUN | NOT RUN | PENDING | PENDING |
| Unsafe compliance（diagnostic） | NOT RUN | NOT RUN | NOT RUN | PENDING | PENDING |
| False refusal（diagnostic） | NOT RUN | NOT RUN | NOT RUN | PENDING | PENDING |
| Generation throughput（per task） | NOT RUN | NOT RUN | NOT RUN | PENDING | PENDING |

## 证据与状态模板

| 项目 | Base | SFT | DPO |
| --- | --- | --- | --- |
| Run IDs / code commit / checkpoint SHA | PENDING | PENDING | PENDING |
| Dataset / selection / reference SHA | PENDING | PENDING | PENDING |
| Prompt hash / sampling / environment | PENDING | PENDING | PENDING |
| Evaluator/Judge/rubric/version | PENDING | PENDING | PENDING |
| Generation completeness / invalid coverage | PENDING | PENDING | PENDING |
| Raw / derived / logs / checksum / archive | PENDING | PENDING | PENDING |
| Human review coverage / status | PENDING | PENDING | PENDING |

比例差值写pp；relative另报百分比且基线0时undefined。Judge部分生成后未评分填PENDING；尝试但不可用的LC保留PENDING并写unavailable原因。主任务指标与补充诊断不能合并当总成绩。
