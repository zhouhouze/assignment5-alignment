# P3 下一节：SFT Packed Dataset — CPU 学习入口（未启动训练）

**Status: READ-ONLY KICKOFF, NOT P3 EXECUTION PASS; P2 Data Admission still PENDING.** 用户要求AI-first收尾后直接进入下一步，故仅在已读取官方测试与接口文档的范围内完成CPU学习准备，不修改任何student TODO、不训练、不使用GPU。

## 本轮阅读的真实接口

- `tests/adapters.py:get_packed_sft_dataset(tokenizer, dataset_path, seq_length, shuffle)` 目前仍是 `NotImplementedError`。
- `tests/adapters.py:run_iterate_batches(dataset, batch_size, shuffle)` 也未实现。
- `tests/test_data.py::test_packed_sft_dataset`：官方Llama fixture，`seq_length=32`，需逐例比较 `input_ids/labels` 与固定参考；再验证先shuffle文档。
- `tests/test_data.py::test_iterate_batches`：`batch_size=8`，期望dataset有75条、批次 `ceil(75/8)`，最后一批允许不足8；两键均为long tensor。
- Qwen适配实验的正式training设计是packed `L=512`、EOS ID 151643、full-token next-token目标。先按官方测试验证通用 Dataset 接口，再在已批准数据视图上做Qwen额外CPU sanity。

## 一个课堂口算示例（非真实Tokenizer输出）

假设拼接后的Token流为 [A,B,EOS,C,D,EOS]，`seq_length=3`。则首个packed训练位置的 `input_ids` 是 [A,B,EOS]，对应 `labels` 是 [B,EOS,C]。**EOS跨文档边界保留，labels相对input仅右移一次；不能按每条文档独立截断或再次shift。**

## 教学与工程最小下一步

Codex先说明官方fixture与函数的输入/输出、关键边界（EOS、shuffle、lookahead、尾部舍弃、最后batch），写最小toy检查说明。得到该组件的单独实施授权及P2准入或明确允许使用不含真实train的fixture后，才分组件实现并运行窄测试。不给现有19项GRPO NotImplemented虚假的PASS。

GPU=NOT REQUIRED，P4全参Qwen7B训练的硬件/预算另审，当前 RTX5090 32GB不能默认胜任普通AdamW全参数训练。
