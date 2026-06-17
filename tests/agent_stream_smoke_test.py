import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_agent_stream_smoke_is_real_single_stream_and_wired():
    package_json = json.loads(read_text("package.json"))
    source = read_text("scripts/agent_stream_smoke.mjs")

    assert package_json["scripts"]["qa:agent:stream-smoke"] == "QA_BASE_URL=${QA_BASE_URL:-https://shianjieyouwu.com} node scripts/agent_stream_smoke.mjs"
    assert "/api/comprehensive/ask/stream" in source
    assert "QA_MOCK_AGENT_STREAM" not in source
    assert "tool_models: ['bazi']" in source
    assert "reading_mode: 'standard'" in source
    assert "profile_confirmed: true" in source
    assert "/api/csrf-token" in source
    assert "'X-CSRFToken': csrfToken" in source
    assert "Referer: `${baseUrl}/`" in source
    assert "rawText" in source
    assert "stream 未返回 done 事件" in source
    assert "测试账号没有可用每日轻量额度、积分或单术数额度" in source
    assert "afterAssets" in source
