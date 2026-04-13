import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

qwen_client = OpenAI(api_key=os.getenv('DASHSCOPE_API_KEY'), base_url=os.getenv('QWEN_API_BASE'))


def perform_chat(client, model_name, messages, temperature, max_tokens):
    response = client.chat.completions.create(
        model=model_name,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens
    )
    return response.choices[0].message.content


def generate_feedback(initial_output):
    feedback_prompt = [
        {"role": "system",
         "content": f"请对以下内容提供反馈和改进建议：\n\n{initial_output}\n\n请详细描述需要改进的部分并提供具体建议。"},
    ]
    response = perform_chat(qwen_client, "qwen-plus", feedback_prompt, temperature=0.85, max_tokens=8000)
    return response


def optimize_output(initial_output, feedback):
    optimization_prompt = [
        {"role": "system",
         "content": f"根据以下反馈对初始输出进行优化：\n\n初始输出：\n{initial_output}\n\n反馈：\n{feedback}\n\n请生成改进后的输出。"},
    ]

    response = perform_chat(qwen_client, "qwen-plus", optimization_prompt, temperature=0.85, max_tokens=8000)
    return response


class Reflection:
    # 初始化反思对象，设置最大迭代次数和质量阈值
    def __init__(self, max_iterations=5, quality_threshold=0.9):
        self.logs = []
        self.max_iterations = max_iterations
        self.quality_threshold = quality_threshold

    # 记录每次交互的日志
    def log_interaction(self, message, response):
        self.logs.append((message, response))

    def reflect(self):
        reflections = []
        for message, response in self.logs:
            if "error" in response.lower():
                reflections.append((message, response, "Error detected"))
            else:
                reflections.append((message, response, "Response is fine"))
        return reflections

    # 执行反馈和优化的迭代过程，直到达到预定的停止条件
    def iterative_optimization(self, initial_output):
        current_output = initial_output
        for iteration in range(self.max_iterations):
            feedback = generate_feedback(current_output)
            current_output = optimize_output(current_output, feedback)
            self.log_interaction(current_output, feedback)

            # 模拟质量评估，这里假设每次迭代质量增加0.1
            current_quality = (iteration + 1) * 0.1
            if current_quality >= self.quality_threshold:
                break

        return current_output


# 函数入口
def perform_reflection(initial_output):
    reflection = Reflection()
    final_output = reflection.iterative_optimization(initial_output)
    return final_output
