# zhongxing — 语义压缩管道

<div align="center">

**人语 → 机语 · 让老设备拥有长文本问答能力**

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](./LICENSE)
[![Ollama](https://img.shields.io/badge/Ollama-Ready-orange.svg)](https://ollama.com/)

</div>

---

## 这是什么？

zhongxing 是一个**语义压缩管道**，让 **GTX 1060 6GB + 16GB RAM** 级老旧设备也能高效运行大模型（如 DeepSeek V4-Flash），实现长文本深度问答。

**核心思路**：不是让小模型勉强够用，而是通过压缩管道把人类语言转译成"机语"——一种零歧义的结构化紧凑表示，让大模型以最少的 token 完成推理。

```
原文 → 分块 → [小脑×3 并行提取] → RRF融合+紧凑化 → 补漏 → 机语
                                                              ↓
问题 → 大脑(14b) ← 机语(紧凑行格式) → 自然语言回答（含反馈环）
```

---

## 核心理念

> **压缩不是删减，是编码。**

人类语言充满冗余——修饰词、程度副词、因果连接词等。这些对人类理解有帮助，但对模型推理是噪声