# Base / SFT / DPO 横向比较报告模板

状态：NOT RUN；只预建结构。已完成的Base PILOT见[历史报告](../SUP-QWEN-01-baseline/pilot-report.md)，不能推广成Full趋势。

| 章节 | 待填证据 / 当前状态 |
| --- | --- |
| Objective / pre-registered hypotheses | PENDING |
| Configuration / model / dataset / Prompt versions | PENDING |
| Evaluation method / Judge validation / CI | PENDING |
| Full results | [Scorecard](model-evaluation-scorecard.md)：NOT RUN |
| Absolute pp / relative % / CI | PENDING；基线0时relative undefined |
| Base→SFT四格：CC/CW/WC/WW | NOT RUN |
| SFT→DPO四格：CC/CW/WC/WW | NOT RUN |
| 2×2 Prompt effects / interaction | NOT RUN；单独diagnostic表 |
| Alignment tax / guardrail退化 | PENDING |
| Error label migration / subgroup results | PENDING |
| Representative original examples / human status | PENDING |
| Raw paths / run manifests / checksum / restore | PENDING |
| Limitations / seed / confounders / contamination | PENDING |
| Product interpretation / next approval | PENDING |

主比较Base-zero vs SFT-Alpaca是产品配置综合变化；DPO-Alpaca vs SFT-Alpaca保持模板才更接近训练差异。准确率升高但误拒/截断升高须同时披露。多标签统计不能当互斥分组；每一项结论需要逐题证据，未运行不写方向性猜测为结果。
