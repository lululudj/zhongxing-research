"""Quick test - 14B brain pipeline"""
import sys, os, json, time, urllib.request, urllib.error, traceback
sys.path.insert(0, r"e:\zhongxing2")
import zhongxing_agent
from zhongxing_agent import (
    discover_schema, run_extractors, rrf_fuse,
    serialize_compact, entity_gap_check, cooccurrence_scan,
    big_brain_answer, FALLBACK_CONFIG
)

config = dict(FALLBACK_CONFIG)
config["big_brain_model"] = "qwen2.5:14b"
config["max_feedback_rounds"] = 0
context = "萧炎抬头望向那巨大的黑角域方向。药老沉声道：韩枫，我那不肖弟子，当年若非他偷袭，我也不至于落到这般田地。韩枫如今已是斗皇强者。小医仙天生厄难毒体，不修炼也能自动吸收天地毒素提升实力。美杜莎是蛇人族的女王，乃是斗宗级别的强者。"
questions = ["药老的叛徒弟子是谁？", "小医仙有什么特殊体质？", "美杜莎的实力等级是什么？"]

def log(msg):
    print(msg, flush=True)

log(f"Config: {json.dumps(config, ensure_ascii=False)}")
log(f"Context: {len(context)} chars")

try:
    # Step 1: Compression (uses 3B + 1.5B)
    log("\n[1] Compressing...")
    t0 = time.time()
    schema = discover_schema(context, config["schema_model"])
    log(f"  Schema: {json.dumps(schema, ensure_ascii=False)} ({time.time()-t0:.1f}s)")
    
    t0 = time.time()
    extractions = run_extractors(context, schema, config["extractor_model"], 3)
    log(f"  Extractors: {sum(len(e['entities']) for e in extractions)} entities ({time.time()-t0:.1f}s)")
    
    t0 = time.time()
    fusion = rrf_fuse(extractions, config["schema_model"], len(context))
    if isinstance(fusion["fused_context"], list):
        fusion["fused_context"] = {"E": fusion["fused_context"]}
    log(f"  RRF: {len(fusion['fused_context'].get('E',[]))} entities ({time.time()-t0:.1f}s)")
    
    t0 = time.time()
    gap = entity_gap_check(context, fusion["fused_context"], config["schema_model"])
    if gap["missing"]:
        ex = fusion["fused_context"].get("E", [])
        if isinstance(ex, list):
            ex.extend(gap.get("supplements", []))
    log(f"  Gap: {gap.get('supplement_count',0)} supplements ({time.time()-t0:.1f}s)")
    
    cooccurrence_scan(context, fusion["fused_context"])
    compact = serialize_compact(fusion["fused_context"])
    ratio = len(context) / max(len(compact), 1)
    log(f"  Compact: {len(context)}->{len(compact)} chars ({ratio:.1f}:1)")
    log(f"  Machine: {compact[:300]}")
    log("  COMPRESSION DONE!")

    # Step 2: Direct answers (14B)
    log("\n[2] Direct answers (14B)...")
    for qi, q in enumerate(questions):
        t0 = time.time()
        prompt = f"根据上下文回答：\n\n{context}\n\n问：{q}"
        try:
            ans = zhongxing_agent.call_ollama("qwen2.5:14b", prompt, timeout=300)
            log(f"  Q{qi+1} ({time.time()-t0:.1f}s): {ans[:200]}")
        except Exception as e:
            log(f"  Q{qi+1} ERROR: {e}")
    log("  DIRECT DONE!")

    # Step 3: Pipeline answers (14B)
    log("\n[3] Pipeline answers (14B)...")
    for qi, q in enumerate(questions):
        t0 = time.time()
        try:
            ans = big_brain_answer(fusion, q, "qwen2.5:14b", context, config["schema_model"], max_rounds=0)
            log(f"  Q{qi+1} ({time.time()-t0:.1f}s): {ans.get('answer','')[:200]}")
        except Exception as e:
            log(f"  Q{qi+1} ERROR: {e}")
    log("  PIPELINE DONE!")

    log("\nALL DONE!")
except Exception as e:
    log(f"FATAL: {e}")
    traceback.print_exc()