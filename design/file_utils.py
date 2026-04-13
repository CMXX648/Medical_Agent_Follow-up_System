from utils.chat import kimi_client, kimi_chat
from pathlib import Path
from design.prompt import PROMPT


def upload_and_extract_file_content(file_path):
    try:
        with Path(file_path).open('rb') as file:
            file_object = kimi_client.files.create(file=file, purpose="file-extract")

        # 获取文件内容
        file_content = kimi_client.files.content(file_id=file_object.id).text

        # 删除文件对象，清理资源
        kimi_client.files.delete(file_id=file_object.id)

        return file_content
    except Exception as e:
        return f"Error during file upload and content extraction: {e}"


def generate_survey_from_file(file_path):
    # 提取文件内容
    file_content = upload_and_extract_file_content(file_path)
    if file_content:
        user_content = f"这是原问卷内容：\"\"\"{file_content}\"\"\""
        system_prompt = PROMPT
        # 使用提取的内容生成问卷
        return kimi_chat(system_prompt, user_content)
    else:
        print("Failed to extract content from the file.")
        return None
