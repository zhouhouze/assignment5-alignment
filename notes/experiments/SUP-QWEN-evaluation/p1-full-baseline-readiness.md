# P1 Qwen2.5-7B Full Base Baseline — Readiness

日期：2026-10-10。Protocol=[SUP-QWEN-EVAL-v1](evaluation-protocol-v1.md)。**整体P1 GPU generation readiness：BLOCKED。协议口径已冻结，执行实现/现场条件未全部满足。**

P0仅设计/CPU核验/归档，不启动generation、不下载72B。本页不是已执行run报告。

## 真实阻塞项

| ID | 当前证据 | 解决路径 / 验收 |
| --- | --- | --- |
| B1 Full路径未实现 | qwen_baseline.py CLI stage只有CPU_DRY_RUN/SMOKE/PILOT；run明确拒绝FULL；select非PILOT只保留1条/任务；prepare.selection文案固定20条 | 下一轮获批后先CPU实现显式FULL，选全部16266且保持协议顺序/ID；manifest selection改为all；配置授权阶段受控更新。禁止只删run保护就执行 |
| B2 Full恢复与规模IO未验收 | validate拒绝pending/failed是正确保护，但没有事故核对/continuation工作流；每batch重验全部已保存raw/selected inputs，规模上有累积IO风险；当前测试只覆盖小样本 | CPU故障注入验证正常边界恢复、pending/半写/损坏/duplicate-ID hard stop、同配置续跑不重采样；为16266规模做无模型IO/ledger验收，保留等效完整性，不在GPU上才发现开销 |
| B3 现场及持久化条件未核查 | P0未连接新机器；旧权重通过/GPU空闲记录不证明现在状态 | P1启动前查实际HEAD、weights SHA、tokenizer SHA、driver/software、GPU进程/显存、磁盘/inodes、日志与raw持久化/恢复；当前PENDING |
| B4 下一轮执行范围/预算待批 | 本轮只有P0授权 | 先批准P1 CPU readiness；通过后以实际资源/租费/存储批准GPU Full；产品阈值不阻塞此准备 |

这不是要求重新讨论accuracy或Prompt；下一轮直接采用v1，只解决工程与运行条件。自动评分、人审与Judge状态分开。

## 已通过的CPU/历史证据

- 起点local HEAD=origin/learning/pa5-supplement=439f17b2f152676175b2ad2e38f2c93302a75b7e，工作树clean；最终P0归档commit以Git历史和最终回报为准。
- 本地固定7B config/tokenizer inventory **8/8** bytes/SHA通过，仅加载tokenizer，无模型weights加载。
- 60个benchmark文件hash与历史manifest一致；14042/1319/805/100记录数与任务内ID唯一性通过。
- 全16266条Base prompt CPU渲染+tokenize，通过add_special_tokens=False；最大prompt tokens：1186/330/624/164，+512均<=4096；零超长。ID清单/hash和逐题渲染inventory hash已写协议。
- 当前config等于PILOT manifest configuration；sampling/engine逐项冻结，无按PILOT分数调参。
- Baseline历史239项SHA再核通过；已有SMOKE4、PILOT80、review27 pending。20例MMLU75%/GSM85%不是Full。
- 本轮只运行CPU parser测试：`PYTHONDONTWRITEBYTECODE=1 /Users/hr/Documents/Lesson/assignment5-alignment/.venv/bin/python -m pytest tests/test_metrics.py tests/test_supplement_metrics_edges.py -q -p no:cacheprovider --tb=short` → **20 passed in 0.01s**。未重跑GPU或训练测试，也不称Full runner tests已通过。

## 下一轮启动前清单

| 项目 | P0状态 | P1启动/关闭时必须提供 |
| --- | --- | --- |
| Git HEAD/源码同步 | 本地/origin起点一致；云端未核查 | 云端/本地实际执行commit一致、clean或准确patch/hash；协议归档commit+SHA，不把旧执行commit套新代码 |
| 7B权重验收 | 历史PASS，当前现场PENDING | weights-manifest model/revision正确，逐shard SHA/bytes+tokenizer inventory通过；不下载浮动main |
| GPU状态 | PENDING | nvidia-smi型号/显存/driver、其他进程占用、可用显存；不给已运行实验抢GPU |
| 磁盘/持久化 | PENDING | 权重约15.23GB之外，按CPU序列化估算selected/raw/scored/export/log/备份空间和inodes；建议可用余量至少估算增量两倍，记录mount与持久性，不能只看总容量 |
| Dataset | PASS（本地冻结） | 执行机60文件SHA、全量ID/count/顺序与协议一致 |
| Prompt/tokenizer | PASS（本地冻结） | 6个prompt hash、tokenizer revision/assets、Base render inventory hash与长度复核 |
| Generation config | FROZEN，未开Full权限 | 固定sampling/engine与effective config一致；独立记录Full授权/代码，不改模板/parser |
| Runner readiness | BLOCKED B1/B2 | Full选样与manifest、保护、恢复、CPU tests、规模IO通过 |
| Smoke/Pilot | 历史完成 | 引用原manifest/code/metrics/checksum；不重生成“更好pilot” |
| Full规模 | FROZEN | MMLU14042/GSM1319/Alpaca805/SST100，唯一candidate16266；PILOT分开目录 |
| Raw schema | FROZEN规范，Full未验收 | 协议§14所有输入/输出/血缘字段；模型输出立即落盘+SHA，合法空/错/length仍保存 |
| 自动评分 | 固定parser测试PASS | MMLU/GSM per-item score、分母含parse failure，Alpaca/SST candidate export；Judge状态NOT RUN，不写赢率/安全分 |
| metric recomputation | 规则冻结 | 独立遍历raw，复算分子/分母/长度/finish/count/唯一batch时间，逐项与metrics一致；不只调用同一个summarize自证 |
| checksum | 历史239 PASS，新run NOT RUN | raw/selected/manifest/metrics/log/review全覆盖；校验和不含自身；传输后再验 |
| GitHub archive | P0按本轮commit，P1 NOT RUN | 小产物提交，完整raw持久归档且registry带bytes/SHA/restore；push后核对origin commit，保持Main分支不动 |

## 中断/恢复验收矩阵（未来CPU测试，不是本轮已实现）

| 场景 | 必须行为 |
| --- | --- |
| 启动前或完整批边界退出，无pending | 核对配置/ID/raw SHA，续跑仅从未开始IDs；已保存raw字节不变 |
| generation exception/OOM/返回数量不符 | failed/partial、保留pending/日志、hard stop；不自动retry |
| 半批已写raw或raw有但SHA未完成 | 已完整部分保留，未完成文件隔离/登记；禁止删pending直接跑；人工核对批账本后另批continuation |
| JSONL损坏、SHA不符、额外/重复ID | hard stop、保留证据；重复必须按(task,example_id)检查，不能仅看文件数量 |
| 已生成但未落盘/是否生成不明 | 不能自动当作未生成补跑；显式恢复决定披露丢失证据；无法证明则保持partial，不伪造Full |
| 完整run再次启动 | 不再加载/重采样已完成结果；明确already complete |
| 改prompt/parser/config或数据后resume | 拒绝；新协议/run与旧证据隔离，不拼成同一Full |

独立audit只读raw，metric文件是派生新版本；续跑批ID要包含attempt/run防计时碰撞。任何续跑引起batch composition变化需披露，greedy不承诺跨调度位级一致。完整归档不依赖SSH不断线或实例不会释放。

## 评分与关闭条件

raw任务计数/ID/hash全部等于冻结集合，MMLU/GSM独立复算PASS、无未解infra异常、持久化恢复校验与GitHub索引完成，才可称P1 generation+自动评分完成。Alpaca/Safety Judge=NOT RUN，LC=NOT VALIDATED；未人审仍pending，不能把缺Judge当做P1失败而越权跑72B。

P1可先保存等待人审的review包；人审规模/人员预算独立确认，不把pending包说成已审。Full样本选法沿用协议§10，各错误层包含非明显失败与正确对照。

## 资源估算与建议下一步

旧20例/任务PILOT外推纯生成约1.44h，上一规划2–4 GPU小时只是排程粗估，不含Judge/人工。**尚未通过Full规模IO和现场测量，不能保证租期。** B1/B2先CPU处理，不为文档/CPU准备长租GPU；确认实际GPU/磁盘/预算后再给P1启动窗口。

Recommended next step：获批后执行P1 CPU Full runner/readiness准备；B1/B2测试与B3/B4落实后，才可转READY并启动P1 Full Base。当前没有可直接安全执行的Full CLI命令，本页不提供假命令。

授权可一次覆盖P1的CPU准备和通过验收后的GPU范围/预算；如用户已明确这样批准，不需重复询问同一批准。当前P0没有此授权，BLOCKED首先源于实际Full实现与恢复/现场条件缺项。
