from .file_utils import generate_survey_from_file
from utils.paths import QUESTIONNAIRE_TXT_PATH, SURVEY_PDF_PATH, ensure_output_dir

"""
author:cmxx648 
"""

def main():
    file_path = SURVEY_PDF_PATH

    try:
        survey = generate_survey_from_file(file_path)
        ensure_output_dir()

        with open(QUESTIONNAIRE_TXT_PATH, 'w', encoding='utf-8') as fw:
            print("调查问卷已生成")
            fw.write(survey)

    except Exception as e:
        print(f"生成调查问卷时发生错误：{e}")


# 当文件作为脚本运行时，执行主函数
if __name__ == "__main__":
    main()
