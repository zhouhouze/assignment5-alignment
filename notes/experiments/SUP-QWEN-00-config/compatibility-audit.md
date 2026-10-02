# Qwen adapted compatibility audit

`experiment_type = PA5 Supplement Adapted Reproduction`
`directly_comparable_to_official = false`

日期：2026-10-02。官方配置路线保留；本轮只完成 CPU preflight。主数据流：

Qwen2.5-7B Base → 四基准 baseline → 官方 Alpaca 模板 SFT → 四基准 eval → HH DPO（同一 SFT policy/reference）→ 四基准 eval。
Qwen2.5-72B-Instruct 只负责 AlpacaEval 与 Safety Judge。

## 固定配置与官方来源

[配置](../../../configs/pa5_supplement_qwen.json)为独立入口。官方依据：本仓库 Stanford CS336 Spring 2026 Supplement PDF、`tests/test_data.py` / `test_dpo.py` / `test_metrics.py`、`cs336_alignment/prompts_safety/`，不是2024/2025作业实现。数据镜像 README 的下载链接指向 **cs336-spring-2024**，不能当作2026等价证据。

Policy revision/tokenizer：`d149729398750b98c0af14eb82c78cfe92750796`。Judge revision/tokenizer：`495f39366efef23836d0cfae4fbe635880d2be31`。
两者 AutoConfig 均解析为 `qwen2 / Qwen2ForCausalLM`；AutoTokenizer CPU加载成功，不等于 vLLM 模型加载或训练验收。

## 搜索与逐项处置

执行 `rg -n 'Llama|llama|eos_token|bos_token|pad_token|chat_template|stop_token|end_of_text'`，搜代码、测试、文档；排除uv.lock、大型fixture tokenizer词表、历史artifact正文；fixture配置另行审查。完整命中见 preflight/compatibility-search.txt.gz。

| 位置/假设 | 处理 |
| --- | --- |
| `modal_utils_safety.py` 的两个 Llama 绝对路径 | 官方入口保留；Qwen独立JSON配置，不调用该默认路径 |
| `audit_supplement_environment.py` 固定 gated Llama 检查 | 保留官方审计；Qwen用独立 preflight与固定下载inventory |
| AlpacaEval原模板 Llama BOS/header/EOT | 原文件保留；抽取相同system/user语义，以固定Qwen judge tokenizer `apply_chat_template`重渲染 |
| 原AlpacaEval annotator固定70B路径 | 独立`alpaca_eval_vllm_qwen2_5_72b_fn`，model/tokenizer revision、BF16、TP2、seed0固定 |
| Safety helper已用apply_chat_template | 语义可复用，未来Qwen入口必须显式锁revision；本轮仅保存语义/渲染，不启动LLM |
| Safety非true默认为safe | 原逻辑不动；新路线保留官方兼容分数与strict True/False/invalid分开，invalid不冒充safe；有invalid时Review Gate不通过 |
| Base tokenizer自带chat模板 | 存在不代表应该使用。baseline和SFT保持官方纯文本；Judge才用nativechat |
| Qwen generation_config默认可能影响参数 | future vLLM `generation_config='vllm'`并显式temperature0/top_p1/n1，避免继承模型采样偏好 |
| EOS/PAD/BOS | Policy EOS/PAD=151643；Judge EOS=151645、PAD=151643；tokenizer BOS=None；config BOS=151643不强行插入 |
| SFT PAD==EOS | 不可用 `labels == pad_id` 全局mask，否则真实文档EOS监督会丢失。未来按实际padding位置mask；packing无padding |
| 官方 Llama test fixtures | 保留；新增Qwen离线sanity，不替换官方snapshot |
| MMLU/GSM8K parser | 原规则与源码保持不变；失败是实验结果 |
| Main/O1/O2与R1停止规则 | 不继承到Supplement；不得引入 `</answer>` / boxed grader |
| model family if分支 | 当前runner/训练循环尚未实现，未发现需要改写的现成Llama family分支 |

## 张量与数学边界（未实现核心数据集）

每个文档：官方Alpaca字符串编码、`add_special_tokens=False`，追加一个policy EOS ID。
拼接 token 流长度 T；下阶段Dataset预期input_ids/labels均为int64 `[512]`，batch `[B,512]`，labels向右错一位。
算术审计 `N=floor((T-1)/512)`；余数 `(T-1)%512`，一枚lookahead用于最后一个target。不是response-only loss，没有截断每篇文档到512。
手算：流0…10、L=4，inputs=0…3和4…7，labels=1…4和5…8；剩余2枚未消费后缀。未来核心实现须另读官方fixtures并通过测试。

## 风险与下一任务

本轮只改配置/审计工具，不改核心训练或parser。BF16 full SFT不承诺32GB可运行；优先80GB级，72B judge优先2×80GB且需实测KV余量；不得静默quant/offload。
下一任务：连接/归档确认后，经批准实施baseline runner CPU dry-run→每benchmark1条→20条pilot。正式SFT前先处理空字段准入与人工审阅。
