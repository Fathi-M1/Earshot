"""Brand name is a variable read from design/tokens.json; nothing hard-codes it."""

from earshot import brand


def test_brand_from_tokens():
    assert brand.name() == "earshot"
    assert brand.display_name() == "Earshot"


def test_colors_and_states():
    assert brand.color("forest") == "#1F3A24"
    assert brand.color("forest-deep") == "#12241A"
    tile = brand.state_tile("LISTENING")
    assert tile["word"] == "LISTENING"
    assert tile["shape"] == "circle"


def test_tokens_path_exists():
    assert brand.TOKENS_PATH.exists()
