"""Recall helpers: cosine ranking + pack/unpack; graceful failure when the
embedder is unreachable (01 §3.7)."""

import tempfile

import httpx
import respx

from earshot import recall


def test_pack_unpack_roundtrip():
    vec = [0.1, -0.2, 0.3, 0.0]
    assert recall._unpack(recall._pack(vec)) == [round(v, 6) for v in [0.1, -0.2, 0.3, 0.0]] or \
        all(abs(a - b) < 1e-6 for a, b in zip(recall._unpack(recall._pack(vec)), vec))


def test_cosine():
    assert recall._cosine([1, 0], [1, 0]) == 1.0
    assert recall._cosine([1, 0], [0, 1]) == 0.0
    assert recall._cosine([1, 0], []) == -1.0


@respx.mock
def test_search_empty_when_embedder_down(monkeypatch, tmp_path):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    respx.post("http://127.0.0.1:11434/api/embed").mock(return_value=httpx.Response(500))
    respx.post("http://127.0.0.1:11434/api/embeddings").mock(return_value=httpx.Response(500))
    r = recall.Recall(session="t")
    r.add_line("some line")        # embed fails -> not stored
    assert r.count() == 0
    assert r.search("anything") == []
    r.close()
