import json


def evaluate_and_suggest(dialogue_history):
    # 初始化评分
    score = 0
    suggestions = []
    factors = {
        "慢性病病史": 1,  # 默认为低危
        "生活习惯": 1,  # 默认为低危
        "体征": 1,  # 默认为低危
        "家族史": 1,  # 默认为低危
        "既往疾病史及控制情况": 1  # 默认为低危
    }

    # 解析对话历史
    if "慢性病病史" in dialogue_history:
        if "病情控制不佳" in dialogue_history:
            factors["慢性病病史"] = 3
        elif "病情得到良好控制" in dialogue_history:
            factors["慢性病病史"] = 2

    if "生活习惯" in dialogue_history:
        if "多个不健康生活习惯" in dialogue_history:
            factors["生活习惯"] = 3
        elif "少量不健康生活习惯" in dialogue_history:
            factors["生活习惯"] = 2

    if "体征" in dialogue_history:
        if "高血压" in dialogue_history or "肥胖" in dialogue_history:
            factors["体征"] = 3
        elif "轻微血压升高" in dialogue_history or "BMI略高" in dialogue_history:
            factors["体征"] = 2

    if "家族史" in dialogue_history:
        if "家族中多位患病亲属" in dialogue_history:
            factors["家族史"] = 3
        elif "家族中有患病但数量不多" in dialogue_history:
            factors["家族史"] = 2

    if "既往疾病史及控制情况" in dialogue_history:
        if "病情控制不佳" in dialogue_history:
            factors["既往疾病史及控制情况"] = 3
        elif "病情得到良好控制" in dialogue_history:
            factors["既往疾病史及控制情况"] = 2

    # 计算总分
    score = sum(factors.values())

    # 生成建议
    if score <= 7:
        risk_level = "低危"
        suggestions.append("您的整体健康风险较低，请继续保持健康的生活方式。")
    elif 8 <= score <= 11:
        risk_level = "中危"
        suggestions.append("您的整体健康风险中等，请注意调整生活方式，定期进行健康检查。")
    else:
        risk_level = "高危"
        suggestions.append("您的整体健康风险较高，请及时就医并积极配合治疗，改善生活习惯。")

    # 返回JSON格式的对话历史和建议
    result = {
        "dialogue_history": dialogue_history,
        "score": score,
        "risk_level": risk_level,
        "suggestions": suggestions
    }

    return json.dumps(result, ensure_ascii=False, indent=4)
