"""localclient is the only HTTP client: it must refuse public hosts before any
socket opens (bytes-to-internet = 0 by construction) and count bytes on local
calls (01 §3.10, §10)."""

import httpx
import pytest
import respx

from earshot import localclient


def setup_function():
    localclient.reset_counters()


def test_accepts_loopback_and_private():
    assert localclient.is_local_host("127.0.0.1")
    assert localclient.is_local_host("localhost")
    assert localclient.is_local_host("10.0.0.5")
    assert localclient.is_local_host("172.20.10.1")  # hotspot gateway
    assert localclient.is_local_host("192.168.1.10")


def test_refuses_public_ip_literals():
    assert not localclient.is_local_host("8.8.8.8")
    assert not localclient.is_local_host("1.1.1.1")
    assert not localclient.is_local_host("")


def test_post_to_public_raises_and_sends_nothing():
    with pytest.raises(localclient.PublicHostRefused):
        localclient.post_json("http://1.1.1.1/api", {"x": 1})
    c = localclient.counters()
    assert c.bytes_sent == 0
    assert c.requests == 0


def test_get_public_host_refused():
    with pytest.raises(localclient.PublicHostRefused):
        localclient.get("https://example.com/")
    assert localclient.counters().bytes_sent == 0


@respx.mock
def test_local_call_counts_bytes():
    route = respx.post("http://127.0.0.1:11434/api/generate").mock(
        return_value=httpx.Response(200, json={"response": "ok", "eval_count": 3})
    )
    resp = localclient.post_json("http://127.0.0.1:11434/api/generate", {"model": "x", "prompt": "hi"})
    assert resp.status_code == 200
    assert route.called
    c = localclient.counters()
    assert c.bytes_sent > 0
    assert c.bytes_recv > 0
    assert c.requests == 1
