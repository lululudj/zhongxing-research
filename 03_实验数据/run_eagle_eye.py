import urllib.request, json, subprocess, time, sys
sys.path.insert(0, r'e:\zhongxing2')
import zhongxing_agent as zx

log_path = r'e:\zhongxing2\eagle_eye_result.txt'

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
fusion["compact_context"] = zx.serialize_compact(fusion["fused_context"])
log(f"Fused: {len(fusion['fused_context'].get('E',[]))} entities, compact={len(fusion['compact_context'])} chars")

# 阶段4: 大脑推理 + 鹰眼校验
log("\n=== Stage 4: Big Brain + Eagle Eye ===")
for i, q in enumerate(questions):
    log(f"\nQ{i+1}: {q}")
    
    result = zx.big_brain_answer(fusion, q, "qwen2.5:14b",
                                  text=text, fuse_brain_model="qwen2.5:3b",
                                  max_rounds=2, vram_folding=True, vram_limit=6144,
                                  eagle_eye=True, eagle_eye_model="qwen2.5:3b")
    log(f"  Answer: {result['answer'][:200]}")
    log(f"  Time: {result['time']}s, Feedback: {result['feedback_rounds']}")
    
    ee = result.get("eagle_eye")
    if ee:
        log(f"  Eagle Eye: {ee['verdict']} ({ee['time']}s)")
        if ee['verdict'] in ('WRONG', 'AMBIGUOUS'):
            log(f"    Issue: {ee['issue'][:150]}")
            log(f"    Corrected: {ee['corrected'][:200]}")
            log(f"    Reason: {ee['reason'][:150]}")
    
    zx.fold_cleanup(["qwen2.5:14b"])
    time.sleep(2)

zx.fold_cleanup()
used_final, free_final, _ = zx.nvidia_smi()
log(f"\nFinal VRAM: {used_final}/{total} MiB")
log("=== E2E Test Complete ===")