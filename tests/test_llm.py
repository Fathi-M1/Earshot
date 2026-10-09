"""Local LLM helper: schema call + translation, all via localclient (loopback)."""

import httpx
import respx

from earshot import llm, localclient


def setup_function():
    localclient.reset_counters()


@respx.mock
def test_translate_returns_translation():
    respx.post("http://127.0.0.1:11434/api/chat").mock(
        return_value=httpx.Response(200, json={"message": {"content": '{"translation": "مرحبا"}'}})
    )
    out = llm.translate("hello", "ar")
    assert out == "مرحبا"
    assert localclient.counters().requests == 1


@respx.mock
def test_chat_json_none_on_bad_json():
    respx.post("http://127.0.0.1:11434/api/chat").mock(
        return_value=httpx.Response(200, json={"message": {"content": "not json"}})
    )
    assert llm.chat_json("m", "sys", "u", {"type": "object"}) is None


@respx.mock
def test_translate_none_on_error():
    respx.post("http://127.0.0.1:11434/api/chat").mock(return_value=httpx.Response(500))
    assert llm.translate("hello", "ar") is None
