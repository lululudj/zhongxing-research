"""10题对比测试 — 3B Pipeline vs DeepSeek GLM"""
import sys, os, time, json, traceback

sys.path.insert(0, os.path.dirname(__file__))
from zhongxing_agent import (
    call_ollama, universal_extract, big_brain_answer, serialize_compact,
    fold_cleanup, nvidia_smi
)

import requests

ZHIPU_KEY = "8314b6afbe96464285305357384eab38.nmeOEbGAwESwihzk"
ZHIPU_URL = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
ZHIPU_MODEL = "glm-4-flash"

LOG_FILE = os.path.join(os.path.dirname(__file__), "10q_vs_v4_log.txt")
REPORT_FILE = os.path.join(os.path.dirname(__file__), "10q_vs_v4_report.json")

def log(msg):
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(msg + "\n")
            f.flush()
    except:
        pass
    try:
        print(msg, flush=True)
        sys.stdout.flush()
    except:
        pass

def call_glm(prompt, max_tokens=512):
    """调用智谱 GLM API"""
    headers = {
        "Authorization": f"Bearer {ZHIPU_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": ZHIPU_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": 0.0
    }
    r = requests.post(ZHIPU_URL, json=payload, headers=headers, timeout=60)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]

FAST_SCHEMA = {"text_type": "通用", "entity_types": ["人物","机构","概念"],
               "attr_types": ["属性","数值","时间"], "rel_types": ["关系","因果"]}

TEST_CASES = [
    ("科技", "2022年11月，OpenAI发布了ChatGPT，基于GPT-3.5架构，拥有1750亿参数。", "ChatGPT基于什么架构？有多少参数？"),
    ("科技", "台积电3纳米制程主要客户包括苹果、英伟达和AMD。全球芯片代工市场份额超过55%。", "台积电的3纳米制程主要客户有哪些？"),
    ("科技", "2019年谷歌Sycamore处理器在200秒内完成传统超算需1万年的计算。", "谷歌量子霸权处理器叫什么？用了多少秒？"),
    ("历史", "秦始皇于公元前221年统一六国，推行书同文、车同轨。", "秦始皇哪年统一六国？推行什么政策？"),
    ("历史", "法国大革命1789年爆发，1793年路易十六被送上断头台。", "法国大革命哪年爆发？路易十六结局？"),
    ("法律", "民法典共7编1260条，2021年1月1日施行。", "民法典共几编多少条？"),
    ("医学", "DNA双螺旋由沃森和克里克1953年发现。", "DNA双螺旋哪年发现？谁发现？"),
    ("财经", "比特币由中本聪2009年创建，总量上限2100万枚。", "比特币总量上限？谁创建？"),
    ("地理", "珠穆朗玛峰海拔8848.86米。", "珠峰最新测量高度？"),
    ("物理", "爱因斯坦1905年提出狭义相对论，公式E=mc²。", "狭义相对论公式？哪年提出？"),
]

EXTRACTOR = "qwen2.5:1.5b"
BRAIN = "qwen2.5:3b"
EAGLE = "qwen2.5:3b"

# 清理
for f in [LOG_FILE, REPORT_FILE]:
    try: os.remove(f)
    except: pass

log("=" * 70)
log("10题对比测试: 3B Pipeline vs DeepSeek GLM (裁判)")
log("=" * 70)
log(f"模型: 提取{EXTRACTOR} | 推理{BRAIN} | 鹰眼{EAGLE} | 裁判: deepseek-chat")

results = []
total_start = time.time()

for idx, (domain, text, question) in enumerate(TEST_CASES):
    q_start = time.time()
    r = {"idx": idx, "domain": domain, "question": question}
    log(f"\n--- [{idx+1}/10] {domain}: {question} ---")
    
    # Step 1: GLM 直接回答 (标准答案)
    try:
        v4_answer = call_glm(f"根据以下文本回答问题:\n{text}\n\n问题: {question}")
        r["v4_answer"] = v4_answer
        log(f"  GLM: {v4_answer[:120]}")
    except Exception as e:
        r["v4_answer"] = f"V4_ERROR: {e}"
        log(f"  GLM ERR: {e}")
    
    # Step 2: 3B Pipeline 回答 (v2.0优化: 问题导向提取)
    try:
        extraction = universal_extract(text, idx % 3, FAST_SCHEMA, EXTRACTOR, question=question)
        ents = extraction.get("entities", [])
        compact = serialize_compact({"E": ents})
        r["entity_count"] = len(ents)
        
        fusion = {"E": ents, "compact_context": compact}
        pipe = big_brain_answer(
            fusion, question, BRAIN, text, BRAIN, 1,
            vram_folding=True, vram_limit=6144,
            eagle_eye=True, eagle_eye_model=EAGLE
        )
        r["pipeline_answer"] = pipe["answer"]
        r["pipeline_time"] = round(time.time() - q_start, 1)
        r["eagle_verdict"] = pipe.get("eagle_eye", {}).get("verdict", "N/A")
        log(f"  3B管线 ({r['pipeline_time']}s): {pipe['answer'][:120]}")
    except Exception as e:
        traceback.print_exc()
        r["pipeline_answer"] = f"ERROR: {e}"
        r["pipeline_time"] = round(time.time() - q_start, 1)
        log(f"  3B管线 ERR: {e}")
    
    # Step 3: GLM 裁判 — 对比两个答案
    if r.get("v4_answer") and r.get("pipeline_answer") and "ERROR" not in r["pipeline_answer"] and "V4_ERROR" not in r["v4_answer"]:
        judge_prompt = f"""你是严格的阅卷老师。下面有一个问题、原文、标准答案和学生答案。
请判断学生答案是否正确，并给出评分。

规则:
- 学生答案的核心事实必须与标准答案一致
- 用词不同但意思相同算对
- 部分正确部分错误算错
- 学生答案如果包含了额外的不相关信息但核心答案正确，算对

原文: {text}
问题: {question}
标准答案(GLM): {r['v4_answer']}
学生答案(3B Pipeline): {r['pipeline_answer']}

请严格按以下格式输出(只输出这三行，不要多写):
判定: CORRECT 或 INCORRECT
理由: (一句话说明为什么对或错)
评分: X/10"""
        try:
            judge = call_glm(judge_prompt, max_tokens=256)
            r["judge_result"] = judge
            first_line = judge.split("\n")[0] if judge else ""
            r["is_correct"] = "INCORRECT" not in first_line and "CORRECT" in first_line
            log(f"  裁判: {judge.replace(chr(10), ' | ')}")
        except Exception as e:
            r["judge_result"] = f"JUDGE_ERROR: {e}"
            r["is_correct"] = None
            log(f"  裁判 ERR: {e}")
    else:
        r["is_correct"] = None
        r["judge_result"] = "SKIPPED (error in one of the answers)"
    
    results.append(r)
    
    # 清理VRAM
    try:
        fold_cleanup([BRAIN])
    except:
        pass

# 统计
total_time = round(time.time() - total_start, 1)
correct_count = sum(1 for r in results if r.get("is_correct") is True)
incorrect_count = sum(1 for r in results if r.get("is_correct") is False)
unknown_count = sum(1 for r in results if r.get("is_correct") is None)
pipeline_times = [r["pipeline_time"] for r in results if r.get("pipeline_time")]

log("\n" + "=" * 70)
log("              10题对比测试报告")
log("=" * 70)
log(f"  正确: {correct_count}/10 | 错误: {incorrect_count} | 无法判定: {unknown_count}")
log(f"  正确率: {correct_count}/{correct_count+incorrect_count} ({correct_count/(correct_count+incorrect_count)*100:.1f}%)" if (correct_count+incorrect_count) > 0 else "  正确率: N/A")
log(f"  3B管线平均耗时: {round(sum(pipeline_times)/len(pipeline_times),1)}s" if pipeline_times else "  3B管线平均耗时: N/A")
log(f"  总耗时: {total_time}s ({total_time/60:.1f}min)")

log(f"\n{'#':<3} {'领域':<6} {'问题':<30} {'判定':<10} {'管线耗时':<8}")
log("-" * 60)
for r in results:
    q_short = r["question"][:28]
    verdict = "CORRECT" if r.get("is_correct") is True else ("WRONG" if r.get("is_correct") is False else "N/A")
    t = r.get("pipeline_time", "?")
    log(f"{r['idx']+1:<3} {r['domain']:<6} {q_short:<30} {verdict:<10} {t}s")

# 保存报告
report = {
    "test_time": time.strftime("%Y-%m-%d %H:%M:%S"),
    "summary": {
        "total": 10, "correct": correct_count, "incorrect": incorrect_count,
        "unknown": unknown_count,
        "accuracy": round(correct_count/(correct_count+incorrect_count)*100, 1) if (correct_count+incorrect_count) > 0 else None,
        "avg_pipeline_time": round(sum(pipeline_times)/len(pipeline_times), 1) if pipeline_times else None,
        "total_time": total_time
    },
    "details": [{
        "idx": r["idx"]+1, "domain": r["domain"], "question": r["question"],
        "v4_answer": r.get("v4_answer", ""),
        "pipeline_answer": r.get("pipeline_answer", ""),
        "is_correct": r.get("is_correct"),
        "judge_result": r.get("judge_result", ""),
        "pipeline_time": r.get("pipeline_time", 0),
        "eagle_verdict": r.get("eagle_verdict", "N/A")
    } for r in results]
}
with open(REPORT_FILE, "w", encoding="utf-8") as f:
    json.dump(report, f, ensure_ascii=False, indent=2)

log(f"\n详细报告: {REPORT_FILE}")
log("测试完成!")