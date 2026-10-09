"""Watch-chunk segmentation (02 §3.3: short rolling chunks for the lock screen)."""

from earshot import captions


def test_chunks_respect_chars_and_words():
    chunks = captions.chunk_for_watch(
        "one two three four five six seven eight", max_chars=28, max_words=6
    )
    assert all(len(c) <= 28 for c in chunks)
    assert all(len(c.split()) <= 6 for c in chunks)
    assert " ".join(chunks).split() == "one two three four five six seven eight".split()


def test_long_word_still_capped():
    chunks = captions.chunk_for_watch("supercalifragilisticexpialidocious", max_chars=28)
    assert all(len(c) <= 28 for c in chunks)


def test_clip_title():
    assert captions.clip_title("short line", 28) == "short line"
    long = "x" * 40
    out = captions.clip_title(long, 28)
    assert len(out) <= 28 and out.endswith("…")


def test_empty_returns_single_blank():
    assert captions.chunk_for_watch("") == [""]
