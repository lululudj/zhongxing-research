import urllib.request, json, subprocess, time, sys
sys.path.insert(0, r'e:\zhongxing2')
import zhongxing_agent as zx

# 快速端到端测试，输出到文件
log_path = r'e:\zhongxing2\e2e_result.txt'

def log(msg):
    print(msg, flush=True)
    with open(log_path, 'a', encoding='utf-8') as f:
        f.write(msg + '\n')

open(log_path, 'w', encoding='utf-8').close()

# 先卸载所有
for m in ['qwen2.5:1.5b', 'qwen2.5:3b', 'qwen2.5:14b']:
    zx.unload_model(m)
time.sleep(3)

used, free, total = zx.nvidia_smi()
log(f"Baseline VRAM: {used}/{total} MiB")

text = zx.TEST_TEXT
questions = zx.TEST_QUESTIONS

# 阶段1-3: 提取+融合
log("\n=== Stage 1-3: Extraction ===")
schema = zx.discover_schema(text, "qwen2.5:3b")
log(f"Schema: {schema['text_type']}")

extractions = zx.run_extractors(text, schema, "qwen2.5:1.5b", 3)
total_ents = sum(len(e["entities"]) for e in extractions)
log(f"Extracted: {total_ents} entities")

fusion = zx.rrf_fuse(extractions, "qwen2.5:3b", len(text))
log(f"Fused: {len(fusion['fused_context'].get('E', []))} entities, compact={len(fusion['compact_context'])} chars")

used1, free1, _ = zx.nvidia_smi()
log(f"VRAM after extraction: {used1}/{total} MiB")

# 阶段4: 大脑推理 (VRAM折叠ON)
log("\n=== Stage 4: Big Brain (VRAM Folding ON) ===")
for i, q in enumerate(questions):
    log(f"\nQ{i+1}: {q}")
    used_before, _, _ = zx.nvidia_smi()
    
    result = zx.big_brain_answer(fusion, q, "qwen2.5:14b",
                                  text=text, fuse_brain_model="qwen2.5:3b",
                                  max_rounds=2, vram_folding=True, vram_limit=6144)
    log(f"  Answer: {result['answer'][:200]}")
    log(f"  Time: {result['time']}s, Feedback: {result['feedback_rounds']}")
    
    used_after, _, _ = zx.nvidia_smi()
    log(f"  VRAM delta: {used_after - used_before} MiB")
    
    # 每问后卸载14B
    zx.fold_cleanup(["qwen2.5:14b"])
    time.sleep(2)

# 最终清理
zx.fold_cleanup()
used_final, free_final, _ = zx.nvidia_smi()
log(f"\nFinal VRAM: {used_final}/{total} MiB (delta={used_final - used} MiB)")
log("=== E2E Test Complete ===")