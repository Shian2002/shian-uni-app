import importlib
import os
import sys


def _load_service(monkeypatch):
    backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
    sys.path.insert(0, backend_dir)
    try:
        module = importlib.import_module("deepseek_service")
        return importlib.reload(module)
    finally:
        if sys.path and sys.path[0] == backend_dir:
            sys.path.pop(0)


class _FakeCompletions:
    def __init__(self, seen):
        self._seen = seen

    def create(self, **params):
        self._seen.append(params)
        return iter(())


class _FakeChat:
    def __init__(self, seen):
        self.completions = _FakeCompletions(seen)


class _FakeClient:
    def __init__(self, seen):
        self.chat = _FakeChat(seen)


def test_home_model_provider_mapping(monkeypatch):
    service = _load_service(monkeypatch)

    basic = service._model_config("basic")
    advanced = service._model_config("advanced")
    expert = service._model_config("expert")

    assert basic["provider"] == "zhipu"
    assert basic["model"] == "glm-5.1"
    assert basic["thinking_type"] == "disabled"

    assert advanced["provider"] == "zhipu"
    assert advanced["thinking_type"] == "disabled"

    assert expert["provider"] == "zhipu"
    assert expert["thinking_type"] == "enabled"


def test_home_model_thinking_flags_are_fixed_by_tier(monkeypatch):
    service = _load_service(monkeypatch)
    seen = []
    monkeypatch.setattr(service, "_get_model_client", lambda config: _FakeClient(seen))
    messages = [{"role": "user", "content": "测试"}]

    list(service.get_reading_stream(messages, model_id="advanced", reading_mode="deep"))
    list(service.get_reading_stream(messages, model_id="expert", reading_mode="concise"))
    list(service.get_reading_stream(messages, model_id="basic", reading_mode="deep"))

    assert seen[0]["extra_body"] == {"thinking": {"type": "disabled"}}
    assert seen[1]["extra_body"] == {"thinking": {"type": "enabled"}}
    assert seen[2]["extra_body"] == {"thinking": {"type": "disabled"}}
