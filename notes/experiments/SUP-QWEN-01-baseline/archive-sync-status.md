# GPU Gate 归档与云端同步状态

## 2026-10-10：同步恢复并验收

新SSH入口连接成功。云端从干净的f5f4050安全fast-forward到03e5e59；239项Baseline文件SHA256全部通过，4条smoke和80条pilot与仓库外原始输出逐字节一致。本地与GitHub原有档案完整，认证阻塞已解除。验证证据见`artifacts/pa5-supplement-qwen/archive-sync/20261010/verification.json`。随后将本次状态更新提交推送，并将云端fast-forward到同一状态归档提交；最终提交号从本文件Git History定位，三端HEAD在完成回复中确认。

本轮只补齐归档同步，没有加载模型或产生新generation。GPU检查为RTX5090 32607MiB、15MiB占用、0%利用率。当前Baseline GPU Gate已完成；27条human review仍pending，FULL/SFT/DPO/Judge仍未获本轮执行授权。

## 2026-10-03 历史阻塞记录（已解除）

2026-10-03。模型执行和产物验收已完成；最终云端Git同步仍待完成。

- 实际GPU执行commit：`f5f4050de424a2b371da83e792fa5a4a81279084`，启动时云端工作区clean。
- 完整实验产物归档commit：`aa4698f8b62d5a5512696bc48ea18a76e1aba55c`，已推送到GitHub并通过ls-remote核对。本地raw、复算、报告、复核包与checksum均完整；239个文件变更，Baseline目录总计约1.96MB，不含权重。
- 云端原始证据位于`/root/pa5-supplement-setup/20261003-gpu-gate/runs/`，已通过310712-byte传输包SHA核验完整取回。最后可见状态为smoke4/4、pilot80/80、GPU15MiB/0%，全部模型进程退出。
- 最后向云端发送pull前，长期SSH会话超时。重新连接32132端口时，root返回Permission denied；vipuser连接关闭。没有继续猜测密码或修改登录配置。当前云端HEAD无法再次核验；最后成功核验是f5f4050，不能宣称已与归档HEAD一致。
- 已请求用户提供当前SSH信息。恢复后只需检查工作区、执行非破坏性fast-forward到本地/GitHub最新归档提交、复核Baseline SHA256SUMS及三端HEAD；不需要重新生成任何输出。

当前判定：实验pipeline、80条raw和offline复算PASS；GitHub归档完成；**all aligned=NO（云端待核验/同步）**。完整Gate交接尚有这一项阻塞，当前不启动FULL/SFT/DPO/Judge。恢复连接并完成同步后，才将本轮结束状态更新为三端全部对齐。
