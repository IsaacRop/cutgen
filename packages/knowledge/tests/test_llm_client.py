import os

import pytest

from cutgen_knowledge.llm.client import LLMConfig, render_input


def test_render_input_formats_sections():
    out = render_input({"niche": "games", "transcript": "oi tudo bem"})
    assert "## niche\ngames" in out
    assert "## transcript\noi tudo bem" in out


def test_render_input_json_dumps_structured_values():
    out = render_input({"words": [{"t": 0, "w": "oi"}]})
    assert '"t": 0' in out


def test_llm_config_defaults(monkeypatch):
    monkeypatch.setenv("CUTGEN_LLM_API_KEY", "sk-test-fake")
    monkeypatch.delenv("CUTGEN_LLM_MODEL_FAST", raising=False)
    config = LLMConfig.from_env()
    assert config.api_key == "sk-test-fake"
    assert config.base_url == "https://api.anthropic.com"
    assert config.model_heavy == "claude-opus-5"
    assert config.model_fast == "claude-haiku-4-5"


def test_llm_config_overrides(monkeypatch):
    monkeypatch.setenv("CUTGEN_LLM_API_KEY", "sk-test-fake")
    monkeypatch.setenv("CUTGEN_LLM_MODEL_FAST", "claude-sonnet-5")
    config = LLMConfig.from_env()
    assert config.model_fast == "claude-sonnet-5"


def test_llm_config_requires_api_key(monkeypatch):
    monkeypatch.delenv("CUTGEN_LLM_API_KEY", raising=False)
    with pytest.raises(KeyError):
        LLMConfig.from_env()
