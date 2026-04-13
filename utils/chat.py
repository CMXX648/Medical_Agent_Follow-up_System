import os
import re
import json
from dotenv import load_dotenv
from openai import OpenAI
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from survey.prompt import PROMPT1, PROMPT2
from utils.paths import QUESTIONNAIRE_TXT_PATH

# 加载环境变量
load_dotenv()

try:
    with open(QUESTIONNAIRE_TXT_PATH, 'r', encoding='utf-8') as fr:
        file_content = fr.read()
    questionnaire_text = f"这是问卷内容。\n \n \"{file_content}\""
except FileNotFoundError:
    questionnaire_text = "（问卷内容未加载，请先运行 design/designer.py 生成问卷文件）"
    print(f"[警告] 未找到问卷文件 {QUESTIONNAIRE_TXT_PATH}，请先运行 design/designer.py 生成问卷。")

# 预热消息列表构建函数（只调用一次）
# 使用模型1作提问员
def build_warmup_messages(patient_info=None):
    pre_filled = ""
    if patient_info:
        pre_filled = f"\n\n已知患者信息（无需重复询问）：姓名={patient_info['name']}，性别={patient_info['gender']}，年龄={patient_info['age']}岁"
    return [
        SystemMessage(content=PROMPT1),
        AIMessage(content="好的，请提供随访问卷..."),
        HumanMessage(content=questionnaire_text + pre_filled),
        AIMessage(content='好的，当你输入"问卷开始"后我将按照你提供的问卷问题顺序逐个提问')
    ]


def chat_with_model(model, messages, max_tokens=5000):
    response = model.invoke(messages, config={"max_tokens": max_tokens})
    return response.content


# OpenAI客户端用于文件上传功能
kimi_client = OpenAI(
    api_key=os.getenv('KIMI_API_KEY'),
    base_url=os.getenv('KIMI_API_BASE')
)

# 使用LangChain的模型抽象用于聊天
kimi_model = ChatOpenAI(
    api_key=os.getenv('KIMI_API_KEY'),
    base_url=os.getenv('KIMI_API_BASE'),
    model_name="moonshot-v1-8k",
    temperature=0.3
)

qwen_model = ChatOpenAI(
    api_key=os.getenv('DASHSCOPE_API_KEY'),
    base_url=os.getenv('QWEN_API_BASE'),
    model_name="qwen-plus",
    temperature=0.5
)




# 使用模型2作归纳员
def qwen_chat(user_content, functions=None,max_tokens=5000):
    messages = [
        {"role": "system",
         "content": PROMPT2},
        {"role": "assistant",
         "content": "好的，请提供随访问卷内容"},
        {"role": "user",
         "content": questionnaire_text},
        {"role": "assistant",
         "content": "好的，请继续提供随访对话记录，我将会对对话记录转换为JSON格式"},
        {"role": "user",
         "content": user_content}
    ]
    response = qwen_model.invoke(messages, config={"max_tokens": max_tokens})
    return response.content



def kimi(system_prompt, user_content, functions=None, max_tokens=5000):
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_content)
    ]
    response = kimi_model.invoke(messages, config={"max_tokens": max_tokens})
    return response.content


def qwen(system_prompt, user_content, functions=None, max_tokens=5000):
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_content)
    ]
    response = qwen_model.invoke(messages, config={"max_tokens": max_tokens})
    return response.content

#========================================================================
### 用于保存对话记录
def record_dialogue_history(dialogue_history, output_file):
    try:
        with open(output_file, 'w', encoding='utf-8') as file:
            file.write(dialogue_history)
    except Exception as e:
        print(f"保存对话历史时出错: {e}")


# 历史聊天文本切割为json
def contains_json(text):
    json_pattern = re.compile(r'[{].*?[}]', re.DOTALL)
    possible_jsons = json_pattern.findall(text)
    for possible_json in possible_jsons:
        if is_json(possible_json):
            return True
    return False


def is_json(text):
    try:
        json_object = json.loads(text)
    except ValueError as e:
        return False
    return True
