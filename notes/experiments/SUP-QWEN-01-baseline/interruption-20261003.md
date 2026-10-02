# Baseline 下载阶段连接中断

状态：BLOCKED_REMOTE_CONNECTIVITY，GPU generation NOT STARTED。
`directly_comparable_to_official=false`。本条是运行进展记录，不是SMOKE/PILOT完成报告。

## 已确认进展

- CPU dry-run通过；本地与云端相关43项测试通过。云端结果为43 passed in 4.19s，完整日志尚未同步。
- 运行代码、配置、故障测试与限定7B下载脚本已推送至`learning/pa5-supplement`，commit `ee0b5c7c69a55a879c66a61efa2ac32d800754f1`。
- 云端已准备`20261003-smoke-02`及`20261003-pilot-02`的manifest/选题，未开始GPU加载或generation。manifest固定运行源码来自f3662b2；ee0b5c7只增加测试/下载辅助变更，runner/config/parser未变。
- 权重固定`Qwen/Qwen2.5-7B@d149729398750b98c0af14eb82c78cfe92750796`。HF初始传输较慢，模型加载前切换aria2分段下载；全部保留来源仍为该固定HF revision。未下载72B权重。

## 最后可见下载状态

最后读取进度为分片1约31%、分片2约49%、分片3约44%、分片4约48%。其中最慢分片当时ETA约22分钟。该值是连接中断前观察，不代表当前后台状态，也未通过最终文件hash验收。

SSH长期会话随后返回server not responding；电信及移动入口的29920端口均返回Connection refused，电信入口再次复查仍拒绝连接。原因未知，不能推断为GPU故障、租期到期或已完成下载。
云端此前date输出为2026-10-03 00:27:58 CST；失联后的本地date输出为2026-10-03 07:14:29 CST。两端时间存在不一致，保留原始观察，不据此计算准确下载墙钟耗时。

## 恢复顺序

1. 确认用户实例仍在运行及实际SSH地址/端口，再读取下载进程、日志和分片状态；不能假定断线意味着进程已退出。
2. 同一分片不得由两个下载进程同时写。只在确认旧进程退出后恢复缺失传输，完成全部7文件SHA/bytes校验并生成weights-manifest。
3. 拉回云端43项测试完整日志、准备manifest和已脱敏下载日志。保留传输失败记录；不要把signed CDN URL query或凭据提交Git。
4. GPU空闲且权重验证通过后，按原批准范围先4条SMOKE，检查通过再80条PILOT；合法错误/空答/截断不重试，GPU基础设施故障立即停止。
5. 完成原始产物、复算、复核包、报告、checksum和Git同步后停止，等待FULL Gate批准。

当前无SMOKE/PILOT准确率、模型加载耗时或峰值显存可汇报。恢复连接后的时间需要按实际剩余下载量重新估算；此前35–50分钟估计不包含本次连接阻塞时间。
