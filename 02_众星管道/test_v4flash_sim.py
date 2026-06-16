"""
zhongxing + V4-Flash 模拟器 端到端测试
用 Qwen2.5:14B 充当 V4-Flash 替身，模拟 mmap 推理 + 1060 内存约束
验证: 压缩管道 → 轻量模型推理 → 完整回答
"""
import sys, os, json, time, re, urllib.request, urllib.error

OLLAMA = "http://localhost:11434"
BRAIN = "qwen2.5:14b"

# 1060 6GB 模拟: 限制 GPU 层数（模拟只有部分权重能进 GPU）
GPU_LAYERS = os.environ.get("GPU_LAYERS", "20")

# 5 领域测试数据
TESTS = {
    "小说": {
        "context": """萧炎抬头望向那巨大的黑角域方向，眼中有着一丝凝重。
在黑角域之中，有着不少的强者，其中最为著名的便是韩枫，
此人乃是药老的叛徒弟子，当年偷袭药老导致其灵魂体被迫遁入骨灵冷火之中。
韩枫如今已是斗皇强者，掌控着黑角域最大的势力枫城。

药老沉声道："韩枫，我那不肖弟子，当年若非他偷袭，我也不至于落到这般田地。"
萧炎闻言，心中对韩枫的恨意更甚，拳头紧握。
药老是他最尊敬的师父，韩枫对药老的所作所为，他绝不会轻易放过。

小医仙是萧炎在魔兽山脉结识的朋友，她天生厄难毒体，
这种特殊体质使得她不修炼也能自动吸收天地毒素提升实力，
但同时也意味着她随时可能被毒素反噬失控。
萧炎曾承诺会帮她控制毒体，这份承诺一直记在心中。

美杜莎是蛇人族的女王，拥有极其强大的实力，乃是斗宗级别的强者。
萧炎在迦南学院修炼时与美杜莎产生了纠葛。""",
        "questions": [
            "药老的叛徒弟子是谁？他做了什么？",
            "小医仙有什么特殊体质？这种体质的危险是什么？",
            "美杜莎是谁？实力等级是什么？",
        ]
    },
    "法律合同": {
        "context": """甲方（出租方）：北京华远房地产开发有限公司
乙方（承租方）：深圳市创新科技有限公司

第一条 租赁标的
甲方同意将其合法拥有的位于北京市海淀区中关村大街108号创新大厦A座15层1501-1508室的办公用房出租给乙方使用，租赁面积共计1200平方米。

第二条 租赁期限
租赁期限为五年，自2026年1月1日起至2030年12月31日止。
其中装修免租期为2026年1月1日至2026年2月28日，免租期内乙方无需支付租金，但需承担物业管理费及水电费。

第三条 租金及支付方式
月租金为人民币180,000元（大写：壹拾捌万元整），含税。
租金按季度支付，每季度首月5日前支付当季度租金540,000元。
乙方逾期支付租金的，每逾期一日，应按逾期金额的千分之五向甲方支付违约金。

第四条 违约责任
任何一方违反本合同约定，应向守约方支付相当于三个月租金的违约金，即人民币540,000元。
如因乙方原因导致合同提前解除，乙方已支付的租赁保证金不予退还。""",
        "questions": [
            "租赁面积是多少？",
            "月租金和季付金额分别是多少？",
            "乙方逾期支付租金的违约金标准是什么？",
        ]
    },
    "财经财报": {
        "context": """华为技术有限公司2025年度财务报告摘要

一、经营业绩
2025年，华为实现销售收入人民币7,250亿元，同比增长12.8%。
其中，ICT基础设施业务收入3,520亿元，终端业务收入2,380亿元，
云计算业务收入850亿元，数字能源业务收入500亿元。

二、盈利情况
2025年净利润为人民币685亿元，同比增长18.5%。
净利润率为9.4%，较上年提升0.5个百分点。
营业利润率为12.1%，较上年提升1.2个百分点。

三、研发投入
2025年研发费用为人民币1,450亿元，占销售收入的20.0%。
近十年累计研发投入超过人民币12,000亿元。
截至2025年底，华为在全球拥有有效授权专利超过14万件。

四、现金流
经营活动现金流净额为人民币920亿元，同比增长15.2%。
现金及短期投资余额为人民币2,380亿元，资产负债率降至58.2%。""",
        "questions": [
            "2025年华为销售收入和净利润分别是多少？",
            "研发费用占销售收入的比例是多少？",
            "经营活动现金流净额是多少？",
        ]
    },
    "政策新闻": {
        "context": """国务院办公厅关于促进人工智能产业高质量发展的指导意见

一、总体要求
以习近平新时代中国特色社会主义思想为指导，坚持创新驱动、应用牵引、安全可控的原则，
加快构建人工智能产业生态体系。到2028年，人工智能核心产业规模超过1万亿元，
带动相关产业规模超过10万亿元。

二、重点任务
（一）加强基础理论研究。支持高校和科研院所开展人工智能基础理论和前沿技术研究，
重点突破大模型架构、强化学习、多模态感知等关键技术。

（二）推动产业应用落地。在制造、医疗、教育、交通、金融等重点领域，
推动人工智能深度应用，培育一批具有国际竞争力的龙头企业。

（三）完善标准体系。加快制定人工智能领域国家标准和行业标准，
建立健全人工智能安全评估和风险监管体系。

三、保障措施
加大财政资金支持力度，设立人工智能产业发展专项基金，规模不低于500亿元。
鼓励社会资本参与，支持符合条件的AI企业在科创板上市融资。""",
        "questions": [
            "到2028年人工智能核心产业规模目标是多少？",
            "重点任务包括哪几个方面？",
            "人工智能产业发展专项基金规模不低于多少？",
        ]
    },
    "学术论文": {
        "context": """基于多模态注意力机制的遥感图像语义分割研究

摘要：针对遥感图像中目标尺度差异大、背景复杂、小目标分割精度低的问题，
本文提出一种基于多模态注意力机制的遥感图像语义分割网络（MMA-Net）。
该网络包含三个核心模块：多尺度特征提取模块（MFE）、跨模态注意力融合模块（CAF）
和边缘感知解码器（EAD）。在ISPRS Vaihingen和Potsdam两个公开数据集上的实验表明，
MMA-Net在整体精度（OA）上达到91.2%，平均交并比（mIoU）达到78.5%，
较基线模型DeepLabV3+分别提升3.8%和5.2%。消融实验验证了各模块的有效性，
其中CAF模块对精度提升贡献最大，单独使用可使mIoU提升3.1%。

实验设置：所有实验在NVIDIA RTX 3090 GPU上进行，使用PyTorch框架实现。
训练采用AdamW优化器，初始学习率为1e-4，batch size为8，共训练200个epoch。""",
        "questions": [
            "论文提出的网络叫什么？包含哪些核心模块？",
            "整体精度和平均交并比分别是多少？",
            "哪个模块对精度提升贡献最大？",
        ]
    }
}

def ollama_chat(model, content, system="", stream=False, timeout=300, num_gpu=None):
    """调用 Ollama chat API"""
    msgs = []
    if system:
        msgs.append({"role": "system", "content": system})
    msgs.append({"role": "user", "content": content})
    
    options = {"temperature": 0.1}
    if num_gpu is not None:
        options["num_gpu"] = num_gpu
    
    data = json.dumps({
        "model": model,
        "messages": msgs,
        "stream": stream,
        "options": options,
    }).encode("utf-8")
    
    req = urllib.request.Request(
        f"{OLLAMA}/api/chat",
        data=data,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            resp = json.loads(r.read().decode("utf-8"))
            return resp["message"]["content"]
    except Exception as e:
        return f"ERROR: {e}"

def ollama_generate(model, prompt, timeout=300, num_gpu=None):
    """使用 generate API（更简单）"""
    options = {"temperature": 0.1}
    if num_gpu is not None:
        options["num_gpu"] = num_gpu
    
    data = json.dumps({
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": options,
    }).encode("utf-8")
    
    req = urllib.request.Request(
        f"{OLLAMA}/api/generate",
        data=data,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            resp = json.loads(r.read().decode("utf-8"))
            return resp["response"]
    except Exception as e:
        return f"ERROR: {e}"

# ---------- 导入 zhongxing 压缩管道 ----------
sys.path.insert(0, os.path.dirname(__file__))
from zhongxing_agent import (
    call_ollama, discover_schema, run_extractors, rrf_fuse,
    serialize_compact, entity_gap_check, cooccurrence_scan,
    big_brain_answer, FALLBACK_CONFIG
)

def compress_pipeline(text, config):
    """完整压缩管道"""
    # 维度自发现
    schema = discover_schema(text, config["schema_model"])
    
    # 并行提取
    extractions = run_extractors(text, schema, config["extractor_model"], config["num_extractors"])
    
    # RRF 融合
    fusion = rrf_fuse(extractions, config["schema_model"], len(text))
    if isinstance(fusion["fused_context"], list):
        fusion["fused_context"] = {"E": fusion["fused_context"]}
    
    # 补漏 + 共现
    gap = entity_gap_check(text, fusion["fused_context"], config["schema_model"])
    if gap["missing"]:
        existing = fusion["fused_context"].get("E", [])
        if isinstance(existing, list):
            existing.extend(gap.get("supplements", []))
    cooccurrence_scan(text, fusion["fused_context"])
    
    return fusion, schema

# ---------- 主测试 ----------
def main():
    print("=" * 70)
    print("zhongxing + V4-Flash 模拟器 端到端测试")
    print(f"大脑: {BRAIN} (替身V4-Flash) | GPU层: {GPU_LAYERS} (模拟1060)")
    print("=" * 70)
    
    config = dict(FALLBACK_CONFIG)
    config["big_brain_model"] = BRAIN
    
    # 检查 Ollama
    try:
        req = urllib.request.Request(f"{OLLAMA}/api/tags")
        with urllib.request.urlopen(req, timeout=5) as r:
            models = [m["name"] for m in json.loads(r.read()).get("models", [])]
        print(f"Ollama: {', '.join(models)}")
    except Exception as e:
        print(f"Ollama 连接失败: {e}")
        sys.exit(1)
    
    results = {}
    
    for domain, data in TESTS.items():
        context = data["context"]
        questions = data["questions"]
        
        print(f"\n{'='*70}")
        print(f"  领域: {domain} | 上下文: {len(context)}字 | {len(questions)}题")
        print(f"{'='*70}")
        
        # --- 模式A: 直接推理 (无压缩) ---
        print(f"\n  [A] 直接推理 (14B, 无压缩, 完整上下文)...")
        direct_answers = []
        direct_start = time.time()
        for qi, q in enumerate(questions):
            prompt = f"根据以下上下文回答问题：\n\n{context}\n\n问题：{q}"
            t0 = time.time()
            ans = ollama_chat(BRAIN, prompt, timeout=300)
            t = time.time() - t0
            direct_answers.append({"q": q, "a": ans[:300], "t": round(t, 1)})
            print(f"    Q{qi+1} ({t:.1f}s): {ans[:100]}...")
        direct_total = time.time() - direct_start
        
        # --- 模式B: 压缩管道推理 ---
        print(f"\n  [B] zhongxing 压缩管道 (1.5B×3 + 3B + 14B)...")
        pip_start = time.time()
        
        # 压缩
        try:
            fusion, schema = compress_pipeline(context, config)
            compact = serialize_compact(fusion["fused_context"])
            ratio = len(context) / max(len(compact), 1)
            print(f"    压缩: {len(context)}→{len(compact)}字 ({ratio:.1f}:1)")
            print(f"    机语预览: {compact[:200]}...")
        except Exception as e:
            print(f"    压缩失败: {e}")
            compact = context
            ratio = 1.0
        
        # 推理
        pipe_answers = []
        for qi, q in enumerate(questions):
            t0 = time.time()
            ans = big_brain_answer(fusion, q, BRAIN, context, config["schema_model"])
            t = time.time() - t0
            pipe_answers.append({"q": q, "a": ans.get("answer", "")[:300], "t": round(t, 1)})
            fb = f" (反馈{ans.get('feedback_rounds',0)}轮)" if ans.get("feedback_rounds", 0) > 0 else ""
            print(f"    Q{qi+1} ({t:.1f}s{fb}): {ans.get('answer', '')[:100]}...")
        pipe_total = time.time() - pip_start
        
        results[domain] = {
            "direct": direct_answers,
            "pipe": pipe_answers,
            "direct_total": round(direct_total, 1),
            "pipe_total": round(pipe_total, 1),
            "compression_ratio": round(ratio, 1),
            "original_len": len(context),
            "compressed_len": len(compact),
        }
    
    # --- 汇总 ---
    print(f"\n{'='*70}")
    print("  测试汇总")
    print(f"{'='*70}")
    print(f"{'领域':<10} {'原始字':<8} {'压缩字':<8} {'压缩比':<8} {'直接耗时':<10} {'管道耗时':<10}")
    print("-" * 60)
    for domain, r in results.items():
        print(f"{domain:<10} {r['original_len']:<8} {r['compressed_len']:<8} {r['compression_ratio']:<8.1f} "
              f"{r['direct_total']:<10.1f} {r['pipe_total']:<10.1f}")
    
    # 保存结果
    out = {
        "config": {"brain": BRAIN, "gpu_layers": GPU_LAYERS, "platform": "V4-Flash-simulator"},
        "results": results,
    }
    with open("e2e_v4flash_sim.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"\n结果保存: e2e_v4flash_sim.json")

if __name__ == "__main__":
    main()