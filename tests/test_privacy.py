"""Privacy proof + translation script sanitizing (fix D)."""

import httpx
import respx

from earshot import llm, localclient, privacy


def test_proof_reports_zero_internet_after_local_call():
    localclient.reset_counters()
    with respx.mock:
        respx.post("http://127.0.0.1:11434/api/generate").mock(
            return_value=httpx.Response(200, json={"ok": True})
        )
        localclient.post_json("http://127.0.0.1:11434/api/generate", {"x": 1})
    p = privacy.proof()
    assert p["internet_bytes_sent"] == 0
    assert p["local_bytes_sent"] > 0
    assert p["internet_connections"] == 0  # our process opens nothing public in a test


def test_translation_strips_foreign_script():
    # Arabic translation that hallucinated CJK ("安娜") must be sanitized away.
    assert "安" not in llm._sanitize("مرحبا 安娜", "ar")
    assert llm._sanitize("مرحبا 安娜", "ar").startswith("مرحبا")


@respx.mock
def test_translate_rejects_mostly_foreign():
    respx.post("http://127.0.0.1:11434/api/chat").mock(
        return_value=httpx.Response(200, json={"message": {"content": '{"translation": "安娜娜娜"}'}})
    )
    # output is all CJK -> sanitized to nothing -> rejected (None -> caller keeps original)
    assert llm.translate("hello", "ar") is None
