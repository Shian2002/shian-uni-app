"""硅基流动 (SiliconFlow) DeepSeek API 调用模块

提供塔罗牌 AI 解读能力，支持流式输出 (SSE)。
"""

from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()

_SILICONFLOW_API_KEY = os.getenv("SILICONFLOW_API_KEY", "")
_SILICONFLOW_BASE_URL = os.getenv("SILICONFLOW_BASE_URL", "https://api.siliconflow.cn/v1")
MODEL = os.getenv("DEEPSEEK_MODEL_NORMAL", "deepseek-ai/DeepSeek-V3")

_client = None
_model_clients = {}

def _get_client():
    global _client
    if _client is None and _SILICONFLOW_API_KEY:
        _client = OpenAI(
            api_key=_SILICONFLOW_API_KEY,
            base_url=_SILICONFLOW_BASE_URL,
        )
    return _client


def _first_env(*names):
    for name in names:
        value = os.getenv(name, "")
        if value:
            return value
    return ""


def _model_config(model_id):
    """返回首页综合模型的 OpenAI 兼容调用配置。"""
    selected = model_id or "basic"
    if selected == "expert":
        return {
            "provider": "zhipu",
            "api_key": _first_env("EXPERT_AI_API_KEY", "ZAI_API_KEY", "ZHIPU_API_KEY"),
            "base_url": _first_env("EXPERT_AI_BASE_URL", "ZAI_BASE_URL", "ZHIPU_BASE_URL") or "https://open.bigmodel.cn/api/paas/v4/",
            "model": _first_env("EXPERT_AI_MODEL", "ZAI_MODEL_EXPERT", "ZHIPU_MODEL_EXPERT") or "glm-5.1",
            "supports_thinking": True,
            "thinking_type": "enabled",
        }
    if selected == "advanced":
        return {
            "provider": "zhipu",
            "api_key": _first_env("ADVANCED_AI_API_KEY", "ZAI_API_KEY", "ZHIPU_API_KEY"),
            "base_url": _first_env("ADVANCED_AI_BASE_URL", "ZAI_BASE_URL", "ZHIPU_BASE_URL") or "https://open.bigmodel.cn/api/paas/v4/",
            "model": _first_env("ADVANCED_AI_MODEL", "ZAI_MODEL_ADVANCED", "ZAI_MODEL_EXPERT", "ZHIPU_MODEL_EXPERT") or "glm-5.1",
            "supports_thinking": True,
            "thinking_type": "disabled",
        }
    return {
        "provider": "zhipu" if _first_env("BASIC_AI_API_KEY", "ZAI_API_KEY", "ZHIPU_API_KEY") else "siliconflow",
        "api_key": _first_env("BASIC_AI_API_KEY", "ZAI_API_KEY", "ZHIPU_API_KEY", "SILICONFLOW_API_KEY"),
        "base_url": _first_env("BASIC_AI_BASE_URL", "ZAI_BASE_URL", "ZHIPU_BASE_URL", "SILICONFLOW_BASE_URL") or "https://open.bigmodel.cn/api/paas/v4/",
        "model": _first_env("BASIC_AI_MODEL", "ZAI_MODEL_BASIC", "ZAI_MODEL_EXPERT", "ZHIPU_MODEL_EXPERT", "DEEPSEEK_MODEL_NORMAL") or "glm-5.1",
        "supports_thinking": bool(_first_env("BASIC_AI_API_KEY", "ZAI_API_KEY", "ZHIPU_API_KEY")),
        "thinking_type": "disabled",
    }


def _get_model_client(config):
    key = (config["provider"], config["base_url"], config["api_key"])
    if not config["api_key"]:
        return None
    if key not in _model_clients:
        _model_clients[key] = OpenAI(api_key=config["api_key"], base_url=config["base_url"])
    return _model_clients[key]


TAROT_SYSTEM_PROMPT = """你是一位资深塔罗牌解读师，精通韦特塔罗、占星和符号学。
请根据用户的问题和抽到的塔罗牌阵，给出专业、温暖、有洞察力的解读。

你的回答应该包括：
1. **牌阵总览**：概述整个牌阵的基调、元素分布（火/水/风/土）、大阿卡纳占比
2. **逐张解读**：结合牌位含义，解读每张牌的正逆位含义及其在当前位置的象征
3. **综合解读**：将所有牌位串联起来，形成完整的故事线
4. **行动建议**：给出 2-3 条具体可执行的建议

要求：
- 语言温暖有力量，像朋友在对话，不要机械套话
- 结合用户的具体问题，避免泛泛而谈
- 用 markdown 组织，但不要太多标题层级
- 总字数 600-1200 字"""


def get_tarot_reading_stream(cards_info: list, user_question: str, spread_name: str):
    """流式调用 DeepSeek 进行塔罗牌解读

    Args:
        cards_info: [{name, name_en, position_name, position_meaning, is_reversed, type, element, keyword}]
        user_question: 琨户占卜问题
        spread_name: 牌阵名称

    Yields:
        str: 流式文本块
    """
    client = _get_client()
    if not client:
        yield None, "未配置 SILICONFLOW_API_KEY"
        return

    # 构建牌面信息文本
    cards_text = ""
    for i, c in enumerate(cards_info):
        orient = "逆位" if c.get("is_reversed") else "正位"
        cards_text += (
            f"第{i+1}张：【{c.get('name','')}】{orient} → 牌位：{c.get('position_name','')}（{c.get('position_meaning','')}）\n"
            f"  类型：{c.get('type','')} | 元素：{c.get('element','')} | 关键词：{c.get('keyword','')}\n\n"
        )

    user_msg = f"牌阵：{spread_name}\n我的问题：{user_question}\n\n抽到的牌：\n{cards_text}"

    messages = [
        {"role": "system", "content": TAROT_SYSTEM_PROMPT},
        {"role": "user", "content": user_msg}
    ]

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            temperature=0.8,
            max_tokens=2048,
            stream=True,
        )
        for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content, None
        yield None, None  # 完成信号

    except Exception as e:
        error_msg = str(e)
        if "401" in error_msg:
            yield None, "API Key 无效"
        elif "429" in error_msg:
            yield None, "请求太频繁，请稍后再试"
        else:
            yield None, f"AI 服务异常：{error_msg[:100]}"


def get_tarot_followup_stream(history: list, new_question: str):
    """多轮对话追问——带历史上下文"""
    client = _get_client()
    if not client:
        yield None, "未配置 SILICONFLOW_API_KEY"
        return

    messages = [{"role": "system", "content": TAROT_SYSTEM_PROMPT}]
    for h in history:
        messages.append({"role": h.get("role", "user"), "content": h.get("content", "")})
    messages.append({"role": "user", "content": new_question})

    try:
        response = client.chat.completions.create(
            model=MODEL, messages=messages, temperature=0.8, max_tokens=2048, stream=True
        )
        for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content, None
        yield None, None
    except Exception as e:
        error_msg = str(e)
        if "401" in error_msg:
            yield None, "API Key 无效"
        elif "429" in error_msg:
            yield None, "请求太频繁"
        else:
            yield None, f"AI 服务异常：{error_msg[:100]}"


MODEL_DEEP = os.getenv("DEEPSEEK_MODEL_DEEP", "deepseek-ai/DeepSeek-R1")

QIMEN_SYSTEM_PROMPT = """你是一位精通奇门遁甲的资深命理专家，擅长根据奇门遁甲盘面分析问题。
请根据用户提供的奇门排盘数据和问题，给出专业的奇门遁甲分析解读。

你的回答应该包括以下结构（markdown格式）：
1. **盘面概要**：说明当前的时辰、局数、值符值使
2. **用神分析**：根据用户问题选择对应的用神宫位，分析天盘地盘关系
3. **吉凶判断**：分析八门、九星、八神、天干等吉凶格局和组合
4. **建议指导**：给出针对性的建议和注意事项

要求：
- 语言通俗易懂，专业但不晦涩
- 用 markdown 标题和列表组织内容
- 避免笼统的套话，要结合具体盘面数据
- 字数控制在 800-1500 字"""


def get_qimen_reading(panel_info: str, question: str, is_deep: bool = False, system_prompt: str = None) -> dict:
    """调用 DeepSeek 进行奇门解盘（非流式，一次性返回完整结果）

    Args:
        panel_info: 排盘结果文本（由 _build_qimen_ask_prompt 构建的 markdown）
        question: 用户问题
        is_deep: 是否使用 DeepSeek-R1 深度分析
        system_prompt: 自定义系统提示词，默认使用 QIMEN_SYSTEM_PROMPT

    Returns:
        dict: { content, reasoning, model, error }
    """
    client = _get_client()
    if not client:
        return {"error": "未配置 SILICONFLOW_API_KEY", "content": "", "reasoning": None, "model": ""}

    model_name = MODEL_DEEP if is_deep else MODEL
    sp = system_prompt if system_prompt else QIMEN_SYSTEM_PROMPT

    messages = [
        {"role": "system", "content": sp},
        {"role": "user", "content": f"盘局信息：\n{panel_info}\n\n我的问题：{question}"}
    ]

    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=messages,
            temperature=0.7,
            max_tokens=4096,
            stream=False,
        )
        message = response.choices[0].message
        reasoning = getattr(message, 'reasoning_content', None)
        content = message.content or ""
        return {"reasoning": reasoning, "content": content, "model": model_name, "error": None}

    except Exception as e:
        error_msg = str(e)
        if "401" in error_msg:
            return {"error": "API Key 无效", "content": "", "reasoning": None, "model": ""}
        elif "429" in error_msg:
            return {"error": "请求太频繁，请稍后再试", "content": "", "reasoning": None, "model": ""}
        else:
            return {"error": f"API 调用失败：{error_msg[:200]}", "content": "", "reasoning": None, "model": ""}


def is_available() -> bool:
    """检查 SiliconFlow API 是否已配置"""
    return bool(_SILICONFLOW_API_KEY)


def get_reading_stream(messages: list, model_name: str = None, model_id: str = None, reading_mode: str = "standard"):
    """通用流式解读，供奇门/六爻/梅花/紫微/八字共用

    Args:
        messages: OpenAI 格式消息数组，调用方自行构建 system_prompt 和 user content
        model_name: 可选模型名，默认使用 MODEL

    Yields:
        (str, None): 流式文本块
        (None, None): 完成信号
        (None, str): 错误消息
    """
    if model_id:
        config = _model_config(model_id)
        client = _get_model_client(config)
        model = model_name or config["model"]
        missing_msg = "未配置 %s 模型 API Key" % config["provider"]
    else:
        client = _get_client()
        model = model_name or MODEL
        missing_msg = "未配置 SILICONFLOW_API_KEY"
    if not client:
        yield None, missing_msg
        return

    try:
        params = {
            "model": model,
            "messages": messages,
            "temperature": 0.8,
            "max_tokens": 4096,
            "stream": True,
        }
        if model_id and config.get("supports_thinking"):
            params["extra_body"] = {"thinking": {"type": config.get("thinking_type", "disabled")}}
        response = client.chat.completions.create(**params)
        for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content, None
        yield None, None  # 完成信号

    except Exception as e:
        error_msg = str(e)
        if "401" in error_msg:
            yield None, "API Key 无效"
        elif "429" in error_msg:
            yield None, "请求太频繁，请稍后再试"
        else:
            yield None, f"AI 服务异常：{error_msg[:100]}"


def get_chat_completion(messages: list, model_id: str = "basic", temperature: float = 0.3, max_tokens: int = 1200):
    """非流式通用模型调用，供低延迟结构化任务使用。"""
    config = _model_config(model_id)
    client = _get_model_client(config)
    if not client:
        return {"error": "未配置 %s 模型 API Key" % config["provider"], "content": "", "model": config["model"]}
    try:
        params = {
            "model": config["model"],
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False,
        }
        if config.get("supports_thinking"):
            params["extra_body"] = {"thinking": {"type": config.get("thinking_type", "disabled")}}
        response = client.chat.completions.create(**params)
        content = ""
        if response.choices and response.choices[0].message:
            content = response.choices[0].message.content or ""
        return {"content": content, "model": config["model"], "error": None}
    except Exception as e:
        return {"error": str(e), "content": "", "model": config["model"]}
