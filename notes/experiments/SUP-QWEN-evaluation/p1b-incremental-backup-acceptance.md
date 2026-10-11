# P1B-0.5 — Full 增量备份与恢复验收

> 历史Gate记录，保留当时状态。2026-10-11实际Full已16,266/16,266并验收；最新结果、授权/费用和精确启动命令见[p1b-full-baseline-report.md](p1b-full-baseline-report.md)及其session-evidence/launch-*.json，不能把下方旧NOT RUN视为当前状态。

日期：2026-10-11。`experiment_type=PA5 Supplement Adapted Reproduction`；`evaluation_protocol=SUP-QWEN-EVAL-v1`；`directly_comparable_to_official=false`。

本轮只授权备份与恢复工程验收。正式GPU Full仍为**0/16266 / NOT RUN**；没有prepare正式run、模型加载、重新生成Smoke/Pilot、SFT/DPO/Judge。测试复用昨天的CPU Mock文件，新增内容仅为明确标记的CPU备份fixture。人审状态保持pending。

## Objective / system sketch

目标：把云端已经提交的实验文件周期备份到独立Mac，验证故障后可恢复；不把“传输启动”或“文件存在”视为备份完成。

```text
既有Runner：.pending → fsync → 原子发布 sealed raw（原实现不变）
                         ↓
新增 backup export：Raw优先 → 对应attempt元数据 → 稳定文件快照
                         ↓ SSH / gzip delta
Mac：objects/SHA256 → 全引用校验+fsync → snapshots/ → LATEST.json
                         ↓ 校验成功后回传独立ack
新增 guard：ack过期 → SIGTERM自有实验进程组 → 必要时SIGKILL
```

只增加备份、保护、验收脚本与测试/文档；原Runner、协议、Prompt、parser、采样配置不变。回滚使用本Gate提交的`git revert`；先停止未来备份/guard进程，不删除任何唯一产物。

## Configuration / format

- 生产建议间隔60秒，SSH传输单次timeout180秒；备份失败即记录FAILED并非零退出，不无限重试。
- guard建议max-age180秒、poll5秒、SIGTERM宽限30秒；只管理它自己通过`start_new_session=True`启动的进程组。
- 使用现有密码认证SSH master，传输子命令BatchMode；不把密码/私钥写入脚本、Git或配置。连接断开后需重新认证再恢复，不承诺无人值守密码重连。
- Mac复用`/Users/hr/Documents/Lesson/pa5-experiment-backups/`。验收位于`preflight/20261011-p1b05/live-*/`；正式数据未来使用`full/<run_id>/`，本轮未创建正式目录。
- 存储布局：`objects/<sha前2位>/<其余位>`、`snapshots/<id>.json`、`LATEST.json`、`backup-events.jsonl`、失败传输`incoming-*`及stderr。对象/快照不覆写，云端删除不会删除旧本地快照；本轮没有安装清理策略。
- 数学检查：`SHA256(source_bytes) == manifest.sha256 == SHA256(local_object) == SHA256(restored_bytes)`。属于字节完整性，不替代Runner的schema、身份、配置和最终指标校验。无模型Tensor、梯度或训练参数。

## Writing safety / snapshot semantics

1. 实验协议以单条封存JSONL原子发布Raw，备份校验单行 framing 与canonical `record_sha256`。已发布Raw损坏、改写、丢失均停止；不清洗、覆盖或重新采样。
2. 读取前后检查inode/size/mtime/ctime，拒绝symlink。活动日志/progress变化则defer；不可变文件变化则hard stop。白名单防止把环境、权重或凭据目录递归传走。
3. 先收集Raw，再扫描已先于Raw发布的attempt/intent元数据，允许progress领先于快照Raw。活跃快照是可恢复的前缀，不是全run在同一时刻的事务快照；最终完整性仍由Runner验证。
4. 写入中`.pending-*`不计入有效Raw。`--quiescent`必须成功取得Runner排他锁，才纳入finalized、未提交pending及失败finalizing事故证据；事故字节保留原状，不评分、不计完成数。锁被占用即失败，不阻塞或杀死写入者。
5. gzip完整读取至EOF检查CRC，再校验每个对象bytes/SHA；本地对象全部持久化后发布snapshot及LATEST；新目录先fsync其父目录，事件日志与失败传输也执行fsync。失败传输不作为成功快照；进程硬杀可能留下START/未引用对象，guard通过ack过期检测。
6. 只有本地校验/落盘成功才回传ack；ack必须在run目录之外，绑定源目录与manifest SHA，避免污染finalize的source inventory。ack回传失败也标FAILED；本地有效快照保留，旧远端ack逐渐过期。
7. Resume单位为文件/对象：已有已校验Raw复用，仅传新/变化对象。中断的gzip delta重新传，不承诺大文件内部字节偏移续传。文件级恢复足以覆盖当前单条Raw文件结构。
8. 活动备份不包含finalized；正式生成/评分全部结束后必须`--quiescent`再备份，确认deferred为空，恢复到新目录并执行原Runner validate，才可声称完整归档。

## Tests / observed results

具体命令、源码hash、逐轮日志和恢复路径见[验收证据目录](../../../artifacts/pa5-supplement-qwen/baseline/gate-audit/20261011-p1b05/)。

- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p test_qwen_backup.py -v`：Mac与Linux各**24 tests PASS**。使用stdlib，不加载模型。覆盖半写文件、seal损坏、读时append、mutable defer、source删除/改写、传输截断、磁盘写失败、本地对象损坏、新目录/事件日志fsync顺序、锁冲突、路径/symlink、旧目标拒绝覆盖、guard启动前拒绝及运行中过期停止。
- 实际SSH周期测试：CPU writer追加fixture，数次周期抓取Raw增长；网络故障注入保留LATEST并记录FAILED；恢复周期只新增第7条Raw；随后quiescent另传未提交pending事故字节，完成数仍为7。重复无变化周期copied_objects=0。
- 生产间隔验证：实际60秒配置连续完成两轮，准确启动间隔见one-minute-cadence.json，第二轮copied_objects=0；认证master和SHA校验均成功，worker按cycles=2自动退出。
- 云端真实guard测试：先周期续期，再停止ack刷新，max-age4秒演示保护停止**自有CPU child**，不触碰GPU或其他进程。生产180秒配置尚未进行GPU退出测试。
- 复用2026-10-10既有CPU Mock：**16266 Raw / 24421文件**，云端→Mac逐对象校验→本地恢复→打包回传独立云端目录→原`qwen_baseline.validate`通过，包含finalized/source inventory校验；无vLLM导入、无模型生成。准确耗时、压缩包bytes/SHA以`live-acceptance.json/log`为准。
- 按项目要求补跑`tests/test_grpo.py`：**19项原有NotImplementedError失败**，与P1A分类一致；不把它们列为备份通过项，不补全或改动GRPO函数。CPU执行，GPU不可见。

### Incident / correction

初始SSH复用master失效，部署命令退出255；重新密码认证并启用keepalive后恢复，未记录凭据。初次验收成功后，补充了quiescent事故文件保留。第二次验收发现旧测试错误地把新增传输对象数等同于新增Raw数（pending也应传输），保留FAILED报告/log，并将恢复周期与最终事故备份分开验收。最终版本重新执行真实SSH和全量旧Mock恢复，最终PASS才是本Gate结论。

## Provider retention evidence

智星云[实例状态文档](https://s.apifox.cn/b0fc397f-c455-4c9a-9d82-875fc48ae106/doc-6898147)区分已结束/释放的Status0和选中保留磁盘后的Status8；Status8可从保留磁盘创建新实例。[释放保留磁盘接口](https://s.apifox.cn/b0fc397f-c455-4c9a-9d82-875fc48ae106/api-242528020)会将状态改为0并记录DiskReleaseTime。官方[常见问题](https://gpu.ai-galaxy.cn/docs_v2/常见问题.html)说明本地盘无冗余并建议开启使用结束后保留全部磁盘。

**公开机制不等于本实例的设置。** 用户2026-10-10说明关机后保留实例；本轮重连观察到原目录、commit和产物仍在，但没有受控关机/释放实验，没有读取账户级IsKeepDisk、保留期限、磁盘费用或操作记录。当前只有系统盘，无独立云盘。关机保留、到期保留磁盘、主动释放磁盘不可混为一谈；**释放后的恢复保证UNKNOWN，不假定可恢复**。不调用关机/释放API作破坏性验证。已校验Mac快照可独立于云实例恢复，但只有已同步部分受保护。

## Limitations / product interpretation

周期备份不是零数据丢失：正常恢复点落后约60秒加本轮传输/校验时间；网络中断或Mac睡眠时可更长。guard到过期后至多再等待poll及终止宽限；它不是实例租费封顶，也不会关机/退租。Mac需要保持开机、网络与足够空间；caffeinate防空闲睡眠，不保证合盖/断电仍在线。进程组保护经过CPU验证；vLLM自行建立其他进程组的退出路径仍需正式执行现场观察，必要时按归属确认处理，不自动杀其他任务。

SHA与seal只验证字节和原封存契约，模型答案错、空答、格式坏、length均仍是合法待评估输出。恢复快照不代表FULL COMPLETED；真实实验是否完整须按16266 expected IDs和冻结协议另验。正式阶段还需人审和Judge范围控制。

## Result / next task

**P1B_0_5_BACKUP_ACCEPTANCE=PASS；P1B_EXECUTION_READY=NO。** 当前没有持续运行的验收watcher或测试writer；备份机制已实现、验证并归档，未来获批后才绑定正式run启动。

下一任务：按[资源与费用检查清单](p1b-resource-cost-checklist.md)确认开机窗口、当前费率/预算/累计时间和磁盘保留设置，再由用户单独批准P1B-1。实际命令在[p1b-execution-commands.md](p1b-execution-commands.md)新增0.5章节。当前费用上限/最长时间/P1B-1批准均未给出。Learner explanation status=pending：为什么Raw复制成功还不能立刻算备份成功，为什么pending要保留却不能计入完成样本？
