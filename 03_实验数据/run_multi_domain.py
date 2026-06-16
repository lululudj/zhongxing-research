# -*- coding: utf-8 -*-
"""多领域批跑测试：法律、财报、新闻、学术、小说"""
import sys, os, time, json

sys.path.insert(0, 'E:/zhongxing2')
from zhongxing_agent import *

log = open('E:/zhongxing2/multi_domain_result.txt', 'w', encoding='utf-8')
sys.stdout = log
sys.stderr = log

test_cases = [
    ("小说", (
        "萧炎抬头望向那巨大的黑角域方向，眼中有着一丝凝重。"
        "在黑角域之中，有着不少的强者，其中最为著名的便是韩枫，"
        "此人乃是药老的叛徒弟子，当年偷袭药老导致其灵魂体被迫遁入骨灵冷火之中。"
        "韩枫如今已是斗皇强者，掌控着黑角域最大的势力枫城。\n\n"
        "药老沉声道：\u201c韩枫，我那不肖弟子，当年若非他偷袭，我也不至于落到这般田地。\u201d"
        "萧炎闻言，心中对韩枫的恨意更甚，拳头紧握。"
        "药老是他最尊敬的师父，韩枫对药老的所作所为，他绝不会轻易放过。\n\n"
        "萧战望着远去的萧炎背影，心中百感交集。"
        "他这个儿子，从小便展现出过人的天赋，却又经历了三年废物的屈辱。"
        "如今能重新崛起，全靠自身的坚毅。"
        "萧战身为乌坦城萧家家主，虽然实力不过大斗师级别，但多年来将萧家治理得井井有条。\n\n"
        "萧炎进入迦南学院修炼，在这里遇到了不少强敌。"
        "迦南学院后山有着一座天焚炼气塔，塔底封印着陨落心炎，这是一种异火排名第十四的天地奇物。"
        "萧炎在炼气塔中修炼，不仅实力突飞猛进，更与美杜莎女王产生了纠葛。"
        "美杜莎是蛇人族的女王，拥有极其强大的实力，乃是斗宗级别的强者。\n\n"
        "小医仙是萧炎在魔兽山脉结识的朋友，她天生厄难毒体，"
        "这种特殊体质使得她不修炼也能自动吸收天地毒素提升实力，"
        "但同时也意味着她随时可能被毒素反噬失控。"
        "萧炎曾承诺会帮她控制毒体，这份承诺一直记在心中。"
    ), [
        "药老的叛徒弟子是谁？他做了什么？",
        "萧炎和小医仙是什么关系？小医仙有什么特殊体质？",
        "美杜莎是谁？她的实力等级是什么？",
    ]),
    ("法律合同", (
        "甲方（委托方）：北京智创科技有限公司，法定代表人张三，统一社会信用代码91110108MA01XXXXX，"
        "住所地北京市海淀区中关村软件园A座12层。乙方（受托方）：上海云算信息技术有限公司，法定代表人李四，"
        "统一社会信用代码91310115MA02XXXXX，住所地上海市浦东新区张江高科技园区B栋8层。\n\n"
        "根据《中华人民共和国民法典》第九百一十九条之规定及双方友好协商，就甲方委托乙方进行"
        "「智能数据分析平台」软件开发事宜，达成以下条款：\n"
        "第一条 开发内容：乙方为甲方开发智能数据分析平台V1.0，包含数据采集模块、清洗引擎、"
        "可视化大屏三大子系统。交付物包括完整源代码、技术文档、部署手册及一年期免费维护服务。\n\n"
        "第二条 合同金额：项目总价款为人民币壹佰捌拾万元整（￥1,800,000），分三期支付。"
        "首期于合同签署后5个工作日内支付30%即54万元；二期于中期验收通过后支付40%即72万元；"
        "尾期于最终验收合格后30日内支付30%即54万元。\n\n"
        "第三条 交付期限：乙方应于2025年12月31日前完成全部开发并通过甲方验收。\n\n"
        "第四条 违约责任：任何一方违反合同约定，应向守约方支付合同总金额20%的违约金，"
        "即36万元。因乙方原因逾期交付的，每逾期一日按合同总额千分之三计付违约金，"
        "逾期超过90日的，甲方有权单方解除合同并索赔全部损失。\n\n"
        "第五条 保密条款：双方对合同内容及履行过程中获知的对方技术秘密和商业秘密承担保密义务，"
        "保密期限为合同终止后五年。\n\n"
        "第六条 争议解决：因本合同产生的争议，双方应协商解决；协商不成的，"
        "提交北京仲裁委员会按照其仲裁规则仲裁，仲裁裁决为终局裁决。"
    ), [
        "合同总价款是多少？分几期支付？首期支付多少？",
        "乙方逾期交付的违约金怎么计算？逾期多久甲方可以单方解约？",
        "双方发生争议后，解决方式是什么？去哪里仲裁？",
    ]),
    ("财经财报", (
        "深圳华大智造科技股份有限公司（股票代码：688114）2024年半年度财务报告摘要：\n\n"
        "报告期内，公司实现营业收入为人民币12.87亿元，较上年同期的14.53亿元下降11.42%；"
        "归属于上市公司股东的净利润为人民币-2.13亿元，去年同期为-1.08亿元，"
        "亏损同比扩大97.22%；扣除非经常性损益后的净利润为-2.56亿元。\n"
        "基本每股收益为-0.51元/股。加权平均净资产收益率为-5.82%。\n\n"
        "分业务板块来看，基因测序仪业务实现收入10.24亿元，占总营收79.6%，"
        "同比增长3.7%。实验室自动化业务收入1.86亿元，同比下降45.3%，"
        "主要是由于新冠相关检测需求大幅萎缩。新业务板块收入0.77亿元。\n\n"
        "研发投入方面，报告期内公司研发费用为4.92亿元，同比增长18.6%，"
        "研发费用率为38.2%，较去年同期提高约10个百分点。\n\n"
        "截至报告期末，公司总资产规模为98.6亿元，归属于上市公司股东的净资产为68.4亿元，"
        "资产负债率为30.6%。经营活动产生的现金流量净额为-3.21亿元。"
        "公司现金及等价物余额为15.3亿元，短期借款8.5亿元。\n\n"
        "海外业务方面，公司在亚太、欧洲、美洲三大区域实现收入合计4.73亿元，"
        "占总营收比重提升至36.8%，较去年全年提升4.2个百分点。"
    ), [
        "公司2024上半年营收和净利润各是多少？同比变化如何？",
        "研发费用率和变化趋势说明了什么经营策略？",
        "公司流动性状况如何？现金和短期借款各多少？",
    ]),
    ("政策新闻", (
        "2025年3月19日，国家互联网信息办公室发布《人工智能生成合成内容标识管理办法》，"
        "要求自2025年9月1日起，所有在中国境内向公众提供服务的生成式人工智能产品，"
        "必须对生成合成的文本、图片、音频、视频等内容进行显式或隐式标识。\n\n"
        "管理办法明确，深度合成服务提供者应当在生成内容中添加不低于画面1/16面积的"
        "「AI生成」水印标识（显式标识），同时必须在文件元数据中嵌入包含生成模型信息、"
        "生成时间、服务提供者名称的数字水印（隐式标识），且该标识应具备抗篡改能力。\n\n"
        "对于违反规定的行为，管理办法设置了分级处罚机制：情节较轻的，由网信部门责令限期改正，"
        "给予警告，可以并处1万元以上10万元以下罚款；情节严重的，处10万元以上100万元以下罚款，"
        "可以责令暂停相关业务、停业整顿、吊销相关业务许可证；"
        "构成违反治安管理行为的，依法给予治安管理处罚；构成犯罪的，依法追究刑事责任。\n\n"
        "该办法还对深度合成服务使用者的责任进行了界定：使用者利用生成合成内容从事"
        "造谣、诈骗、诽谤等违法活动的，依法承担相应法律责任。服务提供者发现使用者从事"
        "违法活动的，应当立即停止提供服务，保存有关记录并向有关部门报告。\n\n"
        "业内分析人士指出，该办法是全球范围内首个针对AI生成内容强制标识的专项法规，"
        "将对国内数十家AI大模型厂商产生直接影响。目前已有多家头部厂商表示将积极配合。"
    ), [
        "该办法要求AI生成内容如何标识？有哪些标识方式？",
        "违反规定的处罚措施有哪些层级？最重可以怎么处罚？",
        "服务提供者发现使用者违法活动后，有什么义务？",
    ]),
    ("学术论文", (
        "论文题目：基于注意力机制的多模态语义压缩方法研究\n\n"
        "摘要：针对大语言模型在处理长文本时面临的计算资源消耗过大问题，"
        "本文提出了一种基于多层级注意力机制的语义压缩框架（MLASC）。"
        "该框架通过三个递进层次实现信息压缩：第一层为句法级注意力层，利用轻量级双向GRU网络"
        "对文本进行句法结构感知，剔除冗余修饰成分；第二层为语义级注意力层，"
        "通过跨句注意力机制捕捉实体间的共指关系与事件链条，合并重复语义；"
        "第三层为任务感知层，根据下游问答任务的需求动态调整压缩粒度。\n\n"
        "实验部分，我们在CNN/DailyMail长文本摘要数据集和PubMedQA医学问答数据集上进行了评估。"
        "使用LLaMa-2-7B作为下游推理模型，将原始文本压缩至原始长度的15%-30%作为输入。"
        "实验结果显示，在CNN/DailyMail数据集上，压缩后ROUGE-L得分仅下降2.1个百分点（从43.8降至41.7），"
        "而推理耗时减少了62%；在PubMedQA上，准确率从78.5%微降至76.3%，但GPU显存占用从14.2GB降至4.8GB。"
        "相比传统的抽取式摘要方法，MLASC方法在信息保留率和压缩比两个维度均取得了显著优势。\n\n"
        "消融实验表明，移除语义级注意力层会导致性能下降最为显著（ROUGE-L再降5.3个百分点），"
        "说明跨句语义合并是压缩框架的核心贡献。"
    ), [
        "MLASC框架的三个层次分别是什么？各自有什么作用？",
        "实验结果显示压缩带来了哪些性能变化？推理耗时和显存占用各降低多少？",
        "消融实验中哪个层次对性能影响最大？说明了什么？",
    ]),
]

print("=" * 70)
print("zhongxing 1.6.1 多领域测试")
print(f"共 {len(test_cases)} 个领域：小说、法律、财经、新闻、学术")
print("=" * 70)

config = FALLBACK_CONFIG
results = []

for domain_idx, (domain_name, text, questions) in enumerate(test_cases):
    if domain_idx < 1:  # Skip already completed domains
        continue
    print(f"\n{'='*60}")
    print(f"[{domain_idx+1}/{len(test_cases)}] 领域: {domain_name}")
    print(f"文本:{len(text)}字 | {len(questions)}题")
    print(f"{'='*60}")
    log.flush()
    try:

    start = time.time()

    # Step 1: Schema
    print("\n[1/4] 维度自发现...", flush=True)
    log.flush()
    schema = discover_schema(text, config["schema_model"])
    print(f"  类型: {schema['text_type']} | 实体: {', '.join(schema['entity_types'][:4])}")
    log.flush()

    # Step 2: Extraction
    print(f"\n[2/4] 提取({config['num_extractors']}×1.5b并行)...", flush=True)
    log.flush()
    extractions = run_extractors(text, schema, config["extractor_model"], config["num_extractors"])
    total_ents = sum(len(e["entities"]) for e in extractions)
    if total_ents < 5:
        extractions2 = run_extractors(text, schema, config["extractor_model"], config["num_extractors"])
        total_ents2 = sum(len(e["entities"]) for e in extractions2)
        if total_ents2 > total_ents:
            extractions = extractions2
            print(f"  重跑: {total_ents2} > {total_ents}")
    log.flush()

    # Step 3: RRF
    print("\n[3/4] RRF融合 + NER...", flush=True)
    log.flush()
    fusion = rrf_fuse(extractions, config["schema_model"], len(text))
    if isinstance(fusion["fused_context"], list):
        fusion["fused_context"] = {"E": fusion["fused_context"]}
    gap = entity_gap_check(text, fusion["fused_context"], config["schema_model"])
    if gap["missing"]:
        existing_E = fusion["fused_context"].get("E", [])
        if isinstance(existing_E, list) and isinstance(gap.get("supplement_entities"), list):
            existing_E.extend(gap["supplement_entities"])
            fusion["fused_context"]["E"] = existing_E

    compact_str = serialize_compact(fusion["fused_context"])
    json_str = json.dumps(fusion["fused_context"], ensure_ascii=False)
    compact_ratio = len(text) / max(len(compact_str), 1)
    print(f"  压缩: {len(text)}→{len(compact_str)}字 ({compact_ratio:.1f}:1) | 实体:{len(fusion['fused_context'].get('E',[]))}")
    print(f"  机语:\n{compact_str[:400]}")
    log.flush()

    # Step 4: Brain
    print(f"\n[4/4] 大脑推理({len(questions)}题串行)...", flush=True)
    log.flush()
    qa_results = []
    for i, q in enumerate(questions):
        print(f"  Q{i+1} 推理中...", flush=True)
        log.flush()
        try:
            pipe = big_brain_answer(fusion, q, config["big_brain_model"],
                                    text, config["schema_model"],
                                    config.get("max_feedback_rounds", 2))
            qa_results.append({"q": q, "answer": pipe["answer"], "time": pipe["time"]})
            fb = f", 反馈{pipe['feedback_rounds']}轮" if pipe["feedback_rounds"] > 0 else ""
            print(f"  Q{i+1}({pipe['time']}s{fb}): {pipe['answer'][:120]}")
        except Exception as e:
            qa_results.append({"q": q, "answer": f"ERROR: {e}", "time": 0})
            print(f"  Q{i+1}: ERROR - {e}")
        log.flush()

    elapsed = time.time() - start
    domain_result = {
        "domain": domain_name,
        "text_len": len(text),
        "compact_len": len(compact_str),
        "ratio": round(compact_ratio, 1),
        "time": round(elapsed, 1),
        "qa": qa_results,
    }
    results.append(domain_result)
    print(f"\n  >> {domain_name} 完成: 压缩{compact_ratio:.1f}:1, 耗时{elapsed:.1f}s")

# Summary
print(f"\n\n{'='*70}")
print("多领域测试汇总")
print(f"{'='*70}")
for r in results:
    print(f"\n【{r['domain']}】 文本{r['text_len']}字→机语{r['compact_len']}字 ({r['ratio']}:1) | {r['time']}s")
    for i, qa in enumerate(r['qa']):
        print(f"  Q{i+1}: {qa['q']}")
        print(f"    A: {qa['answer'][:150]}")

print(f"\n{'='*70}")
print("平均压缩比: {:.1f}:1 | 总耗时: {:.1f}s".format(
    sum(r['ratio'] for r in results)/len(results),
    sum(r['time'] for r in results),
))
print("ALL DONE")

log.close()