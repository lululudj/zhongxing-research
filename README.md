# 众星研究成果 — 在32GB内存笔记本上运行284B DeepSeek V4-Flash

> **私有仓库 — 完整研究记录**

---

## 目录结构

```
01_编译与部署/       - llama.cpp-deepseek-v4-flash 编译脚本、模型配置
02_众星管道/         - 众星管道核心代码（zhongxing_agent/moe/server）
03_实验数据/         - 基准测试脚本和结果数据
04_速度优化探索/     - GPU加速/mmap/推测解码尝试记录
05_项目文档/         - 完整项目文档（架构/版本/调研/bug记录）
```

## 核心成果

1. **编译成功** antirez/llama.cpp-deepseek-v4-flash fork（唯一支持deepseek4架构的引擎）
2. **86GB模型在32GB RAM上运行** 通过mmap内存映射突破物理内存限制
3. **众星管道验证通过** 前3层（发现+提取+压缩）仅需5.4秒
4. **端到端推理成功** V4-Flash在消费级笔记本上生成文本

## 硬件环境

- CPU: Intel i7-13620H（16线程）
- GPU: NVIDIA RTX 4060 Laptop（8GB显存）
- RAM: 32GB DDR4
- 模型: DeepSeek V4-Flash IQ2_XXS（86.7GB）

## 关联仓库

- 众星2.0代码：https://github.com/lululudj/zhongxing2
- 众星3.0文章：https://github.com/lululudj/zhongxing3
