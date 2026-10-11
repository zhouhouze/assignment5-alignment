# P1B-1 启动前资源与费用检查清单

2026-10-11；SUP-QWEN-EVAL-v1；Adapted Reproduction；directly_comparable_to_official=false。本文件是检查单，不是执行批准。Full 0/16266。准确现场事实见本Gate resources.json。

| 检查项 | 本轮状态 / 启动前动作 |
| --- | --- |
| 授权 | 本轮仅P1B-0.5；单独P1B-1批准PENDING |
| Git | 本地/云端learning/pa5-supplement同步本Gate归档commit，源码clean；冻结实际run_code_commit；不混入Main |
| GPU | 查询时RTX5090 32GB、无compute进程；启动前重查；有其他任务则停止 |
| 模型 | 已有固定Qwen/Qwen2.5-7B四分片，勿重下；启动时Runner重新校验全部bytes/SHA |
| 协议 | 固定SUP-QWEN-EVAL-v1、数据/Prompt/parser/config；漂移即停 |
| 云端空间 | 至少5GiB和100000 inodes余量，现场约130GiB/1273万；最终输出用唯一run目录 |
| Mac空间 | 至少5GiB余量并计入对象、周期快照manifest、日志和恢复演练副本；不得存仓库tmp下 |
| 保留机制 | 关机后实例保留为用户说明；账户是否选中保留磁盘、保留期限/费用UNKNOWN；释放后恢复UNKNOWN |
| 外部备份 | 60秒周期；初始快照SHA校验及ack完成后才允许guard启动；Mac保持在线，caffeinate不能防合盖断网 |
| 故障处理 | 本地FAILED非零退出，保留incoming/stderr/旧快照；guard ack180秒过期停止自有进程组；检查事故并显式resume，不重采样合法坏输出 |
| 最终备份 | 生成/评分完成后quiescent锁、deferred=0、SHA与原Runner restore validate；失败不释放唯一云端数据 |
| 吞吐依据 | 历史各20题Pilot：MMLU5.4087、GSM1.0726、Alpaca0.6341、Safety1.1644 examples/s；不保证Full同速 |
| 纯生成外推 | 约86.36分钟；MMLU43.3、GSM20.5、Alpaca21.2、Safety1.4分钟 |
| 总窗口建议 | 2–3小时另留备份/准备余量；确认本次到期/关机计划，不沿用昨天00:13计划 |
| 当前时价 | 最近用户提供3.16元/小时（2026-10-10）；当前控制台价未独立核实 |
| 预计GPU费用 | 按该费率2–3小时约6.32–9.48元；准备、空闲、磁盘、带宽等另计 |
| 已产生费用 | UNKNOWN，不根据GPU利用率0%推断免费 |
| 用户最长运行时间 | PENDING；明确累计所有attempt，分任务run也不得重复使用总额度 |
| 用户费用上限 | PENDING；金额应包含认可的准备/空闲余量，计费规则另核对 |
| 超限 | max-seconds为下一批准入上限，加载/当前批次可越界；不是自动退租或精确计费截断。接近批准上限安全停止并保留PARTIAL |
| 范围 | P1B-1仅四任务生成/评分/归档；Alpaca Judge/Safety Judge NOT RUN；SFT/DPO不推进 |

Next task：上述必要条件确定并收到正式批准后，按P1B实际命令启动一个run；本Gate不执行任何真实Full命令。
