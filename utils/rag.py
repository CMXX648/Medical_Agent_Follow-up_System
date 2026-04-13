# utils/rag.py
import os
import re
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.documents import Document
from utils.chat import kimi_model
from utils.paths import VECTORSTORE_DIR, ensure_output_dir

# ------------------------------------------------------------------ #
#  知识库文档
# ------------------------------------------------------------------ #
HEALTH_DOCUMENTS = [
    # 高血压
    "高血压患者自测血压建议每天固定时段，测量前静坐5-10分钟。",
    "高血压患者除低盐外，还应减少腌制食品、加工肉类的摄入。",
    "家庭自测血压的正常值为收缩压<135mmHg，舒张压<85mmHg。",
    "高盐饮食会使血压升高，高血压患者烹饪建议用蒸、煮、炖，少用红烧、酱卤。",
    "糖尿病患者合并高血压时，血压应控制在130/80mmHg以下。",
    # 糖尿病
    "糖尿病患者需控制空腹血糖在3.9-7.0mmol/L，餐后2小时血糖<10.0mmol/L。",
    "糖尿病患者应规律监测糖化血红蛋白，建议每3个月检测一次。",
    "糖尿病患者需做好足部护理，每天检查足部，避免外伤和感染。",
    "糖尿病患者应均衡饮食，主食可替换为杂粮、杂豆，增加膳食纤维摄入。",
    # 血脂
    "血脂异常患者需减少高胆固醇、高甘油三酯食物，如动物内脏、油炸食品。",
    "高胆固醇血症患者服用他汀类药物，需定期检查肝功能和肌酸激酶。",
    "血脂异常患者可适当增加深海鱼、坚果等富含不饱和脂肪酸的食物。",
    "高血脂患者若饮食和运动干预无效，需及时启动药物治疗。",
    # 冠心病
    "冠心病患者规律服用抗栓药物，不可擅自停药或调整剂量。",
    "冠心病患者出现胸闷、胸痛时，应立即停止活动并休息，及时就医。",
    "冠心病患者应减少浓茶、咖啡、辛辣刺激性食物的摄入。",
    # 脑卒中
    "脑卒中恢复期患者应坚持康复训练，建议在发病后3-6个月黄金期持续进行。",
    "短暂性脑缺血发作(TIA)患者需及时治疗，降低脑梗死发生风险。",
    "脑卒中患者需控制基础病，将血压、血糖、血脂控制在达标范围。",
    "康复治疗需在专业医生指导下进行，避免自行训练导致二次损伤。",
    "有脑卒中家族史者，应更早开始控制血压、血糖、血脂，定期做脑血管检查。",
    # 房颤
    "房颤患者服用抗凝药物，需定期监测凝血功能，避免出血风险。",
    # 生活方式
    "吸烟者戒烟后24小时内，心血管疾病风险即可开始降低。",
    "戒烟困难者可借助戒烟药物、戒烟门诊等专业方式辅助戒烟。",
    "成年男性腰围应控制在90cm以下，女性腰围控制在85cm以下，减少中心性肥胖。",
    "成年人BMI应维持在18.5-23.9kg/m²，超重或肥胖者需逐步减重。",
    "中等强度运动包括快走、太极拳、慢跑、游泳，每次运动不少于30分钟。",
    "慢病患者运动前应评估身体状况，避免空腹或餐后立即运动。",
    "慢病患者需规律作息，避免熬夜，每天保证7-8小时睡眠时间。",
    "饮酒会升高血压、血糖，高血压和糖尿病患者建议尽量不饮酒。",
    "规律饮水有助于代谢，成年人每天建议饮用1500-2000ml白开水。",
    "情绪波动会诱发血压骤升，慢病患者应保持心态平和，避免过度焦虑。",
    "长期久坐会增加慢病风险，建议每坐1小时起身活动5-10分钟。",
    "慢病患者应定期复查，高血压、糖尿病患者建议每1-3个月复查一次。",
    "慢病患者遵循医嘱用药，漏服药物不可擅自加倍服用。",
]

# ------------------------------------------------------------------ #
#  单例向量库，只构建一次
# ------------------------------------------------------------------ #
_vectorstore = None

def get_vector_store() -> FAISS:
    global _vectorstore
    if _vectorstore is None:
        print("正在初始化知识库...")
        documents = [Document(page_content=doc) for doc in HEALTH_DOCUMENTS]
        embeddings = OpenAIEmbeddings(
            api_key=os.getenv('KIMI_API_KEY'),
            base_url=os.getenv('KIMI_API_BASE')
        )
        _vectorstore = FAISS.from_documents(documents, embeddings)
        print(f"知识库初始化完成，共 {len(documents)} 条文档。")
    return _vectorstore


# ------------------------------------------------------------------ #
#  关键词提取：从对话中提取疾病/症状词用于检索
# ------------------------------------------------------------------ #
KEYWORD_MAP = {
    "高血压": ["血压", "高血压", "降压药", "收缩压", "舒张压"],
    "糖尿病": ["血糖", "糖尿病", "胰岛素", "糖化血红蛋白", "空腹血糖"],
    "血脂异常": ["血脂", "胆固醇", "甘油三酯", "他汀"],
    "冠心病": ["冠心病", "心绞痛", "胸闷", "胸痛", "心肌梗死"],
    "脑卒中": ["脑卒中", "中风", "偏瘫", "失语", "TIA", "脑梗"],
    "房颤": ["房颤", "心律不齐", "抗凝"],
    "肥胖": ["肥胖", "超重", "BMI", "腰围"],
    "吸烟": ["吸烟", "抽烟", "戒烟"],
    "饮酒": ["饮酒", "喝酒", "戒酒"],
    "运动": ["运动", "锻炼", "步行", "太极"],
}

def extract_keywords(dialogue_history: str) -> str:
    """从对话历史中提取疾病关键词，返回用于检索的查询字符串"""
    matched = []
    for label, terms in KEYWORD_MAP.items():
        if any(term in dialogue_history for term in terms):
            matched.append(label)

    if not matched:
        return "慢性病健康管理建议"

    return "，".join(matched) + "的健康管理建议"


# ------------------------------------------------------------------ #
#  对外接口
# ------------------------------------------------------------------ #
def generate_health_advice(dialogue_history: str) -> str:
    """
    基于对话历史生成健康建议。
    1. 提取关键词
    2. 检索相关知识
    3. 调用模型生成建议
    """
    try:
        vs = get_vector_store()

        # 用关键词检索，而不是整段对话
        query = extract_keywords(dialogue_history)
        print(f"[RAG] 检索关键词: {query}")

        docs = vs.similarity_search(query, k=5)
        context = "\n".join([f"- {doc.page_content}" for doc in docs])

        messages = [
            SystemMessage(content=(
                "你是一名专业的医疗随访健康顾问。"
                "请根据提供的健康知识和患者随访信息，生成针对性的健康建议。"
                "建议需具体、可操作，避免泛泛而谈。"
                "输出格式：分点列出，每点不超过两句话。"
            )),
            HumanMessage(content=(
                f"【参考健康知识】\n{context}\n\n"
                f"【患者随访记录】\n{dialogue_history}\n\n"
                f"请生成针对该患者的健康建议："
            ))
        ]

        response = kimi_model.invoke(messages)
        return response.content

    except Exception as e:
        print(f"[RAG] 生成健康建议出错: {e}")
        return "建议您保持健康的生活方式，定期复查，并遵循医生的建议。"


# ------------------------------------------------------------------ #
#  可选：持久化向量库到磁盘，避免每次重新向量化
# ------------------------------------------------------------------ #
VECTORSTORE_PATH = str(VECTORSTORE_DIR)

def save_vector_store():
    """将向量库保存到磁盘"""
    ensure_output_dir()
    vs = get_vector_store()
    vs.save_local(VECTORSTORE_PATH)
    print(f"向量库已保存到 {VECTORSTORE_PATH}")

def load_vector_store_from_disk():
    """从磁盘加载向量库，避免重复向量化"""
    global _vectorstore
    try:
        embeddings = OpenAIEmbeddings(
            api_key=os.getenv('KIMI_API_KEY'),
            base_url=os.getenv('KIMI_API_BASE')
        )
        if os.path.exists(VECTORSTORE_PATH):
            _vectorstore = FAISS.load_local(
                VECTORSTORE_PATH,
                embeddings,
                allow_dangerous_deserialization=True
            )
            print("向量库已从磁盘加载。")
        else:
            print("未找到本地向量库，重新构建...")
            get_vector_store()
            save_vector_store()
    except Exception as e:
        print(f"向量库初始化失败: {e}")
        print("RAG功能将不可用，但问卷功能仍可正常使用。")