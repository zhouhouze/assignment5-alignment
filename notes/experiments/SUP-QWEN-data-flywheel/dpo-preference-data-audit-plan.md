# Anthropic HH 偏好数据审计计划

状态：P7 NOT RUN。依据2026 handout §6.2；本轮只读取四文件首行结构和压缩文件SHA，未实现/运行全量过滤。不是把SFT prompt/response当成chosen/rejected。

| 官方训练来源 | 本地文件 | SHA256 |
| --- | --- | --- |
| harmless-base | data/hh/harmless-base.jsonl.gz | bf3e1ecd3db61bf21d190f69351d26670c67aababa0fd282fa008c17a7202217 |
| helpful-base | data/hh/helpful-base.jsonl.gz | 518a5bf288456fc9f3b7c980c54116fba0c52f274d3f4d344675d83e4058f6f4 |
| helpful-online | data/hh/helpful-online.jsonl.gz | 0994d18b82083f5c084ce04071b683958a724df8c7215ab1d851986642d36a2a |
| helpful-rejection-sampled | data/hh/helpful-rejection-sampled.jsonl.gz | 0cea2d2ab2187624ec1314e8cc6fb579f0fa987b3a33e8102b7556ed4d255f64 |

## 解析与划分

按真实HH对话边界解析chosen和rejected；**任一分支human消息数>1时排除整对**，记录reason；不把多轮截第一轮伪造原偏好。两边单轮instruction必须一致，提取instruction/chosen response/rejected response，保留原始对话、source file SHA、1-based行号。缺键/格式/边界歧义/不一致前缀hard stop或隔离待审，不静默改写。人类文本里的引用标记不可盲目按字符串count处理，需fixture验证。

四来源分别报告raw/valid/excluded/ambiguous/empty/重复数量和长度分布。建议按instruction及近重复组划分固定seed=0约200条validation，四源分层；完整group隔离优先，实际验证数与比例写manifest，不能拆相同prompt到train/val。保持原偏好与raw；去重/异常剔除超出官方单轮过滤的变更需另批，不为了更好训练准确率丢争议对。

## 偏好质量问题

标签：Correctness、Helpfulness、Completeness、Clarity、Safety、Refusal Appropriateness、Verbosity、Instruction Following。每对记录胜出依据、支持原文片段、chosen/rejected token长度及比值、可能长度驱动、安全风险、是否同意原标签、ambiguity、AI初审、人审status/notes。

先做课程规定的3个helpful+3个harmless随机样例（helpful三来源都覆盖）；再建议每源20对随机+20对跨源长度极端/争议定向，共100对上限，seed0、去重、随机与定向统计分开。人工未review一律pending；标记原chosen不一定“客观正确”。

分析每来源为何chosen胜出：内容正确还是只是更长；合理拒绝还是正常请求误拒；清晰/完整性与冗长是否冲突。按长度差分桶报告偏好标签分布，不能用相关性证明标注员只看长度。AI与人工一致率以双方都完成且可判断的对为分母；争议率、unknown和覆盖率单列；至少10%或全部S3/争议双人review，不能由AI替代人工仲裁。

产物：单轮派生manifest、逐来源计数/exclusion、split IDs/hash、长度诊断、原文review packet、[报告模板](dpo-preference-data-audit.md)。P7完成后单独批准P8 smoke；Full仍需pilot验收。
