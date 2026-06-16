"""消融实验 - 双配置版 (no_eagle + no_compact)"""
import sys,os,time,json,traceback
sys.path.insert(0,os.path.dirname(__file__))
from zhongxing_agent import *
import requests
Z_KEY="8314b6afbe96464285305357384eab38.nmeOEbGAwESwihzk"
def judge(q,t,a):
    try:
        r=requests.post("https://open.bigmodel.cn/api/paas/v4/chat/completions",
            json={"model":"glm-4-flash","messages":[{"role":"user","content":f"原文:{t}\n问题:{q}\n答案:{a}\n只输出CORRECT或INCORRECT"}],"max_tokens":50,"temperature":0},
            headers={"Authorization":f"Bearer {Z_KEY}"},timeout=60)
        return "CORRECT" in r.json()["choices"][0]["message"]["content"]
    except: return False
OUT=os.path.join(os.path.dirname(__file__),"experiment_results"); os.makedirs(OUT,exist_ok=True)
EX="qwen2.5:1.5b"; BR="qwen2.5:3b"; EG="qwen2.5:3b"
SC={"text_type":"通用","entity_types":["人物","机构","概念","事物"],"attr_types":["属性","数值","时间"],"rel_types":["关系","因果"]}
QS=[{"id":"MMLU-1","t":"牛顿第二定律指出，物体的加速度与作用力成正比，与质量成反比，公式为F=ma。","q":"牛顿第二定律的公式是什么？A)F=ma B)E=mc^2 C)PV=nRT D)v=at"},
    {"id":"MMLU-2","t":"线粒体是真核细胞中的一种细胞器，被称为细胞的能量工厂，通过氧化磷酸化产生ATP。","q":"线粒体在真核细胞中被称为什么？A)能量工厂 B)核糖体 C)内质网"},
    {"id":"MMLU-3","t":"法国大革命于1789年爆发，1793年路易十六被送上断头台。","q":"法国大革命爆发于哪一年？A)1776年 B)1789年 C)1793年 D)1804年"},
    {"id":"MMLU-4","t":"中华人民共和国民法典共7编1260条，于2021年1月1日起施行。","q":"民法典共多少编？A)5编 B)6编 C)7编 D)8编"},
    {"id":"TF-1","t":"新型冠状病毒的正式名称为SARS-CoV-2，引起的疾病名为COVID-19。mRNA疫苗由辉瑞和莫德纳开发。","q":"新冠病毒正式名称？mRNA疫苗谁开发的？"},
    {"id":"TF-2","t":"青霉素由亚历山大·弗莱明于1928年发现。","q":"青霉素谁发现的？哪年？"},
    {"id":"TF-3","t":"比特币由化名中本聪的人于2009年创建，总量上限为2100万枚。","q":"比特币创建者？总量上限？"},
    {"id":"TF-4","t":"狭义相对论是1905年由爱因斯坦提出的，包含E=mc^2。","q":"狭义相对论哪年谁提出？什么公式？"}]
def run(text,question,eagle,compact,extract,idx):
    if extract:
        e=universal_extract(text,idx%3,SC,EX,question=question); ents=e.get("entities",[])
    else: ents=[]
    if not extract: ctx=text
    elif compact: ctx=serialize_compact({"E":ents})
    else: ctx=json.dumps({"E":ents},ensure_ascii=False)
    p=big_brain_answer({"E":ents,"compact_context":ctx},question,BR,text,BR,1,vram_folding=True,vram_limit=6144,eagle_eye=eagle,eagle_eye_model=EG)
    return p["answer"]

all_r={}
for cfg,eagle,compact,extract in [("no_eagle",False,True,True),("no_compact",False,False,True)]:
    print(f"\n[{cfg}]",flush=True)
    correct=0; times=[]
    for i,q in enumerate(QS):
        t0=time.time()
        try:
            a=run(q["t"],q["q"],eagle,compact,extract,i); t=round(time.time()-t0,1); times.append(t)
            ok=judge(q["q"],q["t"],a)
            if ok: correct+=1
            print(f"  {q['id']}: {'OK' if ok else 'XX'} {t}s",flush=True)
        except Exception as e: print(f"  {q['id']}: ERR {e}"); times.append(round(time.time()-t0,1))
        try: fold_cleanup([BR,EG,EX])
        except: pass
    avg=round(sum(times)/len(times),1) if times else 0; acc=round(correct/len(QS)*100,1)
    all_r[cfg]={"acc":acc,"avg_time":avg,"correct":correct}
    print(f"-> {correct}/{len(QS)} ({acc}%) {avg}s",flush=True)
with open(os.path.join(OUT,"ab_2configs.json"),"w",encoding="utf-8") as f: json.dump(all_r,f)
print("\nDONE!")