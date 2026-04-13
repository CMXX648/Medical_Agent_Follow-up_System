# 医疗随访管理系统

## 1. 项目介绍
本项目将医生端 Django 管理系统与 AI 随访能力打通，形成“医生录入 -> 系统自动随访 -> 自动决策是否继续跟进”的闭环。

当前系统定位为可运行的自动化基础版本：
1. Django 负责患者和医生管理、随访记录展示。
2. Celery + Redis 负责定时调度和异步执行。
3. Survey Agent 负责生成对话、问卷结构化结果和健康建议。
4. 决策 Agent 负责判断是否继续随访并回写患者状态。

## 2. 已实现功能
1. 医生用户注册、登录、个人信息维护。
2. 患者管理与随访记录管理（Django 页面 + Admin）。
3. 患者自动随访字段支持：
   - next_follow_up_date
   - followup_status（pending/completed/no_needed）
   - contact_method（phone/sms/wechat）
4. 随访记录自动化字段支持：
   - need_further_followup
   - decision_reason
   - ai_generated
5. 每天 08:00 定时扫描“当天应随访患者”（Celery Beat）。
6. 单患者自动随访任务（Celery Worker）执行后自动写入 FollowUpRecord。
7. LLM 决策结果自动更新患者下次随访日期和状态。
8. Docker Compose 一键编排 Django + PostgreSQL + Redis + Celery Worker + Celery Beat。

说明：当前随访渠道为可编排的自动流程，主执行逻辑在 survey/agent.py，可继续扩展为真实电话外呼或短信链接。

## 3. 技术栈
1. 后端框架：Django 6
2. 异步任务：Celery + django-celery-beat
3. 消息队列：Redis
4. 数据库：PostgreSQL
5. 大模型调用：OpenAI SDK + LangChain
6. 向量检索：FAISS
7. 前端：Django Template + Tailwind CSS + Font Awesome

## 4. 目录结构
```text
talk/
├── backend/
│   └── medical_followup/
│       ├── manage.py
│       ├── accounts/                       # 医生账户体系
│       ├── core/                           # 患者、随访记录、任务调度
│       └── backend/medical_followup/       # Django settings/urls/celery
├── survey/                                 # Survey Agent 与随访流程
├── utils/                                  # LLM、ASR/TTS、RAG、路径等工具
├── scripts/                                # Django 数据访问脚本
├── design/                                 # 问卷文件生成
├── config/                                 # 配置入口
├── output/                                 # 问卷与随访输出
├── docker-compose.yml                      # 部署编排
├── requirements.txt
└── readme.md
```

## 5. 环境要求
1. Python 3.12+
2. PostgreSQL 14+
3. Redis 6+
4. Windows PowerShell 或 Linux Shell

## 6. 安装与初始化
### 6.1 创建并激活虚拟环境
Windows:
```powershell
python -m venv venv
venv\Scripts\Activate.ps1
```

Linux/macOS:
```bash
python -m venv venv
source venv/bin/activate
```

### 6.2 安装依赖
```bash
pip install -r requirements.txt
```

### 6.3 配置数据库
默认配置在 backend/medical_followup/backend/medical_followup/settings.py：
1. 数据库名：medical_followup
2. 用户名：postgres
3. 密码：postgres123
4. 主机：localhost:5432

### 6.4 执行迁移
```bash
venv\Scripts\python.exe backend/medical_followup/manage.py migrate
```

### 6.5 创建管理员
```bash
venv\Scripts\python.exe backend/medical_followup/manage.py createsuperuser
```

## 7. 启动方式
### 7.1 本地开发（推荐）
分别启动 3 个进程：

终端 1（Django）：
```bash
venv\Scripts\python.exe backend/medical_followup/manage.py runserver 8001
```

终端 2（Celery Worker）：
```bash
venv\Scripts\celery.exe -A backend.medical_followup worker -l info
```

终端 3（Celery Beat）：
```bash
venv\Scripts\celery.exe -A backend.medical_followup beat -l info
```

访问地址：
1. 业务页面：http://127.0.0.1:8001/
2. 后台管理：http://127.0.0.1:8001/admin/

### 7.2 Docker Compose
```bash
docker-compose up -d
```

## 8. 自动随访执行流程
1. 医生录入患者并设置 next_follow_up_date。
2. Celery Beat 每天 08:00 扫描当天待随访患者。
3. Worker 执行 run_patient_followup 任务。
4. Survey Agent 产出：
   - 对话文本
   - 问卷 JSON
   - RAG 健康建议
5. 决策 Agent 返回是否继续随访与建议日期。
6. 系统写入 FollowUpRecord，并更新 Patient.followup_status 与 next_follow_up_date。

## 9. 常用命令
检查 Django 配置：
```bash
venv\Scripts\python.exe backend/medical_followup/manage.py check
```

检查迁移是否完整：
```bash
venv\Scripts\python.exe backend/medical_followup/manage.py makemigrations --check
```

手动运行一次自动随访（示例入口）：
```bash
venv\Scripts\python.exe survey/main.py --patient-name 张三
```

## 10. 后续建议
1. 将 survey/agent.py 的 mock 对话替换为真实电话外呼或短信问卷渠道。
2. 增加 Celery 任务重试、告警和幂等保护。
3. 补充自动化测试（模型、任务、决策解析、状态回写）。