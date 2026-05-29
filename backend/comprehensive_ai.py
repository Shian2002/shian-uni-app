"""首页综合 AI 问答配置与提示词构建。"""
import json


COMPREHENSIVE_LLM_MODELS = [
    {
        "id": "basic",
        "name": "基础模型",
        "provider": "deepseek",
        "strength": "基础",
        "cost_base": 2,
        "cost_multiplier": 1,
        "followup_cost": 1,
        "enabled": True,
    }
]


COMPREHENSIVE_TOOL_MODELS = [
    {"id": "bazi", "name": "八字", "cost": 2},
    {"id": "ziwei", "name": "紫微斗数", "cost": 3},
    {"id": "qimen", "name": "奇门遁甲", "cost": 3},
    {"id": "liuyao", "name": "六爻", "cost": 2},
    {"id": "meihua", "name": "梅花易数", "cost": 2},
]


def get_llm_model(model_id):
    for model in COMPREHENSIVE_LLM_MODELS:
        if model["id"] == model_id and model.get("enabled"):
            return model
    return COMPREHENSIVE_LLM_MODELS[0]


def normalize_tool_models(tool_models):
    allowed = {item["id"] for item in COMPREHENSIVE_TOOL_MODELS}
    result = []
    for item in tool_models or []:
        if item in allowed and item not in result:
            result.append(item)
    return result


def calculate_cost(model_id, tool_models, is_followup=False):
    model = get_llm_model(model_id)
    if is_followup:
        return int(model.get("followup_cost", 1))
    selected = normalize_tool_models(tool_models)
    tool_cost_map = {item["id"]: int(item.get("cost", 0)) for item in COMPREHENSIVE_TOOL_MODELS}
    tools_cost = sum(tool_cost_map.get(item, 0) for item in selected)
    multiplier = float(model.get("cost_multiplier", 1))
    return int(round(int(model.get("cost_base", 0)) + tools_cost * multiplier))


def build_comprehensive_messages(question, profile, tool_models, paipan_context, history=None):
    system = """你是时安解忧屋的综合命理答疑助手。
你必须基于后端已经生成的排盘数据进行分析，不要自行编造出生信息、干支、宫位、星曜或卦象。
回答要求：
1. 先给出直接结论；
2. 分术数说明依据；
3. 汇总不同术数之间一致和冲突的地方；
4. 给出可执行建议；
5. 明确提示内容仅为民俗文化参考，不构成现实决策承诺。
"""
    context = {
        "profile": profile or {},
        "selected_tools": tool_models,
        "paipan_context": paipan_context or {},
    }
    messages = [{"role": "system", "content": system}]
    for item in history or []:
        if item.get("role") in ("user", "assistant"):
            messages.append({"role": item["role"], "content": str(item.get("content", ""))[:6000]})
    messages.append({
        "role": "user",
        "content": "用户问题：%s\n\n后端排盘上下文：\n%s" % (
            question,
            json.dumps(context, ensure_ascii=False, indent=2),
        ),
    })
    return messages
