import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import stego  # noqa: E402


def random_image(h=64, w=64, seed=0):
    return np.random.default_rng(seed).integers(0, 256, (h, w, 3), dtype=np.uint8)


def test_text_round_trip():
    cover = random_image()
    hidden = stego.hide_text(cover, "Meet at 6 pm - नमस्ते")
    assert stego.reveal_text(hidden) == "Meet at 6 pm - नमस्ते"


def test_text_change_is_tiny():
    cover = random_image()
    hidden = stego.hide_text(cover, "hello")
    assert np.max(np.abs(hidden.astype(int) - cover.astype(int))) <= 1


def test_cover_not_modified():
    cover = random_image()
    before = cover.copy()
    stego.hide_text(cover, "hello")
    assert np.array_equal(cover, before)


def test_message_too_long():
    with pytest.raises(ValueError):
        stego.hide_text(random_image(4, 4), "x" * 100)


def test_no_hidden_message():
    with pytest.raises(ValueError):
        stego.reveal_text(np.zeros((32, 32, 3), dtype=np.uint8))


def test_image_round_trip_is_close():
    cover, secret = random_image(seed=1), random_image(seed=2)
    recovered = stego.reveal_image(stego.hide_image(cover, secret))
    # only the top 4 bits of the secret survive, and they come back exactly
    assert np.max(np.abs(recovered.astype(int) - (secret & 0xF0).astype(int))) == 0


def test_png_round_trip(tmp_path):
    cover_path, out_path = tmp_path / "cover.png", tmp_path / "out.png"
    stego._save_png(random_image(), str(cover_path))
    assert stego.main(["hide-text", str(cover_path), str(out_path), "secret"]) == 0
    assert stego.reveal_text(stego._load_rgb(str(out_path))) == "secret"


def test_rejects_jpeg_output(tmp_path):
    with pytest.raises(ValueError):
        stego._save_png(random_image(), str(tmp_path / "out.jpg"))
