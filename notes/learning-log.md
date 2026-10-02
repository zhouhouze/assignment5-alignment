# Supplement学习日志

## 2026-10-02 — Gate A审计与baseline计划

- Component：独立实验线准备，未实现训练或parser。
- Concept：Base→SFT→DPO区分demonstration与preference；评估模板和judge解析也会影响结果。
- Files：SUP-00审计/路线、SUP-01计划、audit数据/hash/环境/测试记录。
- Tests：离线运行test_data/test_dpo/test_metrics，7 failed，全部NotImplementedError；无依赖收集失败。
- Bugs/limitations：服务器Python3.14且缺git/uv/ML依赖；HF未认证401；课程SFT预处理文件缺失；Safety helper有invalid默认safe风险。
- Decision：从官方c2734a2分支，不混入Main实现；停在审计Gate，后续先修环境和parser。
- Remaining：HF权限、课程SFT数据来源、训练硬件、judge和停止规则验证。
- Learner explanation status：Pending；本轮不宣称已理解或完成任何训练组件。

## 2026-10-02 — Supplement parsers

- Component：MMLU/GSM8K字符串提取，新增supplement_metrics与薄adapter。
- Concept：提取规则与答案正确性分离，不能读取gold帮助解析。
- Files：supplement_metrics.py、tests/adapters.py、新增边界测试、parser-report及测试产物。
- Tests：两个官方parser各2 passed；Supplement+边界20 passed/3个未实现失败；官方Main脚手架19个NotImplementedError，未带入个人Main实现。
- Bugs encountered：无parser测试失败；已知协议局限见parser-report。
- Final decision：MMLU明确声明冲突返回None；GSM8K最后十进制数字，处理符号与千分位，不求值表达式。
- Remaining：真实pilot解析覆盖率；环境/HF认证；学习检查。
- Learner explanation status：Pending。Next task：baseline runner在后续批准Gate实现。
