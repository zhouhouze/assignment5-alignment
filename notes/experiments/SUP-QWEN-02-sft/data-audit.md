# SFT 数据逐条审读与人工复核包

`experiment_type = PA5 Supplement Adapted Reproduction`
`directly_comparable_to_official = false`

## 状态与抽样

Codex已读取20条prompt/response原文并逐条写初步意见；**人工复核未完成**，human_label/human_notes=null。
固定Python random.Random(0)，从210348行全量无放回抽20条、按原行序展示，ID为0-based、line_number为1-based。
原文不修改；packet=`artifacts/pa5-supplement-qwen/preflight/20261002/acceptance-v2/review-packet.jsonl`，派生意见另存 `codex-review-annotations.jsonl`。
分类数量：`{"QA": 5, "summarization": 4, "rewriting": 0, "extraction": 1, "classification": 0, "reasoning": 1, "general assistant": 9, "safety refusal": 0, "other": 0}`。小样本无重写/分类/拒答不代表数据没有这些任务。

| example_id | 类型 | 初步审读（非人工结论） |
| --- | --- | --- |
| 10612 | QA | 问题有明确材料；回答正确区分未给出目标数与各成员达标，但从成员到团队是推断，已明示；未见拒答。 |
| 24859 | QA | 品牌策略条列清楚；没有材料或时间锚点，superior/best等营销断言未核实；泛化模板较强。 |
| 36509 | QA | 材料支持替换果酱；相同用量、可可粉和甜度建议为额外推断，非来源原有验证配方。 |
| 36633 | QA | 步骤结构清晰；将训练概括成全需labeled data却列clustering，概念范围过窄；非已验证技术教材。 |
| 57263 | summarization | 基本遵循材料；传记和精神健康论断未经外部核实，摘要承袭源文不等于事实验证。 |
| 67873 | general assistant | 完成短报告结构，具体数据/引用缺失；通用引言—分点—结论模板明显。 |
| 73882 | general assistant | 要求≥2500词、≥10参考文献与数据分析；实际818空白分词，结尾断在of，无参考文献列表，明显不满足约束；来源统计未核验。 |
| 79511 | general assistant | 步骤有组织，但UI位置与region设置可能随版本失效；未实际操作验证，不能当现行Discord教程。 |
| 93860 | reasoning | C#声明int I却引用i，foreach同样混用；大小写敏感导致未定义变量，给出的示例输出不能证明执行成功。代码未运行。 |
| 100989 | general assistant | 儿童故事用破坏机器和爆炸取得胜利；无操作细节但价值示范与儿童受众不匹配，需安全复核。 |
| 106151 | general assistant | 未提供品牌/真实体验，却声称亲自购买数周并详述产品特性；把虚构经历写成事实，真实性问题。 |
| 110250 | QA | 条列可读；洋流路径/跨半球运输的概括存在可疑过度简化，标记专业事实核查，尚未独立验证。 |
| 124937 | summarization | 简洁保留材料回收项目及轮胎年限；没有混入Clean Up Day资格作为日常中心条件。 |
| 127383 | general assistant | 只给章节提纲，没有实际配方、配比、步骤、图片或营养表；形式像完整交付但内容缺失。 |
| 132300 | general assistant | 描述曲式与氛围，未提供音符、和声或可播放作品；可当创意说明，不能标成已完成作曲音频。 |
| 134027 | general assistant | 给出食材步骤与冷藏建议；保存期限未核实、卫生处理不充分；不把此样本当可直接执行的食品安全建议。 |
| 152930 | extraction | 从材料正确提取三名参议院民主党领袖及职位；没有误混众议院信息。 |
| 198129 | summarization | 准确压缩外野阵容背景和选项探索；不把探索写成已交易。 |
| 198693 | general assistant | 结构完整但缺用户要求的案例、参考链接；多数为通用策略，非实证指南。 |
| 205468 | summarization | 保留案件主线，但省略末尾有人拨打911的限定，强化旁观者全无作为的片面叙述。 |

## 定向拒答补充检查（与20条均匀抽样分开）

均匀样本未抽到refusal，于全量response以regex `^(?:I[’']m sorry|I am sorry|I cannot|I can[’']t|Sorry)` 筛1525候选，seed0抽3条。
这个词面候选数量不是安全样本总量，不能据此估计安全覆盖率。

- ID108443：拒绝给两个月婴儿喂巧克力，给替代解释；记录为健康相关保护性回应，医学细节尚未独立核验。
- ID11716：对抢劫避捕请求明确拒绝，转向合法替代；未给作案步骤。
- ID118766：正常Java仿真请求却以无UI为由声称不能完整编程，属于不恰当能力拒答；随后的代码有scanner/string/system大小写错误且末句截断，未运行验证。前缀拒答不等于安全拒答。

原文见 `refusal-targeted-review.jsonl`。3条人审同样pending，不混入20条随机频率。

## 质量与产品含义

语言流畅、Markdown分段多不等于事实/代码正确。SFT可能同时学习回答组织方式、过度自信、虚构体验、未完成交付和拒答模板。
安全拒答样本与儿童故事暴力结局并存，不能仅凭mirror名中的safety宣称模型更安全。需要未来独立Safety评估与过度拒答检查。
不据20+3条给全数据打“通过”质量结论；本轮没有纠正、过滤或补全raw。

Next task：人阅读保留原文与意见后填写human字段；确认空字段准入方案，区分数据质量问题与模型训练实现问题。
