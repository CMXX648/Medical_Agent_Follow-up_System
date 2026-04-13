import json
import re
from datetime import timedelta

from django.conf import settings
from django.utils import timezone

from utils.chat import qwen, qwen_chat
from utils.rag import generate_health_advice


FOLLOWUP_DECISION_PROMPT = """
根据以下患者历史随访记录和本次随访内容，判断：
1. 是否需要继续跟进随访（是/否）
2. 建议的下次随访时间（若需要，格式 YYYY-MM-DD）
3. 判断理由（简要）

只返回 JSON，不要附加解释：
{"need_followup": true, "next_date": "2026-06-01", "reason": "..."}
"""


def _extract_json(text):
    if not text:
        return None

    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        return None

    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        return None


def _build_mock_dialogue(patient_info, history_records):
    history_summary = "；".join(
        [f"{item.get('record_date', '')}:{item.get('health_assessment', '')}" for item in history_records[:3]]
    )

    return (
        "问卷调查开始\n"
        f"AI: 您好，{patient_info['name']}，请问最近总体感觉如何？\n"
        "用户: 总体还可以，偶尔有点乏力。\n"
        "AI: 最近血压或血糖监测情况怎么样？\n"
        "用户: 有按时测量，基本稳定。\n"
        "AI: 用药是否规律？有没有漏服药物？\n"
        "用户: 基本规律，偶尔忘记一次。\n"
        f"历史摘要: {history_summary or '暂无历史记录'}\n"
        "AI: [SURVEY_END] 本次随访结束，祝您健康。\n"
    )


def decide_followup(history_text, current_dialogue):
    model_input = (
        f"【历史记录】\n{history_text or '无'}\n\n"
        f"【本次随访】\n{current_dialogue}\n"
    )

    raw = qwen(FOLLOWUP_DECISION_PROMPT, model_input, max_tokens=1200)
    decision = _extract_json(raw) or {}

    need_followup = bool(decision.get("need_followup", True))
    reason = decision.get("reason") or "模型未给出明确理由，按默认策略继续跟进。"

    next_date = None
    if need_followup:
        date_text = decision.get("next_date")
        if date_text:
            try:
                next_date = timezone.datetime.strptime(date_text, "%Y-%m-%d").date()
            except ValueError:
                next_date = None

        if not next_date:
            default_days = getattr(settings, "DEFAULT_AUTO_FOLLOWUP_DAYS", 7)
            next_date = timezone.localdate() + timedelta(days=default_days)

    return {
        "need_followup": need_followup,
        "next_date": next_date,
        "reason": reason,
        "raw": raw,
    }


def run_followup_agent(patient_info, history_records=None):
    history_records = history_records or []

    dialogue_history = _build_mock_dialogue(patient_info, history_records)

    try:
        survey_json = qwen_chat(dialogue_history)
    except Exception:
        survey_json = "{}"

    try:
        rag_advice = generate_health_advice(dialogue_history)
    except Exception:
        rag_advice = "建议规律作息、遵医嘱用药，并按时复诊。"

    history_text = "\n".join([
        f"{item.get('record_date', '')} {item.get('content', '')}" for item in history_records
    ])
    decision = decide_followup(history_text, dialogue_history)

    return {
        "dialogue_history": dialogue_history,
        "survey_json": survey_json,
        "rag_advice": rag_advice,
        "decision": decision,
    }
