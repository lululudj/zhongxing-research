"""众星系统全面实验 — 标准基准 + 消融 + Baseline + VRAM分析"""
import sys, os, time, json, traceback
sys.path.insert(0, os.path.dirname(__file__))
from zhongxing_agent import (
    call_ollama, universal_extract, big_brain_answer, serialize_compact,
    fold_cleanup, nvidia_smi, compactify_entity
)
import requests

ZHIPU_KEY = "8314b6afbe96464285305357384eab38.nmeOEbGAwESwihzk"
ZHIPU_URL = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
ZHIPU_MODEL = "glm-4-flash"

LOG_DIR = os.path.join(os.path.dirname(__file__), "experiment_results")
os.makedirs(LOG_DIR, exist_ok=True)

def log_markdown(path, msg):
    with open(path, "a", encoding="utf-8") as f:
        f.write(msg + "\n")

def call_glm(prompt, max_tokens=512):
    headers = {"Authorization": f"Bearer {ZHIPU_KEY}", "Content-Type": "application/json"}
    payload = {"model": ZHIPU_MODEL, "messages": [{"role": "user", "content": prompt}],
               "max_tokens": max_tokens, "temperature": 0.0}
    r = requests.post(ZHIPU_URL, json=payload, headers=headers, timeout=60)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]

# ============ 测试题集 (MMLU风格多选题 + TruthfulQA风格事实题 + HotpotQA风格多跳题) ============
QUESTIONS = [
    # --- MMLU风格: 多选题 ---
    {"domain": "MMLU-Physics", "text": "牛顿第二定律指出，物体的加速度与作用力成正比，与质量成反比，公式为F=ma。",
     "question": "牛顿第二定律的公式是什么？\nA) E=mc² B) F=ma C) PV=nRT D) v=at\n请选择正确选项。", "id": "MMLU-1"},
    {"domain": "MMLU-Biology", "text": "线粒体是真核细胞中的一种细胞器，被称为细胞的能量工厂，通过氧化磷酸化产生ATP。",
     "question": "真核细胞中被称为'能量工厂'的细胞器是什么？\nA) 叶绿体 B) 线粒体 C) 核糖体 D) 内质网\n请选择正确选项。", "id": "MMLU-2"},
    {"domain": "MMLU-History", "text": "法国大革命于1789年爆发，1793年路易十六被送上断头台，革命持续约10年。",
     "question": "法国大革命爆发于哪一年？\nA) 1776年 B) 1789年 C) 1793年 D) 1804年\n请选择正确选项。", "id": "MMLU-3"},
    {"domain": "MMLU-Law", "text": "中华人民共和国民法典共7编1260条，于2021年1月1日起施行。",
     "question": "民法典共多少编？\nA) 5编 B) 6编 C) 7编 D) 8编\n请选择正确选项。", "id": "MMLU-4"},
    {"domain": "MMLU-Geography", "text": "撒哈拉沙漠位于非洲北部，面积约940万平方公里，是世界最大的热沙漠。",
     "question": "撒哈拉沙漠面积约多少万平方公里？\nA) 500万 B) 940万 C) 1200万 D) 300万\n请选择正确选项。", "id": "MMLU-5"},
    # --- TruthfulQA风格: 事实判断题 ---
    {"domain": "TruthfulQA", "text": "新型冠状病毒的正式名称为SARS-CoV-2，引起的疾病名为COVID-19。mRNA疫苗由辉瑞和莫德纳开发。",
     "question": "新冠病毒的正式名称是什么？谁开发了mRNA疫苗？", "id": "TFQA-1"},
    {"domain": "TruthfulQA", "text": "青霉素由亚历山大·弗莱明于1928年在伦敦圣玛丽医院偶然发现，从此开启了抗生素时代。",
     "question": "青霉素是谁在什么时候发现的？", "id": "TFQA-2"},
    {"domain": "TruthfulQA", "text": "比特币是一种去中心化的数字货币，于2009年由化名'中本聪'的人创建，总量上限为2100万枚。",
     "question": "比特币由谁创建？总量上限是多少？", "id": "TFQA-3"},
    {"domain": "TruthfulQA", "text": "广义相对论由爱因斯坦在1915年提出。狭义相对论则是1905年提出的，包含著名的公式E=mc²。",
     "question": "狭义相对论是哪一年由谁提出的？包含什么公式？", "id": "TFQA-4"},
    {"domain": "TruthfulQA", "text": "珠穆朗玛峰是地球最高峰，2020年中尼联合测量的最新高度为8848.86米。",
     "question": "珠穆朗玛峰的最新测量高度是多少？", "id": "TFQA-5"},
    # --- HotpotQA风格: 多跳推理 ---
    {"domain": "HotpotQA", "text": "苹果公司由史蒂夫·乔布斯、史蒂夫·沃兹尼亚克和罗纳德·韦恩于1976年创立。2007年，苹果发布了第一代iPhone，从此改变了手机行业。",
     "question": "iPhone是哪家公司哪一年发布的？", "id": "HPQA-1"},
    {"domain": "HotpotQA", "text": "Linux操作系统由芬兰人林纳斯·托瓦兹于1991年创建，采用GNU通用公共许可证(GPL)发布。托瓦兹出生于芬兰赫尔辛基，他的祖父是统计学家。",
     "question": "谁创建了Linux？采用什么许可证？", "id": "HPQA-2"},
    {"domain": "HotpotQA", "text": "秦始皇嬴政于公元前221年统一六国，建立了中国第一个大一统王朝秦朝。他推行书同文、车同轨、统一度量衡等政策。",
     "question": "秦始皇哪年统一六国？推行了哪些政策？", "id": "HPQA-3"},
    {"domain": "HotpotQA", "text": "詹姆斯·瓦特于1765年发明了新型蒸汽机并在1769年获得专利。瓦特的改进使得蒸汽机效率大幅提高，成为工业革命的标志性发明。",
     "question": "瓦特在什么年份获得蒸汽机专利？", "id": "HPQA-4"},
    {"domain": "HotpotQA", "text": "COVID-19疫情由SARS-CoV-2病毒引起，2020年3月WHO宣布全球大流行。辉瑞-BioNTech和Moderna分别开发了mRNA疫苗。",
     "question": "COVID-19的mRNA疫苗是由哪两家公司开发的？", "id": "HPQA-5"},
]

EXTRACTOR = "qwen2.5:1.5b"
BRAIN = "qwen2.5:3b"
EAGLE = "qwen2.5:3b"
BIG_MODEL = "qwen2.5:14b"
FAST_SCHEMA = {"text_type": "通用", "entity_types": ["人物","机构","概念"],
               "attr_types": ["属性","数值","时间"], "rel_types": ["关系","因果"]}

def judge_answer(question, text, student_answer, judge_id=""):
    """GLM裁判: 判断学生答案是否正确"""
    prompt = f"""你是严格的阅卷老师。根据原文判断学生答案是否正确。
原文: {text}
问题: {question}
学生答案: {student_answer}
只输出一行: CORRECT 或 INCORRECT"""
    try:
        result = call_glm(prompt, max_tokens=50)
        return "CORRECT" in result
    except:
        return None

def log_gpu(label=""):
    used, free, total = nvidia_smi()
    if used:
        return f"GPU: {used}/{total}MiB ({free}MiB free)"
    return "GPU: N/A"

# ============ 清理旧文件 ============
report_path = os.path.join(LOG_DIR, "experiment_report.md")
json_path = os.path.join(LOG_DIR, "experiment_data.json")
for f in [report_path, json_path]:
    try: os.remove(f)
    except: pass

md = lambda s: log_markdown(report_path, s)
all_data = {}

md("# 众星系统全面实验报告")
md(f"\n**时间**: {time.strftime('%Y-%m-%d %H:%M:%S')}")
md(f"\n**硬件**: GTX 1060 6GB")
md(f"**模型**: 提取{EXTRACTOR} | 推理{BRAIN} | 鹰眼{EAGLE} | 大军{BIG_MODEL}")
md(f"**裁判**: 智谱GLM-4-Flash")

# ===================================================================
# 实验1: 标准基准测试 (15题跨领域)
# ===================================================================
md("\n---\n## 实验1: 标准基准测试")
md("\n| # | 类型 | 问题 | 答案 | 判定 | 耗时 | 鹰眼 |")
md("|---|---|---|---|---|---|---|")

results_e1 = []
total_correct_e1 = 0
total_time_e1 = 0

for idx, q in enumerate(QUESTIONS):
    q_start = time.time()
    r = {"id": q["id"], "domain": q["domain"], "question": q["question"]}
    print(f"\n[实验1] {q['id']} {q['domain']}", flush=True)
    
    try:
        extraction = universal_extract(q["text"], idx % 3, FAST_SCHEMA, EXTRACTOR, question=q["question"])
        ents = extraction.get("entities", [])
        compact = serialize_compact({"E": ents})
        
        fusion = {"E": ents, "compact_context": compact}
        pipe = big_brain_answer(
            fusion, q["question"], BRAIN, q["text"], BRAIN, 1,
            vram_folding=True, vram_limit=6144,
            eagle_eye=True, eagle_eye_model=EAGLE
        )
        answer = pipe["answer"]
        r["answer"] = answer
        r["time"] = round(time.time() - q_start, 1)
        r["entities"] = len(ents)
        ee = pipe.get("eagle_eye")
        r["eagle"] = ee["verdict"] if ee else "N/A"
        
        correct = judge_answer(q["question"], q["text"], answer, q["id"])
        r["correct"] = correct
        if correct: total_correct_e1 += 1
        total_time_e1 += r["time"]
        
    except Exception as e:
        traceback.print_exc()
        r["answer"] = f"ERROR: {e}"
        r["time"] = round(time.time() - q_start, 1)
        r["correct"] = False
    
    try: fold_cleanup([BRAIN])
    except: pass
    
    results_e1.append(r)
    verdict = "✓" if r.get("correct") else "✗"
    ans_short = r.get("answer","")[:50].replace("|","/")
    md(f"| {idx+1} | {q['domain']} | {q['question'][:40]}... | {ans_short}... | {verdict} | {r['time']}s | {r.get('eagle','')} |")
    print(f"  [{verdict}] {r['time']}s", flush=True)

acc_e1 = round(total_correct_e1/len(QUESTIONS)*100, 1) if QUESTIONS else 0
avg_e1 = round(total_time_e1/len(QUESTIONS), 1) if QUESTIONS else 0
md(f"\n**实验1结果**: 正确 {total_correct_e1}/{len(QUESTIONS)} ({acc_e1}%) | 平均 {avg_e1}s/题")

all_data["experiment_1_benchmark"] = {"correct": total_correct_e1, "total": len(QUESTIONS),
    "accuracy": acc_e1, "avg_time": avg_e1, "details": results_e1}

# ===================================================================
# 实验2: 消融实验 (用前8题)
# ===================================================================
md("\n---\n## 实验2: 消融实验")
md("\n| 配置 | 正确 | 平均耗时 | 说明 |")
md("|---|---|---|---|")

ABLATION_CASES = QUESTIONS[:8]
ablation_configs = []

for config_name, config_desc in [
    ("full", "完整管线(提取+机语+鹰眼)"),
    ("no_eagle", "无鹰眼校验"),
    ("no_compact", "无结构化压缩(用原始提取JSON)"),
    ("no_extract", "无提取(原文直接入推理)"),
]:
    correct_count = 0
    total_time_ab = 0
    print(f"\n[消融] 配置: {config_name}", flush=True)
    
    for idx, q in enumerate(ABLATION_CASES):
        q_start = time.time()
        try:
            if config_name == "full":
                extraction = universal_extract(q["text"], idx % 3, FAST_SCHEMA, EXTRACTOR, question=q["question"])
                ents = extraction.get("entities", [])
                compact = serialize_compact({"E": ents})
                fusion = {"E": ents, "compact_context": compact}
                pipe = big_brain_answer(fusion, q["question"], BRAIN, q["text"], BRAIN, 1,
                    vram_folding=True, vram_limit=6144, eagle_eye=True, eagle_eye_model=EAGLE)
                
            elif config_name == "no_eagle":
                extraction = universal_extract(q["text"], idx % 3, FAST_SCHEMA, EXTRACTOR, question=q["question"])
                ents = extraction.get("entities", [])
                compact = serialize_compact({"E": ents})
                fusion = {"E": ents, "compact_context": compact}
                pipe = big_brain_answer(fusion, q["question"], BRAIN, q["text"], BRAIN, 1,
                    vram_folding=True, vram_limit=6144, eagle_eye=False)
                
            elif config_name == "no_compact":
                extraction = universal_extract(q["text"], idx % 3, FAST_SCHEMA, EXTRACTOR, question=q["question"])
                ents = extraction.get("entities", [])
                raw_json = json.dumps({"E": ents}, ensure_ascii=False)
                fusion = {"E": ents, "compact_context": raw_json}
                pipe = big_brain_answer(fusion, q["question"], BRAIN, q["text"], BRAIN, 1,
                    vram_folding=True, vram_limit=6144, eagle_eye=False)
                
            elif config_name == "no_extract":
                # 原文直接作为机语传入
                compact = q["text"]
                fusion = {"E": [], "compact_context": compact}
                pipe = big_brain_answer(fusion, q["question"], BRAIN, q["text"], BRAIN, 1,
                    vram_folding=True, vram_limit=6144, eagle_eye=False)
            
            answer = pipe["answer"]
            elapsed = round(time.time() - q_start, 1)
            total_time_ab += elapsed
            correct = judge_answer(q["question"], q["text"], answer)
            if correct: correct_count += 1
            
        except Exception as e:
            traceback.print_exc()
            elapsed = round(time.time() - q_start, 1)
            total_time_ab += elapsed
        
        try: fold_cleanup([BRAIN])
        except: pass
        
        print(f"  [{config_name}] {q['id']}: {'✓' if correct else '✗'} {elapsed}s", flush=True)
    
    acc = round(correct_count/len(ABLATION_CASES)*100, 1)
    avg_t = round(total_time_ab/len(ABLATION_CASES), 1)
    md(f"| {config_name} | {correct_count}/{len(ABLATION_CASES)} ({acc}%) | {avg_t}s | {config_desc} |")
    ablation_configs.append({"config": config_name, "desc": config_desc, "correct": correct_count,
        "total": len(ABLATION_CASES), "accuracy": acc, "avg_time": avg_t})

all_data["experiment_2_ablation"] = ablation_configs

# ===================================================================
# 实验3: Baseline对比 (用前6题, 避免14B太慢)
# ===================================================================
md("\n---\n## 实验3: Baseline对比")
md("\n| 模型 | 正确 | 平均耗时 | ")
md("|---|---|---|")

BASELINE_CASES = QUESTIONS[:6]
baseline_results = []

for model_name, model_id in [
    ("1.5B单独", EXTRACTOR),
    ("3B单独", BRAIN),
    ("14B单独", BIG_MODEL),
    ("众星管线(3B)", "pipeline"),
]:
    correct_count = 0
    total_time_bl = 0
    print(f"\n[Baseline] {model_name}", flush=True)
    
    for idx, q in enumerate(BASELINE_CASES):
        q_start = time.time()
        try:
            if model_id == "pipeline":
                extraction = universal_extract(q["text"], idx % 3, FAST_SCHEMA, EXTRACTOR, question=q["question"])
                ents = extraction.get("entities", [])
                compact = serialize_compact({"E": ents})
                fusion = {"E": ents, "compact_context": compact}
                pipe = big_brain_answer(fusion, q["question"], BRAIN, q["text"], BRAIN, 1,
                    vram_folding=True, vram_limit=6144, eagle_eye=True, eagle_eye_model=EAGLE)
                answer = pipe["answer"]
                try: fold_cleanup([BRAIN])
                except: pass
            else:
                prompt = f"根据以下文本回答问题:\n{q['text']}\n\n问题: {q['question']}"
                answer = call_ollama(model_id, prompt, "", timeout=120)
                try: fold_cleanup([model_id])
                except: pass
            
            elapsed = round(time.time() - q_start, 1)
            total_time_bl += elapsed
            correct = judge_answer(q["question"], q["text"], answer)
            if correct: correct_count += 1
            
        except Exception as e:
            traceback.print_exc()
            elapsed = round(time.time() - q_start, 1)
            total_time_bl += elapsed
        
        try: fold_cleanup([BRAIN, EXTRACTOR, BIG_MODEL])
        except: pass
        
        print(f"  [{model_name}] {q['id']}: {'✓' if correct else '(x)'} {elapsed}s", flush=True)
    
    acc = round(correct_count/len(BASELINE_CASES)*100, 1) if BASELINE_CASES else 0
    avg_t = round(total_time_bl/len(BASELINE_CASES), 1) if BASELINE_CASES else 0
    md(f"| {model_name} | {correct_count}/{len(BASELINE_CASES)} ({acc}%) | {avg_t}s |")
    baseline_results.append({"model": model_name, "correct": correct_count, "total": len(BASELINE_CASES),
        "accuracy": acc, "avg_time": avg_t})

all_data["experiment_3_baseline"] = baseline_results

# ===================================================================
# 实验4: VRAM调度定量分析
# ===================================================================
md("\n---\n## 实验4: VRAM调度分析")
md("\n| 阶段 | 时间 | GPU已用 | GPU空闲 | 说明 |")
md("|---|---|---|---|---|")

vram_log = []
def snap_vram(stage, desc=""):
    used, free, total = nvidia_smi()
    if used:
        entry = {"stage": stage, "time": time.strftime("%H:%M:%S"),
                 "used": used, "free": free, "total": total, "desc": desc}
        vram_log.append(entry)
        md(f"| {stage} | {entry['time']} | {used}MiB | {free}MiB | {desc} |")
        print(f"  [VRAM] {stage}: {used}/{total}MiB", flush=True)

snap_vram("初始状态", "无模型加载")

# 测试1.5B加载
try:
    call_ollama(EXTRACTOR, "test", "", timeout=30)
    snap_vram("加载1.5B", "提取模型加载后")
    fold_cleanup([EXTRACTOR])
    time.sleep(2)
    snap_vram("卸载1.5B", "提取模型卸载后")
except: pass

# 测试3B加载
try:
    call_ollama(BRAIN, "test", "", timeout=30)
    snap_vram("加载3B", "推理模型加载后")
    fold_cleanup([BRAIN])
    time.sleep(2)
    snap_vram("卸载3B", "推理模型卸载后")
except: pass

# 测试14B加载 (有VRAM折叠)
try:
    call_ollama(BIG_MODEL, "test", "", timeout=30)
    snap_vram("加载14B(VRAM折叠)", "大模型加载后(21层GPU)")
    fold_cleanup([BIG_MODEL])
    time.sleep(2)
    snap_vram("卸载14B", "大模型卸载后")
except: pass

# 测试完整管线一轮 (VRAM全程)
try:
    q = QUESTIONS[0]
    snap_vram("管线开始", "完整管线启动")
    fold_cleanup([EXTRACTOR, BRAIN, EAGLE, BIG_MODEL])
    time.sleep(2)
    snap_vram("管线清理后", "所有模型卸载")
    
    extraction = universal_extract(q["text"], 0, FAST_SCHEMA, EXTRACTOR, question=q["question"])
    snap_vram("提取完成", "1.5B提取后")
    
    ents = extraction.get("entities", [])
    compact = serialize_compact({"E": ents})
    fusion = {"E": ents, "compact_context": compact}
    
    pipe = big_brain_answer(fusion, q["question"], BRAIN, q["text"], BRAIN, 1,
        vram_folding=True, vram_limit=6144, eagle_eye=True, eagle_eye_model=EAGLE)
    snap_vram("管线完成", "鹰眼+推理完成")
    
    fold_cleanup([BRAIN, EAGLE, EXTRACTOR])
    time.sleep(2)
    snap_vram("管线结束", "全部卸载")
except Exception as e:
    print(f"VRAM test error: {e}")

# 计算VRAM波动幅度
if len(vram_log) >= 2:
    used_vals = [v["used"] for v in vram_log]
    peak = max(used_vals)
    trough = min(used_vals)
    swing = peak - trough
    md(f"\n**VRAM分析**: 峰值 {peak}MiB | 谷值 {trough}MiB | 波动范围 {swing}MiB ({round(swing/8188*100,1)}% 总显存)")

all_data["experiment_4_vram"] = vram_log

# ===================================================================
# 汇总报告
# ===================================================================
md("\n---\n## 汇总")
md("\n### 实验1: 标准基准")
md(f"- 正确率: {acc_e1}%")
md(f"- 平均耗时: {avg_e1}s")

md("\n### 实验2: 消融")
for ac in ablation_configs:
    delta_acc = round(ac["accuracy"] - ablation_configs[0]["accuracy"], 1) if ablation_configs else 0
    delta_time = round(ac["avg_time"] - ablation_configs[0]["avg_time"], 1) if ablation_configs else 0
    md(f"- {ac['config']} ({ac['desc']}): {ac['accuracy']}% ({delta_acc:+.1f}%), {ac['avg_time']}s ({delta_time:+.1f}s)")

md("\n### 实验3: Baseline")
for bl in baseline_results:
    md(f"- {bl['model']}: {bl['accuracy']}%, {bl['avg_time']}s")

md("\n### 实验4: VRAM")
if vram_log:
    md(f"- 峰值: {max(v['used'] for v in vram_log)}MiB")
    md(f"- 波动: {max(v['used'] for v in vram_log) - min(v['used'] for v in vram_log)}MiB")

md(f"\n\n---\n*报告生成: {time.strftime('%Y-%m-%d %H:%M:%S')}*")

# 保存JSON
with open(json_path, "w", encoding="utf-8") as f:
    json.dump(all_data, f, ensure_ascii=False, indent=2)

print(f"\n报告: {report_path}")
print(f"数据: {json_path}")
print("全部实验完成!")