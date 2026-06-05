"""首页综合 AI 问答配置与提示词构建。"""
import json


COMPREHENSIVE_LLM_MODELS = [
    {
        "id": "basic",
        "name": "基础模型",
        "cost_base": 2,
        "cost_multiplier": 0,
        "followup_cost": 2,
        "enabled": True,
    },
    {
        "id": "advanced",
        "name": "高级模型",
        "cost_base": 4,
        "cost_multiplier": 0,
        "followup_cost": 4,
        "enabled": True,
    },
    {
        "id": "expert",
        "name": "专家模型",
        "cost_base": 8,
        "cost_multiplier": 0,
        "followup_cost": 8,
        "enabled": True,
    }
]

COMPREHENSIVE_READING_MODES = [
    {"id": "concise", "name": "简约", "cost_delta": -1, "display_cost": 1},
    {"id": "standard", "name": "标准", "cost_delta": 0, "display_cost": 2},
    {"id": "deep", "name": "深度", "cost_delta": 2, "display_cost": 4},
]


COMPREHENSIVE_TOOL_MODELS = [
    {"id": "qimen", "name": "奇门遁甲", "cost": 3, "needs_profile": False},
    {"id": "bazi", "name": "八字", "cost": 2, "needs_profile": True},
    {"id": "liuyao", "name": "六爻", "cost": 2, "needs_profile": False},
    {"id": "meihua", "name": "梅花易数", "cost": 2, "needs_profile": False},
    {"id": "ziwei", "name": "紫微斗数", "cost": 3, "needs_profile": True},
    {"id": "tarot", "name": "塔罗牌", "cost": 2, "needs_profile": False},
    {"id": "zeji", "name": "择吉工具", "cost": 2, "needs_profile": False},
]

TOOL_DISPLAY_ORDER = ["qimen", "bazi", "liuyao", "meihua", "ziwei", "tarot", "zeji"]


def get_llm_model(model_id):
    for model in COMPREHENSIVE_LLM_MODELS:
        if model["id"] == model_id and model.get("enabled"):
            return model
    return COMPREHENSIVE_LLM_MODELS[0]


def get_reading_mode(mode_id):
    for mode in COMPREHENSIVE_READING_MODES:
        if mode["id"] == mode_id:
            return mode
    return COMPREHENSIVE_READING_MODES[1]


def normalize_tool_models(tool_models):
    allowed = {item["id"] for item in COMPREHENSIVE_TOOL_MODELS}
    result = []
    for item in tool_models or []:
        if item in allowed and item not in result:
            result.append(item)
    return sorted(result, key=lambda x: TOOL_DISPLAY_ORDER.index(x) if x in TOOL_DISPLAY_ORDER else 99)


def recommend_tool_models(question):
    text = str(question or "").strip()
    if not text:
        return ["bazi", "qimen"], "默认以八字看底盘、奇门看当下。"
    lower = text.lower()
    zeji_kw = ["开业", "搬家", "入宅", "签约", "婚嫁", "结婚日", "领证", "出行", "动土", "装修", "择日", "哪天", "吉日"]
    marriage_kw = ["什么时候结婚", "何时结婚", "婚姻", "正缘", "姻缘", "对象", "伴侣"]
    return_kw = ["回来", "复合", "还会不会", "联系我", "想我", "感情状态", "心理", "暧昧", "分手"]
    concrete_kw = ["成败", "应期", "能不能", "是否", "靠谱吗", "合作", "官司", "失物", "找回", "结果", "面试"]
    decision_kw = ["跳槽", "换工作", "投资", "项目", "决策", "方向", "选择", "现在", "当下", "要不要"]
    career_base_kw = ["适合什么工作", "适合做什么", "职业", "事业方向", "工作方向", "适合行业"]
    long_kw = ["命局", "事业", "财运", "格局", "长期", "人生", "未来几年", "大运", "流年"]

    if any(k in text for k in zeji_kw):
        return ["zeji"], "问题重点在择日择时，优先使用择吉。"
    if any(k in text for k in career_base_kw):
        return ["bazi"], "职业方向先看八字基本命盘。"
    if any(k in text for k in marriage_kw):
        return ["bazi", "ziwei"], "婚恋时间和长期关系适合八字结合紫微。"
    if any(k in text for k in return_kw):
        return ["liuyao", "meihua", "tarot"], "具体情感应事以六爻、梅花为主，可补塔罗看状态。"
    if any(k in text for k in concrete_kw):
        if "合作" in text or "靠谱吗" in text:
            return ["qimen", "liuyao"], "合作决策适合奇门看局势、六爻看成败。"
        return ["liuyao", "meihua"], "一事一问和成败应期适合六爻、梅花。"
    if any(k in text for k in decision_kw):
        return ["bazi", "qimen"], "个人选择以八字看底层趋势、奇门看当下局势。"
    if any(k in text for k in long_kw) or any(k in lower for k in ["career", "life"]):
        return ["bazi", "ziwei"], "长期命局和阶段趋势适合八字结合紫微。"
    return ["bazi", "qimen"], "无法明确归类时，默认八字看底盘、奇门看当下。"


def calculate_cost(model_id, tool_models, is_followup=False, profile_count=1, reading_mode='standard'):
    model = get_llm_model(model_id)
    mode_delta = int(get_reading_mode(reading_mode).get("cost_delta", 0))
    if is_followup:
        return max(0, int(model.get("followup_cost", 1)) + mode_delta)
    selected = normalize_tool_models(tool_models)
    tool_cost_map = {item["id"]: int(item.get("cost", 0)) for item in COMPREHENSIVE_TOOL_MODELS}
    tools_cost = sum(tool_cost_map.get(item, 0) for item in selected)
    multiplier = float(model.get("cost_multiplier", 1))
    count = max(1, int(profile_count or 1))
    return max(0, int(round(int(model.get("cost_base", 0)) + tools_cost * count * multiplier + mode_delta)))


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


def build_tool_analysis_messages(question, profile, tool, tool_data, history=None):
    tool_names = {
        "qimen": "奇门遁甲",
        "bazi": "八字排盘",
        "liuyao": "六爻排盘",
        "meihua": "梅花易数",
        "ziwei": "紫微斗数",
        "tarot": "塔罗牌",
        "zeji": "择吉工具",
    }
    system = """你是时安解忧屋的单项术数解读助手。
你只能围绕当前给出的一个术数盘面解读，不能跳到其他术数。
输出要求：
1. 先用一句话给出该术数对用户问题的判断；
2. 再列出盘面依据，必须引用当前盘面的具体信息；
3. 最后给出该术数下的建议或提醒；
4. 不要重复排盘数据，不要编造盘里没有的信息；
5. 不要输出 JSON 字段名或 snake_case 内部键名，八字关系字段必须改用中文术语，例如 zhi_liu_chong 说成“地支六冲”。
"""
    messages = [{"role": "system", "content": system}]
    for item in history or []:
        if item.get("role") in ("user", "assistant"):
            messages.append({"role": item["role"], "content": str(item.get("content", ""))[:2000]})
    messages.append({
        "role": "user",
        "content": "用户问题：%s\n\n当前术数：%s\n\n命盘档案：\n%s\n\n当前术数盘面数据：\n%s" % (
            question,
            tool_names.get(tool, tool),
            json.dumps(profile or {}, ensure_ascii=False, indent=2),
            json.dumps(tool_data or {}, ensure_ascii=False, indent=2),
        ),
    })
    return messages


def build_summary_messages(question, profile, tool_models, tool_analyses, history=None):
    system = """你是时安解忧屋的综合合参助手。
你已经拿到了各术数的单项分析，现在只做最后合参总结。
输出要求：
1. 直接给出综合结论；
2. 汇总各术数一致的地方；
3. 标出冲突或需要谨慎看的地方；
4. 给出用户接下来可以执行的建议；
5. 明确内容仅为民俗文化参考，不构成现实决策承诺。
"""
    messages = [{"role": "system", "content": system}]
    for item in history or []:
        if item.get("role") in ("user", "assistant"):
            messages.append({"role": item["role"], "content": str(item.get("content", ""))[:2000]})
    messages.append({
        "role": "user",
        "content": "用户问题：%s\n\n命盘档案：\n%s\n\n已完成的单项术数分析：\n%s" % (
            question,
            json.dumps(profile or {}, ensure_ascii=False, indent=2),
            json.dumps(tool_analyses or {}, ensure_ascii=False, indent=2),
        ),
    })
    return messages
