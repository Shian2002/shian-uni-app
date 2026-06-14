"""首页综合 AI 问答配置与提示词构建。"""
import json


COMPREHENSIVE_LLM_MODELS = [
    {
        "id": "basic",
        "name": "SHIAN-1.1",
        "cost_base": 2,
        "cost_multiplier": 0,
        "followup_cost": 2,
        "enabled": True,
    }
]

_LEGACY_LLM_MODEL_CONFIG = {
    "advanced": {
        "id": "advanced",
        "name": "时安高级模型",
        "cost_base": 4,
        "cost_multiplier": 0,
        "followup_cost": 4,
        "enabled": False,
    },
    "expert": {
        "id": "expert",
        "name": "时安专家模型",
        "cost_base": 8,
        "cost_multiplier": 0,
        "followup_cost": 8,
        "enabled": False,
    },
}

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
    if model_id in _LEGACY_LLM_MODEL_CONFIG:
        return _LEGACY_LLM_MODEL_CONFIG[model_id]
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
    boss_kw = ["老板", "创业", "做生意", "开公司", "合伙人", "管理者", "领导"]
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
    if any(k in text for k in boss_kw):
        return ["bazi", "qimen"], "是否适合当老板，先用八字看底层性格、财官结构和长期承压能力，再用奇门看当下局势与行动窗口。"
    if any(k in text for k in concrete_kw):
        if "合作" in text or "靠谱吗" in text:
            return ["qimen", "liuyao"], "合作决策适合奇门看局势、六爻看成败。"
        return ["liuyao", "meihua"], "一事一问和成败应期适合六爻、梅花。"
    if any(k in text for k in decision_kw):
        return ["bazi", "qimen"], "个人选择以八字看底层趋势、奇门看当下局势。"
    if any(k in text for k in long_kw) or any(k in lower for k in ["career", "life"]):
        return ["bazi", "ziwei"], "长期命局和阶段趋势适合八字结合紫微。"
    return ["bazi", "qimen"], "无法明确归类时，默认八字看底盘、奇门看当下。"


def _question_intent(question):
    text = str(question or "").strip()
    if any(k in text for k in ["复合", "回来", "分手", "暧昧", "联系我", "想我", "感情", "关系"]):
        return {
            "skill": "关系应事判断",
            "questions": [
                {
                    "question": "这段关系现在最卡住的是对方态度、现实阻碍，还是你要不要继续等？",
                    "options": ["对方态度", "能否复合", "现实阻碍", "还要不要等"],
                },
                {
                    "question": "你更想看短期有没有转机，还是看这段关系长期能不能稳定？",
                    "options": ["短期转机", "长期稳定", "对方心理", "行动建议"],
                },
            ],
        }
    if any(k in text for k in ["老板", "创业", "做生意", "开公司", "合伙人", "管理者", "领导"]):
        return {
            "skill": "事业主导力判断",
            "questions": [
                {
                    "question": "你问“适合当老板”，更偏向想看自己有没有老板命，还是眼前有没有创业/做生意的时机？",
                    "options": ["有没有老板命", "现在适不适合创业", "适合单干还是合伙", "想看长期事业格局"],
                },
                {
                    "question": "你现在处在什么阶段？不同阶段会影响择法。",
                    "options": ["还在想法阶段", "已有项目", "准备离职创业", "已经在经营", "正在找合伙人"],
                },
                {
                    "question": "你更担心哪一块？",
                    "options": ["赚钱能力", "管理能力", "抗压风险", "合伙关系", "行业方向"],
                },
            ],
        }
    if any(k in text for k in ["跳槽", "工作", "事业", "职业", "项目", "合作", "投资"]):
        return {
            "skill": "事业决策择法",
            "questions": [
                {
                    "question": "你更想判断这件事能不能成，还是判断哪条路更适合你？",
                    "options": ["能不能成", "哪条路适合", "现在时机", "风险在哪里"],
                },
                {
                    "question": "这件事现在是刚有想法、已经推进，还是马上要做决定？",
                    "options": ["刚有想法", "已经推进", "马上决定", "已经卡住"],
                },
            ],
        }
    if any(k in text for k in ["财运", "赚钱", "收入", "副业", "生意", "开业"]):
        return {
            "skill": "财运机会判断",
            "questions": [
                {
                    "question": "你更在意短期机会、长期财运，还是某个具体生意能不能做？",
                    "options": ["短期机会", "长期财运", "具体生意", "开业择日"],
                },
                {
                    "question": "这笔钱更像工作收入、投资收益，还是经营生意？",
                    "options": ["工作收入", "投资收益", "经营生意", "还不确定"],
                },
            ],
        }
    if any(k in text for k in ["结婚", "婚姻", "正缘", "姻缘", "对象", "伴侣"]):
        return {
            "skill": "婚恋阶段判断",
            "questions": [
                {
                    "question": "你更想看缘分出现时间、关系稳定度，还是这段关系最终走向？",
                    "options": ["出现时间", "稳定度", "最终走向", "相处风险"],
                },
                {
                    "question": "目前是单身、暧昧、恋爱中，还是已经进入婚姻议题？",
                    "options": ["单身", "暧昧", "恋爱中", "婚姻议题"],
                },
            ],
        }
    if any(k in text for k in ["哪天", "吉日", "择日", "搬家", "签约", "出行", "动土", "装修"]):
        return {
            "skill": "择日择时",
            "questions": [
                {
                    "question": "这件事有没有已经定好的时间范围？",
                    "options": ["已有时间范围", "还没定日期", "只看最近", "要避风险"],
                }
            ],
        }
    return {
        "skill": "综合问事择法",
        "questions": [
            {
                "question": "这件事你最想先知道结果、原因、时机，还是下一步怎么做？",
                "options": ["看结果", "看原因", "看时机", "看行动建议"],
            },
            {
                "question": "它现在处在刚开始、推进中、卡住，还是快要做决定的阶段？",
                "options": ["刚开始", "推进中", "卡住", "快要决定"],
            },
        ],
    }


def build_question_guidance(question, messages=None, model_id="basic", reading_mode="standard", profile_count=1):
    base_question = str(question or "").strip()
    clean_messages = []
    for item in messages or []:
        if not isinstance(item, dict):
            continue
        role = item.get("role")
        content = str(item.get("content") or "").strip()
        if role in ["assistant", "user"] and content:
            clean_messages.append({"role": role, "content": content[:240]})

    intent = _question_intent(base_question)
    user_replies = [item["content"] for item in clean_messages if item["role"] == "user"]
    questions = intent.get("questions") or [{"question": intent.get("question", "你更想看哪一层答案？"), "options": intent.get("options", [])}]
    if len(user_replies) < len(questions):
        current = questions[len(user_replies)]
        return {
            "status": "ask",
            "skill": intent["skill"],
            "assistant_message": "我先按「{}」来理解。{}".format(intent["skill"], current.get("question", "")),
            "options": current.get("options", []),
            "round": len(user_replies) + 1,
            "round_total": len(questions),
        }

    final_question = "；".join([base_question] + user_replies)
    tools, reason = recommend_tool_models(final_question)
    needs_profile = any(item.get("needs_profile") for item in COMPREHENSIVE_TOOL_MODELS if item["id"] in tools)
    return {
        "status": "recommend",
        "skill": intent["skill"],
        "final_question": final_question,
        "tool_models": tools,
        "needs_profile": needs_profile,
        "reason": "已按「{}」理解你的问题。{}".format(intent["skill"], reason),
        "estimated_cost": calculate_cost(model_id, tools, is_followup=False, profile_count=profile_count, reading_mode=reading_mode),
    }


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


def _birth_time_parts(value):
    digits = ''.join(ch for ch in str(value or '') if ch.isdigit())
    parts = {}
    if len(digits) >= 4:
        parts["birth_year"] = digits[:4]
    if len(digits) >= 6:
        parts["birth_month"] = digits[4:6]
    if len(digits) >= 8:
        parts["birth_day"] = digits[6:8]
    if len(digits) >= 10:
        parts["birth_hour"] = digits[8:10]
    if len(digits) >= 12:
        parts["birth_minute"] = digits[10:12]
    return parts


def _normalise_pillar_value(value):
    if isinstance(value, dict):
        return value.get("gan_zhi") or ((value.get("gan") or "") + (value.get("zhi") or ""))
    return value


def _extract_four_pillars(meta):
    if not isinstance(meta, dict):
        return {}
    four_pillars = meta.get("four_pillars") or meta.get("fourPillars") or {}
    if not isinstance(four_pillars, dict):
        return {}
    return {
        key: _normalise_pillar_value(four_pillars.get(key))
        for key in ("year", "month", "day", "hour")
        if four_pillars.get(key)
    }


def _split_ganzhi(value):
    text = str(value or "")
    if len(text) >= 2:
        return text[0], text[1]
    return "", ""


def _build_user_chart_context(profile):
    if isinstance(profile, list):
        return {"profiles": [_build_user_chart_context(item) for item in profile if isinstance(item, dict)]}
    if not isinstance(profile, dict):
        return {}
    meta = profile.get("meta") if isinstance(profile.get("meta"), dict) else {}
    birth_time = profile.get("birth_time") or profile.get("birthTime") or ""
    birth_parts = _birth_time_parts(birth_time)
    four_pillars = _extract_four_pillars(meta)
    birth_year_pillar = four_pillars.get("year") or meta.get("pillars", "")[:2]
    birth_year_gan, birth_year_zhi = _split_ganzhi(birth_year_pillar)
    context = {
        "profile_id": profile.get("id"),
        "name": profile.get("name") or "未命名",
        "gender": profile.get("gender") or meta.get("gender") or "",
        "relationship": profile.get("profile_type") or profile.get("profileType") or "self",
        "source": profile.get("source") or "manual",
        "source_record_id": profile.get("source_record_id"),
        "birth_input": {
            "calendar": profile.get("cal_type") or profile.get("calType") or "公历",
            "birth_time_raw": birth_time,
            **birth_parts,
            "birth_addr": profile.get("birth_addr") or profile.get("birthAddr") or "",
        },
        "qimen_relevant_user_inputs": {
            "birth_year": birth_parts.get("birth_year") or "",
            "birth_year_pillar": birth_year_pillar or "",
            "birth_year_gan": birth_year_gan,
            "birth_year_zhi": birth_year_zhi,
            "year_ming_reference": birth_year_pillar or birth_parts.get("birth_year") or "",
        },
        "location_and_time_options": {
            "birth_lng": meta.get("birthLng") or meta.get("lng") or meta.get("longitude"),
            "birth_lat": meta.get("birthLat") or meta.get("lat") or meta.get("latitude"),
            "use_true_solar_time": meta.get("useSolarTime", True),
            "is_dst": bool(meta.get("isDst", False)),
            "night_zi_mode": meta.get("nightZiMode") or meta.get("night_zi_mode") or "",
            "is_leap_month": bool(meta.get("isLeapMonth", False)),
        },
        "birth_conversion": {
            "birth_solar": meta.get("birth_solar") or meta.get("birthSolar") or "",
            "birth_lunar": meta.get("birth_lunar") or meta.get("birthLunar") or "",
            "sizi_pillars": meta.get("siziPillars") or meta.get("sizi_pillars") or "",
        },
        "birth_four_pillars": four_pillars,
        "birth_year_pillar": birth_year_pillar,
        "birth_day_master": meta.get("day_master") or meta.get("dayMaster") or "",
        "bazi_profile_meta_full": meta,
    }
    return context


def build_comprehensive_messages(question, profile, tool_models, paipan_context, history=None):
    system = """你是时安解忧屋的综合命理答疑助手。
你必须基于后端已经生成的排盘数据进行分析，不要自行编造出生信息、干支、宫位、星曜或卦象。
回答要求：
1. 先给出直接结论；
2. 分术数说明依据；
3. 汇总不同术数之间一致和冲突的地方；
4. 给出可执行建议；
5. 明确提示内容仅为民俗文化参考，不构成现实决策承诺。
排版要求：不要使用 Markdown 标记，不要输出星号、井号、反引号或 --- 分隔线；用自然段和中文小标题组织内容。
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
你会收到用户问题、用户出生命盘上下文、命盘档案和后端生成的完整术数盘面参数。
请以这些参数为事实来源，自主确定分析方法、用神取法和判断权重。
输出要求：
1. 围绕当前给出的一个术数盘面解读，不要跳到其他术数；
2. 结论和依据必须来自用户出生命盘上下文和当前盘面参数，不要自行编造出生信息、干支、宫位、星曜、卦象或牌面；
3. 可以按你的专业判断选择表达结构，但需要让用户看懂关键依据和行动建议；
4. 不要逐字段复述 JSON，也不要输出 snake_case 内部键名，八字关系字段改用中文术语，例如 zhi_liu_chong 说成“地支六冲”。
5. 不要使用 Markdown 标记，不要输出星号、井号、反引号或 --- 分隔线；用自然段和中文小标题组织内容。
"""
    user_chart_context = _build_user_chart_context(profile)
    messages = [{"role": "system", "content": system}]
    for item in history or []:
        if item.get("role") in ("user", "assistant"):
            messages.append({"role": item["role"], "content": str(item.get("content", ""))[:2000]})
    messages.append({
        "role": "user",
        "content": "用户问题：%s\n\n当前术数：%s\n\n用户出生命盘上下文：\n%s\n\n命盘档案原始数据：\n%s\n\n当前术数盘面完整数据：\n%s" % (
            question,
            tool_names.get(tool, tool),
            json.dumps(user_chart_context, ensure_ascii=False, indent=2),
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
排版要求：不要使用 Markdown 标记，不要输出星号、井号、反引号或 --- 分隔线；用自然段和中文小标题组织内容。
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
