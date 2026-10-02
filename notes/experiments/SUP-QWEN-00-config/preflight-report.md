# Qwen Adapted Reproduction — Preflight 报告

`experiment_type = PA5 Supplement Adapted Reproduction`
`directly_comparable_to_official = false`

日期：2026-10-02。当前完成配置、CPU兼容性、数据验收与审读归档。**无Qwen模型生成、无训练、无72B权重下载。**

## Adapted Configuration

| 角色 | 官方 | 本路线 |
| --- | --- | --- |
| Base / SFT / DPO policy | meta-llama/Meta-Llama-3.1-8B | Qwen/Qwen2.5-7B（Base） |
| Judge | meta-llama/Llama-3.3-70B-Instruct | Qwen/Qwen2.5-72B-Instruct |
| SFT | Spring2026 Modal processed copy | garg-aayush/sft-cs336-assign5-datasets，指定三文件 |

Policy model/tokenizer revision：`d149729398750b98c0af14eb82c78cfe92750796`。
Judge model/tokenizer revision：`495f39366efef23836d0cfae4fbe635880d2be31`。
Dataset revision：`ac710ef808346bf458d7b093bfe4586cb15699d9`。

来源：[Qwen7B模型卡](https://huggingface.co/Qwen/Qwen2.5-7B/tree/d149729398750b98c0af14eb82c78cfe92750796)、[72B模型卡](https://huggingface.co/Qwen/Qwen2.5-72B-Instruct/tree/495f39366efef23836d0cfae4fbe635880d2be31)、[mirror说明](https://huggingface.co/datasets/garg-aayush/sft-cs336-assign5-datasets/blob/ac710ef808346bf458d7b093bfe4586cb15699d9/sft-instruct/README.md)。

配置入口：[pa5_supplement_qwen.json](../../../configs/pa5_supplement_qwen.json)。官方路径/模板/结果未被替换。运行配置当前status=preflight_only、generation_authorized=false。

## Model / Tokenizer Access

两模型config/tokenizer文件已实际下载、AutoConfig/AutoTokenizer CPU加载成功，READY仅表示访问和解析。未instantiate QwenForCausalLM、未验证真实vLLM推理。

| 项目 | 7B Base | 72B Judge |
| --- | --- | --- |
| EOS | `<\|endoftext\|>` / 151643 | `<\|im_end\|>` / 151645 |
| PAD | `<\|endoftext\|>` / 151643 | `<\|endoftext\|>` / 151643 |
| tokenizer BOS | None | None |
| config BOS | 151643 | 151643 |
| special_tokens_map | eos_token, pad_token | eos_token, pad_token |
| chat template | 存在；Baseline/SFT不使用 | 用native apply_chat_template |

未新增PAD或伪造Llama token；7B packing追加原生EOS一次。EOS/PAD同ID时不能把文档EOS当padding遮罩。Judge stop IDs [151645,151643]显式记录；禁用Qwen默认随机采样/repetition参数，使用greedy。

## Dataset / Evaluation Method / Results

这是准备记录，无模型accuracy/reward。三文件593,785,365 bytes，总234458行（sample1000与train重复，非独立新数据）：train210348、test23110、sample1000。
所有JSON合法、必需字段字符串类型正确；train21空response+1空prompt，test2空response；精确pair重复0，train重复prompt4。完整源文件未修改。

详细SHA/行号/分布：[data-acceptance.md](../SUP-QWEN-02-sft/data-acceptance.md)。完整train/test数据准入BLOCKED；sample结构PASS。

原样抽seed0 train20条审读，另抽拒答前缀候选3条诊断；human_label/notes全部null，**人工复核pending**。逐条意见与限制见[data-audit.md](../SUP-QWEN-02-sft/data-audit.md)。发现变量大小写编译错误、截断、未完成要求、虚构产品体验与安全内容不一致，不把流畅文风当正确性。

Sample1000：519206 tokens，1014个可用512长度input/target对块，37余数，99.9929%算术利用率；这是CPU token统计，Dataset核心仍未实现。full train tokens尚未测量。

Third-party mirror of the Stanford CS336 safety-augmented UltraChat 200k single-turn dataset; exact bitwise equivalence to the Spring 2026 Modal copy has not been independently verified.

## Compatibility / Blockers

| 组件 | 当前判断 |
| --- | --- |
| Baseline | 配置/prompt/parser READY；runner、权重与GPU smoke尚未做 |
| SFT | 模板/tokenizer sample READY；full准入BLOCKED（空字段、人审、Dataset/batching、训练硬件） |
| DPO | BLOCKED：未训练SFT、无同源policy/reference checkpoint、DPO未实现 |
| Judge | 配置/semantic/nativechat READY；72B inference、parser mock、真实winrate/LC未验收 |

详细[Llama假设审计](compatibility-audit.md)、[Judge方案](judge-compatibility.md)。Qwen2ForCausalLM config解析成功不证明FA2完整模型训练已可运行；5090环境kernel旧验收通过但不是本轮7B smoke。正式SFT优先80GB；Judge优先2×80GB并实测并发/KV余量。未使用量化/LoRA/offload。

## Tests

- 本地：`/Users/hr/Documents/Lesson/assignment5-alignment/.venv/bin/python -m pytest tests/test_qwen_preflight.py tests/test_metrics.py tests/test_supplement_metrics_edges.py -q --tb=short`：**30 passed**。含原4个parser、16边界、10个Qwen/schema/持久Judge模板检查。
- `UV_CACHE_DIR=/tmp/pa5-qwen-uv-cache UV_PROJECT_ENVIRONMENT=/Users/hr/Documents/Lesson/assignment5-alignment/.venv uv run --no-sync pytest tests/test_data.py tests/test_dpo.py tests/test_metrics.py -q --tb=short`：**4 passed / 3 NotImplemented**。前两项在PackedSFTDataset hook失败，batching未独立运行到；DPO hook未实现。初次uv默认cache无权限，改为可写临时cache后得到真实测试结果，日志均保留。
- `python -m pytest tests/test_grpo.py -q --tb=short`：**19 NotImplemented**，隔离Supplement官方脚手架；未改Main已实现O2，不以复制Main实现隐藏失败。
- pinned restore本地21项bytes/SHA全部核验；定向拒答采样重算逐字一致。
- 云端CPU验收：sanity/parser **30 passed**、官方 **4 passed / 3 NotImplemented**；21项源文件bytes/SHA通过，8项独立审计产物与本地逐字节相同。新增SCP连接间歇重置，最终通过已有SSH会话完整取回28KB日志包并核验内容。

## Raw Artifact Paths / Reproducibility

[preflight manifest / sources / tests / review / checksum](../../../artifacts/pa5-supplement-qwen/preflight/20261002/)。原数据在本地与云端登记目录；21项大小/固定URL/SHA见download-inventory与统一artifact-registry。

`python scripts/restore_qwen_preflight_assets.py`：只允许两模型小文件与三指定数据/README；校验失败hard stop。`python scripts/qwen_preflight.py --output /tmp/qwen-fresh-audit`：CPU完整验收与20条抽样；另一个refusal脚本复现3条定向样本。已存在输出目录拒绝覆盖。

小证据入Git，大raw/tokenizer由固定源恢复并保留本地副本。公共upstream持久性不受我们控制；未来训练checkpoint不可用下载Base恢复，必须独立持久化。
执行基准commit为3921eaf，Qwen代码执行时dirty，manifest保存源文件hash；归档commit从该文件Git历史读取，避免伪称运行于干净commit。

## Official vs Adapted / Product Interpretation

变化包括policy/judge模型、tokenizer、EOS与token统计、Judge chat包装及默认采样显式覆盖、第三方历史SFT镜像、环境/日期与Safety invalid审计。不能与官方Llama绝对指标直接作模型优劣判断。
Qwen内部仍有Base→SFT外层prompt变化、单seed和judge偏好混杂；主要观察“数据→行为→评估→偏好”的链路，不能把所有提升归于训练。

## Next Gate / Learning Check

建议经批准进入Qwen7B Baseline：runner CPU dry-run → 各任务1-example smoke → 各20-example pilot。下阶段可以固定版本下载7B权重；本轮没有执行。结束本轮后停止，等待批准。
SFT先核查24空字段并确认派生过滤规则，再Dataset/batching→sample数据pipeline→10–50步smoke→full，各Gate单独验收。人审待用户实际填写。
学习检查（待答，不声称已理解）：为什么同一个模型的tokenizer BOS和config BOS可以不同？为什么PAD==EOS时按ID遮罩会破坏训练信号？为什么换Judge后不能直接比较Llama与Qwen绝对胜率？
