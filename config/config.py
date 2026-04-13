"""
随访系统配置文件
"""
from utils.paths import BACKEND_APP_DIR, OUTPUT_DIR

# 医生信息配置
DEFAULT_DOCTOR = {
    'name': '王医生',
    'gender': '男',
    'phone': '13800000000',  # 默认医生电话号码
    'department': '内科',
    'title': '主治医师'
}

# Django项目配置
DJANGO_SETTINGS_MODULE = 'medical_followup.settings'
DJANGO_PROJECT_PATH = str(BACKEND_APP_DIR)

# 随访记录配置
FOLLOW_UP_OUTPUT_DIR = str(OUTPUT_DIR / 'follow_up_records')
FOLLOW_UP_FILE_PREFIX = 'follow_up_'
