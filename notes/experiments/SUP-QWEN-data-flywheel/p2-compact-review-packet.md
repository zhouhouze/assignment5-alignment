# P2 精简人审包准备结果

2026-10-29，本地 Mac / CPU。**PACKET PREPARED；human review PENDING；Data Admission NOT APPROVED。** 限于已授权的样本准备，不含 P3、训练或 GPU。

- Train：复用历史 Raw 210348 行中 seed0 无放回选出的20条，保留原 example_id；20/20 Raw 物理行号、Derived-v1 mapping、Prompt/Response 一致。没有改称 Derived 随机抽样。
- Validation：从 Derived-v1 23108 行执行 `sorted(random.Random(0).sample(range(1, 23109), 20))`，20个 1-based ID、无放回及每条入选概率20/23108已复核；20/20经 mapping 追溯 Raw 行号及 SHA，Raw/Derived 原文一致。
- 定向拒答：历史3条单列诊断；3/3 血缘和原文一致，不计入随机比例。P2-B.1 三组代表性风险只引用既有候选与原文对照，不作人审标签。

[审核包](../../../artifacts/pa5-supplement-qwen/sft/20261029-p2-review-packet/README.md)含三份首次阅读原文包、单独的历史 AI 意见、manifest 和 SHA256SUMS。生成组件 `scripts/prepare_qwen_sft_review_packet.py` 在已有目录拒绝覆盖；运行时重新核对 Raw/Derived SHA。独立读取复核结果：样本数、seed 选样、mapping、空白人工字段、产物 SHA 全部 PASS。生成命令：`python3 scripts/prepare_qwen_sft_review_packet.py --output artifacts/pa5-supplement-qwen/sft/20261029-p2-review-packet`。无正式质量标签、重大风险处置或 Data Admission 结论。
