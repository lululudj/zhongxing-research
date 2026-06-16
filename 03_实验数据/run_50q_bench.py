"""50题跨领域基准测试 — 文件输出版本，不依赖终端"""
import sys, os, time, json

sys.path.insert(0, os.path.dirname(__file__))
from zhongxing_agent import (
    discover_schema, run_extractors, rrf_fuse, entity_gap_check,
    cooccurrence_scan, big_brain_answer, serialize_compact,
    FALLBACK_CONFIG, fold_cleanup, nvidia_smi
)

LOG_FILE = os.path.join(os.path.dirname(__file__), "50q_benchmark_log.txt")
REPORT_FILE = os.path.join(os.path.dirname(__file__), "50q_benchmark_report.json")

def log(msg):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(msg + "\n")
    print(msg, flush=True)

# ===== 50题 =====
TEST_CASES = [
    ("科技", "2022年11月，OpenAI发布了ChatGPT，基于GPT-3.5架构，这是一个拥有1750亿参数的大语言模型。ChatGPT发布后两个月用户突破1亿。", "ChatGPT基于什么架构？有多少参数？", ["GPT-3.5", "1750亿"]),
    ("科技", "台积电是全球最大半导体代工厂，总部位于台湾新竹。2023年台积电3纳米制程量产，主要客户包括苹果、英伟达和AMD。全球芯片代工市场份额超过55%。", "台积电的3纳米制程主要客户有哪些？", ["苹果", "英伟达", "AMD"]),
    ("科技", "量子计算利用量子比特叠加态和纠缠态计算。2019年谷歌实现量子霸权，Sycamore处理器200秒完成传统超算1万年的计算。2023年IBM发布1121量子比特的Condor处理器。", "谷歌实现量子霸权的处理器叫什么？用了多少秒？", ["Sycamore", "200"]),
    ("科技", "Linux操作系统由芬兰人林纳斯·托瓦兹于1991年创建，采用GPL许可证。全球超96%顶级超算运行Linux，Android也基于Linux内核。", "Linux是谁创建的？采用什么许可证？", ["林纳斯", "GPL"]),
    ("科技", "5G通信由3GPP标准化，中国华为在5G标准必要专利中占比约20%，全球第一。5G理论峰值速率20Gbps，延迟低至1毫秒。", "华为在5G标准必要专利中占比多少？", ["20"]),
    ("历史", "秦始皇嬴政于公元前221年统一六国，建立中国第一个中央集权封建王朝。推行书同文、车同轨、统一度量衡，修建万里长城抵御匈奴。", "秦始皇统一六国是哪一年？推行了什么政策？", ["公元前221", "书同文", "车同轨"]),
    ("历史", "法国大革命爆发于1789年，巴士底狱被攻占。革命口号自由平等博爱。1793年国王路易十六被送上断头台。", "法国大革命哪一年爆发？路易十六的结局？", ["1789", "断头台"]),
    ("历史", "二战1939年德国入侵波兰开始，1945年日本投降结束。同盟国包括美国、苏联、英国、中国。诺曼底登陆1944年6月6日。", "诺曼底登陆是哪一天？", ["1944", "6月"]),
    ("历史", "丝绸之路始于西汉张骞出使西域，连接中国与地中海。运输丝绸、瓷器、香料，传播佛教、伊斯兰教。", "丝绸之路始于什么时期？谁出使西域？", ["西汉", "张骞"]),
    ("历史", "工业革命始于18世纪英国，詹姆斯·瓦特1769年改进蒸汽机。导致工厂制度兴起和城市化加速。", "谁改良了蒸汽机？哪一年？", ["瓦特", "1769"]),
    ("法律", "中国民法典2021年1月1日施行，共7编1260条，包括总则、物权、合同、人格权、婚姻家庭、继承、侵权责任。", "民法典共几编多少条？", ["7", "1260"]),
    ("法律", "刑法第二十条规定正当防卫。为保护国家、公共利益、本人或他人权利免受正在进行的不法侵害，对不法侵害人造成损害的，不负刑事责任。", "正当防卫规定在刑法第几条？", ["二十"]),
    ("法律", "著作权法保护作者权益。著作权保护期限为作者终生及死后五十年。著作人身权包括发表权、署名权、修改权、保护作品完整权。", "著作权保护期限是作者死后多少年？", ["五十"]),
    ("法律", "公司法规定有限责任公司由五十个以下股东出资设立。注册资本为全体股东认缴的出资额。", "有限责任公司股东人数上限是多少？", ["五十"]),
    ("法律", "劳动合同法规定用人单位自用工之日起与劳动者建立劳动关系。未同时订立书面劳动合同的，应自用工之日起一个月内订立。", "用人单位应在用工之日起多久内签书面劳动合同？", ["一个月"]),
    ("医学", "新冠病毒正式名称为SARS-CoV-2，2019年底在武汉首次发现。mRNA疫苗由辉瑞和莫德纳开发，有效率超90%。", "新冠病毒正式名称？mRNA疫苗由哪两家公司开发？", ["SARS-CoV-2", "辉瑞", "莫德纳"]),
    ("医学", "2型糖尿病占所有糖尿病90%以上，特征是胰岛素抵抗和胰岛素分泌相对不足。二甲双胍是一线口服降糖药。", "2型糖尿病的一线口服药是什么？", ["二甲双胍"]),
    ("医学", "青霉素由亚历山大·弗莱明1928年发现，是第一个抗生素。通过抑制细菌细胞壁合成杀菌，对革兰氏阳性菌特有效。", "青霉素谁发现的？哪一年？", ["弗莱明", "1928"]),
    ("医学", "高血压诊断标准收缩压>140mmHg或舒张压>90mmHg。长期高血压是心脑血管疾病主要危险因素。", "高血压诊断标准收缩压是多少？", ["140"]),
    ("医学", "DNA双螺旋结构由沃森和克里克1953年发现。DNA四种碱基：A腺嘌呤、T胸腺嘧啶、G鸟嘌呤、C胞嘧啶。A与T配对，G与C配对。", "DNA双螺旋哪一年发现？由谁发现？", ["1953", "沃森", "克里克"]),
    ("财经", "比特币由中本聪2009年创建，总量上限2100万枚，采用工作量证明共识。2024年1月SEC批准首批比特币现货ETF。", "比特币总量上限多少？谁创建的？", ["2100", "中本聪"]),
    ("财经", "通货膨胀指物价持续上涨。各国央行通常将通胀目标设定在2%左右。美联储通过调整联邦基金利率控制通胀。", "各国央行通胀目标通常设定在多少？", ["2"]),
    ("财经", "道琼斯工业平均指数包含30家美国大型上市公司。纳斯达克以科技股为主。", "道琼斯工业平均指数包含多少家公司？", ["30"]),
    ("财经", "复利公式FV=PV×(1+r)^n，其中r为利率，n为期数。", "复利公式中r代表什么？", ["利率"]),
    ("财经", "中国2023年GDP约126万亿元人民币，全球第二。美国约27万亿美元全球第一。", "中国2023年GDP约多少万亿元？", ["126"]),
    ("地理", "珠穆朗玛峰位于中国与尼泊尔边境，海拔8848.86米，地球最高峰。2020年中尼联合发布最新测量高度。", "珠穆朗玛峰最新测量高度是多少？", ["8848"]),
    ("地理", "亚马逊雨林位于南美洲，覆盖巴西、秘鲁、哥伦比亚等九个国家，占全球热带雨林面积一半。", "亚马逊雨林覆盖几个国家？", ["九"]),
    ("地理", "撒哈拉沙漠是世界最大热沙漠，位于非洲北部，面积约940万平方公里。年降水量不足25毫米。", "撒哈拉沙漠面积约多少万平方公里？", ["940"]),
    ("地理", "太平洋是世界最大海洋，面积约1.65亿平方公里。马里亚纳海沟最深处挑战者深渊约11034米。", "马里亚纳海沟最深处约多少米？", ["11034"]),
    ("地理", "长江亚洲第一长河，全长约6300公里，发源于青藏高原唐古拉山脉，流经11个省区市，注入东海。", "长江全长约多少公里？发源于哪里？", ["6300", "唐古拉"]),
    ("体育", "现代奥运会由顾拜旦1896年复兴，每四年举办一次。2024年巴黎奥运会是第33届。", "现代奥运会由谁复兴？每几年举办一次？", ["顾拜旦", "四年"]),
    ("体育", "巴西队获5次世界杯冠军，是夺冠次数最多的国家。2022年卡塔尔世界杯阿根廷夺冠。", "巴西队获得过几次世界杯冠军？", ["5"]),
    ("体育", "迈克尔·乔丹带领芝加哥公牛获6次NBA总冠军。勒布朗·詹姆斯是现役得分王。", "乔丹带领公牛队获几次总冠军？", ["6"]),
    ("体育", "网球四大满贯：澳网、法网、温网、美网。德约科维奇是获大满贯单打冠军最多的男子选手。", "网球四大满贯包括哪四个赛事？", ["澳网", "法网", "温网", "美网"]),
    ("体育", "马拉松全程42.195公里，源于1908年伦敦奥运会。基普乔格2022年柏林马拉松跑出2小时01分09秒。", "马拉松全程距离多少公里？", ["42.195"]),
    ("文学", "《红楼梦》清代曹雪芹创作，以贾宝玉、林黛玉、薛宝钗爱情悲剧为主线，描写贾史王薛四大家族兴衰。", "《红楼梦》作者是谁？写了哪四大家族？", ["曹雪芹", "贾", "史", "王", "薛"]),
    ("文学", "鲁迅原名周树人，中国现代文学奠基人。1918年发表《狂人日记》，是中国第一篇白话短篇小说。", "鲁迅原名是什么？《狂人日记》哪年发表？", ["周树人", "1918"]),
    ("文学", "莎士比亚四大悲剧：《哈姆雷特》《奥赛罗》《李尔王》《麦克白》。", "莎士比亚四大悲剧包括哪四部？", ["哈姆雷特", "奥赛罗", "李尔王", "麦克白"]),
    ("文学", "《百年孤独》哥伦比亚作家加西亚·马尔克斯著，1967年出版，讲述布恩迪亚家族七代人故事。", "《百年孤独》作者是谁？哪年出版？", ["马尔克斯", "1967"]),
    ("文学", "李白被称为诗仙，杜甫被称为诗圣。李白豪放飘逸，杜甫沉郁顿挫。", "李白和杜甫分别被称为什么？", ["诗仙", "诗圣"]),
    ("生物", "达尔文1859年出版《物种起源》，提出自然选择进化论。适者生存，所有物种来自共同祖先。", "达尔文哪年出版《物种起源》？", ["1859"]),
    ("生物", "真核细胞有细胞核，包含线粒体、内质网、高尔基体等细胞器。线粒体是细胞的能量工厂。", "真核细胞中哪种细胞器是能量工厂？", ["线粒体"]),
    ("生物", "基因编辑技术CRISPR-Cas9由张锋和沙尔庞捷等人开发，2020年获诺贝尔化学奖。", "CRISPR-Cas9获了什么诺贝尔奖？", ["化学"]),
    ("生物", "光合作用发生在叶绿体中，将光能转化为化学能。方程：6CO2+6H2O→C6H12O6+6O2。", "光合作用发生在什么细胞器中？", ["叶绿体"]),
    ("生物", "人类基因组由约30亿碱基对组成，约2万蛋白质编码基因。人类基因组计划2003年完成。", "人类基因组计划哪年完成？", ["2003"]),
    ("物理", "爱因斯坦1905年提出狭义相对论，核心公式E=mc²。1915年提出广义相对论。", "狭义相对论核心公式？哪年提出？", ["E=mc", "1905"]),
    ("物理", "海森堡不确定性原理：不可能同时精确测量粒子位置和动量。薛定谔方程描述量子态演化。", "不确定性原理谁提出的？", ["海森堡"]),
    ("物理", "黑洞引力极强，连光都无法逃脱。2019年事件视界望远镜拍摄首张黑洞照片，拍摄M87星系中心。", "首张黑洞照片哪年拍摄？拍摄哪个星系？", ["2019", "M87"]),
    ("物理", "牛顿第二定律F=ma。牛顿1687年出版《自然哲学的数学原理》。", "牛顿第二定律公式是什么？", ["F=ma"]),
    ("物理", "可见光波长范围约380纳米到780纳米。红光波长最长，紫光最短。", "可见光波长范围约多少纳米？", ["380", "780"]),
]

config = FALLBACK_CONFIG.copy()
config["big_brain_model"] = "qwen2.5:3b"  # 3B大脑，快速验证
config["extractor_model"] = "qwen2.5:1.5b"
config["schema_model"] = "qwen2.5:3b"
config["eagle_eye_model"] = "qwen2.5:3b"  # 鹰眼用3B但大脑也用3B时，用不同实例

def score_answer(answer, keywords):
    hit = sum(1 for kw in keywords if kw.lower() in answer.lower())
    return hit, len(keywords), hit == len(keywords)

log("=" * 70)
log("50题跨领域基准测试 (zhongxing 1.6.3 + 鹰眼红笔模式)")
log("=" * 70)
used, free, total = nvidia_smi()
if used:
    log(f"GPU: {used}/{total} MiB ({free} MiB free)")
log(f"领域: 科技/历史/法律/医学/财经/地理/体育/文学/生物/物理 各5题")
log(f"总题数: {len(TEST_CASES)}")
log("")

results = []
domain_stats = {}
total_start = time.time()

for idx, (domain, text, question, keywords) in enumerate(TEST_CASES):
    start = time.time()
    r = {"idx": idx, "domain": domain, "question": question, "keywords": keywords}
    
    try:
        # Layer 0: 维度自发现
        schema = discover_schema(text, config["schema_model"])
        
        # Layer 1: 提取
        extractions = run_extractors(text, schema, config["extractor_model"], config["num_extractors"])
        
        # Layer 2: RRF融合
        fusion = rrf_fuse(extractions, config["schema_model"], len(text))
        if isinstance(fusion["fused_context"], list):
            fusion["fused_context"] = {"E": fusion["fused_context"]}
        
        gap = entity_gap_check(text, fusion["fused_context"], config["schema_model"])
        if gap["missing"]:
            existing_E = fusion["fused_context"].get("E", [])
            if isinstance(existing_E, list):
                existing_E.extend(gap.get("supplements", []))
        cooccurrence_scan(text, fusion["fused_context"])
        fusion["compact_context"] = serialize_compact(fusion["fused_context"])
        
        r["extract_time"] = round(time.time() - start, 1)
        r["entity_count"] = len(fusion["fused_context"].get("E", []))
        
        # Layer 3: 大脑推理 + 鹰眼
        brain_start = time.time()
        pipe = big_brain_answer(
            fusion, question, config["big_brain_model"],
            text, config["schema_model"],
            config.get("max_feedback_rounds", 2),
            vram_folding=True, vram_limit=6144,
            eagle_eye=True, eagle_eye_model="qwen2.5:3b"
        )
        r["brain_time"] = round(time.time() - brain_start, 1)
        r["total_time"] = round(time.time() - start, 1)
        r["answer"] = pipe["answer"]
        r["feedback_rounds"] = pipe["feedback_rounds"]
        
        ee = pipe.get("eagle_eye")
        if ee:
            r["eagle_verdict"] = ee["verdict"]
            retry = pipe.get("eagle_retry")
            if retry:
                r["eagle_retry_new"] = retry.get("new_entities", 0)
        else:
            r["eagle_verdict"] = "N/A"
        
        hit, total_kw, perfect = score_answer(pipe["answer"], keywords)
        r["keywords_hit"] = hit
        r["keywords_total"] = total_kw
        r["correct"] = perfect
        
    except Exception as e:
        r["error"] = str(e)
        r["total_time"] = round(time.time() - start, 1)
        r["correct"] = False
        r["answer"] = f"ERROR: {e}"
    
    # 卸载14B
    try:
        fold_cleanup([config["big_brain_model"]])
    except:
        pass
    time.sleep(1)
    
    results.append(r)
    
    status = "OK" if r.get("correct") else ("X" if not r.get("error") else "ERR")
    ee = ""
    if r.get("eagle_verdict") == "NEED_REVIEW":
        ee = f" [红圈+{r.get('eagle_retry_new', 0)}实体]"
    log(f"[{idx+1:2d}/50] {domain} | {status} {r['total_time']}s {r.get('keywords_hit',0)}/{r.get('keywords_total',0)}{ee} => {r.get('answer','?')[:80]}")
    
    if domain not in domain_stats:
        domain_stats[domain] = {"correct": 0, "total": 0, "times": [], "hits": 0, "total_kw": 0}
    ds = domain_stats[domain]
    ds["total"] += 1
    if r.get("correct"):
        ds["correct"] += 1
    ds["times"].append(r["total_time"])
    ds["hits"] += r.get("keywords_hit", 0)
    ds["total_kw"] += r.get("keywords_total", 0)
    
    # 每10题保存中间报告
    if (idx + 1) % 10 == 0:
        mid_report = {
            "progress": f"{idx+1}/{len(TEST_CASES)}",
            "results": [{
                "idx": r2["idx"]+1, "domain": r2["domain"], "question": r2["question"],
                "answer": r2.get("answer","")[:100], "correct": r2.get("correct",False),
                "total_time": r2["total_time"]
            } for r2 in results]
        }
        mid_path = os.path.join(os.path.dirname(__file__), f"50q_progress_{idx+1}.json")
        with open(mid_path, "w", encoding="utf-8") as f:
            json.dump(mid_report, f, ensure_ascii=False, indent=2)
        log(f"  [进度保存] {idx+1}/50")

total_time = round(time.time() - total_start, 1)
total_correct = sum(1 for r in results if r.get("correct"))
total_hits = sum(r.get("keywords_hit", 0) for r in results)
total_kw = sum(r.get("keywords_total", 0) for r in results)
times = [r["total_time"] for r in results]
avg_time = round(sum(times)/len(times), 1) if times else 0
eagle_reviews = sum(1 for r in results if r.get("eagle_verdict") == "NEED_REVIEW")
eagle_corrects = sum(1 for r in results if r.get("eagle_verdict") == "CORRECT")

log("\n" + "=" * 70)
log("              50题跨领域基准测试报告")
log("=" * 70)
log(f"  总题数: {len(TEST_CASES)}")
log(f"  完全正确: {total_correct}/{len(TEST_CASES)} ({total_correct/len(TEST_CASES)*100:.1f}%)")
log(f"  关键词命中率: {total_hits}/{total_kw} ({total_hits/total_kw*100:.1f}%)")
log(f"  平均耗时: {avg_time}s/题")
log(f"  总耗时: {total_time}s ({total_time/60:.1f}min)")
log(f"  最快: {min(times)}s | 最慢: {max(times)}s")
log(f"  鹰眼放行: {eagle_corrects} | 红圈: {eagle_reviews}")

log(f"\n{'领域':<8} {'正确率':<10} {'平均耗时':<10} {'关键词命中':<12}")
log("-" * 45)
for domain in sorted(domain_stats.keys()):
    ds = domain_stats[domain]
    acc = f"{ds['correct']}/{ds['total']} ({ds['correct']/ds['total']*100:.0f}%)"
    avg = f"{sum(ds['times'])/len(ds['times']):.1f}s"
    kw = f"{ds['hits']}/{ds['total_kw']} ({ds['hits']/ds['total_kw']*100:.0f}%)"
    log(f"{domain:<8} {acc:<10} {avg:<10} {kw:<12}")

# 保存JSON报告
report = {
    "test_time": time.strftime("%Y-%m-%d %H:%M:%S"),
    "summary": {
        "total": len(TEST_CASES),
        "correct": total_correct,
        "accuracy": round(total_correct/len(TEST_CASES)*100, 1),
        "keyword_hit_rate": round(total_hits/total_kw*100, 1),
        "avg_time": avg_time,
        "total_time": total_time,
        "min_time": min(times),
        "max_time": max(times),
        "eagle_reviews": eagle_reviews,
        "eagle_corrects": eagle_corrects
    },
    "details": [{
        "idx": r["idx"]+1, "domain": r["domain"], "question": r["question"],
        "answer": r.get("answer",""), "correct": r.get("correct",False),
        "keywords_hit": f"{r.get('keywords_hit',0)}/{r.get('keywords_total',0)}",
        "total_time": r["total_time"], "eagle_verdict": r.get("eagle_verdict","N/A"),
        "error": r.get("error","")
    } for r in results]
}
with open(REPORT_FILE, "w", encoding="utf-8") as f:
    json.dump(report, f, ensure_ascii=False, indent=2)

log(f"\n报告已保存: {REPORT_FILE}")
log(f"日志已保存: {LOG_FILE}")