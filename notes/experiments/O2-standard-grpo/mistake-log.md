# O2 Standard GRPO Mistake Log

## 2026-09-14

- 完整本地测试首次尝试因 uv 默认缓存目录不可写而在 pytest 前失败。将 `UV_CACHE_DIR` 指向 `/tmp/o2-uv-cache` 后执行成功；不是算法或测试失败。
- 第一次 training-side 命令在结果目录创建前使用 tee，tee 报目录不存在。Python smoke 仍成功运行并由脚本创建最终 summary；没有伪造缺失的训练日志。随后 rollout 日志在已存在目录中正常保存。
- 原实现全部位于 `tests/adapters.py`。按本轮代码组织要求原样迁到 `cs336_alignment/grpo.py`，adapter 改为薄 wrapper；重构后七项快照测试全部通过。
- rollout 的第二条响应以换行连接 `</think>` 和 `<answer>`，因此严格 grader 给 format=0。保留该真实结果，不调整 grader、不重试。
