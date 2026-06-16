"""速度验证: 5题快速对比 v1.6.3 vs v1.7.0"""
import sys,os,time
sys.path.insert(0,os.path.dirname(__file__))
from zhongxing_agent import *

QS = [
    ("牛顿第二定律指出，物体的加速度与作用力成正比，与质量成反比，公式为F=ma。","牛顿第二定律的公式是什么？"),
    ("线粒体是真核细胞中的一种细胞器，被称为细胞的能量工厂，通过氧化磷酸化产生ATP。","线粒体被称为什么？"),
    ("法国大革命于1789年爆发，1793年路易十六被送上断头台。","法国大革命爆发于哪一年？"),
    ("中华人民共和国民法典共7编1260条，于2021年1月1日起施行。","民法典共多少编？"),
    ("青霉素由亚历山大·弗莱明于1928年发现。","青霉素谁发现的？哪年？"),
]

SC = {"text_type":"通用","entity_types":["人物","机构","概念","事物"],
      "attr_types":["属性","数值","时间"],"rel_types":["关系","因果"]}
EX = "qwen2.5:1.5b"
BR = "qwen2.5:3b"
EG = "qwen2.5:3b"

# 先清理
fold_cleanup([EX, BR, EG])
time.sleep(2)

print("="*50)
print("众星 v1.7.0 速度测试 (5题)")
print("="*50)

total = 0
for i, (text, question) in enumerate(QS):
    t0 = time.time()
    ext = universal_extract(text, 0, SC, EX, question=question)
    ents = ext.get("entities", [])
    compact = serialize_compact({"E": ents})
    fusion = {"E": ents, "compact_context": compact}
    pipe = big_brain_answer(fusion, question, BR, text, BR, 1,
                            vram_folding=True, vram_limit=6144,
                            eagle_eye=True, eagle_eye_model=EG)
    t = round(time.time() - t0, 1)
    total += t
    ee = pipe.get("eagle_eye", {})
    ans = pipe["answer"][:80].replace("\n", " ")
    print(f"[{i+1}] {t}s | eagle={ee.get('verdict','?')} | {ans}")

avg = round(total / len(QS), 1)
print(f"\nAVG: {avg}s/题 (之前 8.7s)")
print(f"加速: {round((1 - avg/8.7)*100)}%")

# 最后清理
fold_cleanup([EX, BR, EG])
print("done")