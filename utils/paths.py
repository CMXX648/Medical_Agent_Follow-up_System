from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# 常用目录
OUTPUT_DIR = PROJECT_ROOT / "output"
DESIGN_DIR = PROJECT_ROOT / "design"
BACKEND_APP_DIR = PROJECT_ROOT / "backend" / "medical_followup"

# 常用文件
QUESTIONNAIRE_TXT_PATH = OUTPUT_DIR / "Q.txt"
FINAL_TXT_PATH = OUTPUT_DIR / "final.txt"
FINAL_JSON_PATH = OUTPUT_DIR / "final1.json"
SURVEY_PDF_PATH = DESIGN_DIR / "慢病随访调查问卷.pdf"
VECTORSTORE_DIR = OUTPUT_DIR / "vectorstore"


def ensure_output_dir() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
