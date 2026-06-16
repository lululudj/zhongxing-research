"""众星管道测试 - 35B MoE大脑"""
import sys, time
sys.path.insert(0, '.')
from zhongxing_agent import *

text = """人工智能在医疗领域取得了重大突破。2024年，Google DeepMind发布了AlphaFold 3，能够精确预测蛋白质结构和相互作用。
该模型采用了扩散模型架构，在药物发现领域引发了革命。与此同时，OpenAI与哈佛医学院合作开发的MedGPT系统，
在临床诊断测试中准确率达到95.7%，超过了资深医生的平均水平。然而，专家警告AI在医疗领域的应用仍面临
数据隐私、算法公平性和监管审批等挑战。欧盟率先通过了AI法案，要求高风险AI系统必须通过严格的安全审查。"""

questions = [
    "AlphaFold 3是谁发布的？有什么功能？",
    "MedGPT的准确率是多少？",
    "AI医疗面临哪些挑战？",
]

config = FALLBACK_CONFIG.copy()
config["big_brain_model"] = "qwen3.6:35b-a3b"
config["eagle_eye_enabled"] = True

print("=" * 50)
print("众星管道测试 (35B MoE大脑)")
print("=" * 50)
print(f"原文: {len(text)}字, {len(questions)}题")
print(f"大脑: {config['big_brain_model']}")
print()

t0 = time.time()

# Layer 0
print("[1/4] 维度自发现...")
schema = discover_schema(text, config["schema_model"])
print(f"  类型: {schema['text_type']}")

# Layer 1
print(f"[2/4] 提取 ({config['num_extractors']}并行)...")
ext = run_extractors(text, schema, config["extractor_model"], config["num_extractors"])

# Layer 2
print("[3/4] RRF融合...")
fusion = rrf_fuse(ext, config["schema_model"], len(text))
compact = fusion["compact_context"]
print(f"  压缩: {len(text)}->{len(compact)}字 ({len(text)/max(len(compact),1):.1f}:1)")
print(f"  机语: {compact[:300]}")

# Layer 3
print(f"\n[4/4] 大脑推理...")
for i, q in enumerate(questions):
    pipe = big_brain_answer(fusion, q, config["big_brain_model"],
                           text, config["schema_model"],
                           config.get("max_feedback_rounds", 1),
                           vram_folding=False, vram_limit=0,
                           eagle_eye=True, eagle_eye_model=config["eagle_eye_model"])
    print(f"  Q{i+1}: {q}")
    print(f"  答: {pipe['answer'][:200]}")
    print(f"  ({pipe['time']}s)")
    print()

total = round(time.time() - t0, 1)
print(f"总耗时: {total}s")
