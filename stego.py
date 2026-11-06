"""
stego.py - hide a text message or a whole image inside another image.

Two techniques:
  * Text in image  - LSB (least significant bit) encoding. Each bit of the message
    replaces the last bit of one colour channel, so the change is invisible.
  * Image in image - the top 4 bits of the secret image are stored in the bottom
    4 bits of the cover image.

Output is always saved as PNG, because PNG is lossless. JPEG compression would
change pixel values and destroy the hidden data.
"""

import argparse
import sys

import numpy as np
from PIL import Image

MAGIC = b"STG1"          # marks that an image really contains a hidden message
HEADER_BYTES = len(MAGIC) + 4  # magic + 4-byte message length


def _load_rgb(path):
    return np.array(Image.open(path).convert("RGB"), dtype=np.uint8)


def _save_png(array, path):
    if not path.lower().endswith(".png"):
        raise ValueError("Output must be a .png file (JPEG would destroy the hidden data).")
    Image.fromarray(array).save(path, format="PNG")


def capacity_bytes(cover):
    """How many message bytes fit in a cover image (1 bit per colour channel)."""
    return cover.size // 8 - HEADER_BYTES


# ---------- text in image ----------

def hide_text(cover, message):
    data = message.encode("utf-8")
    if len(data) > capacity_bytes(cover):
        raise ValueError(f"Message too long: {len(data)} bytes, image fits {capacity_bytes(cover)}.")
    payload = MAGIC + len(data).to_bytes(4, "big") + data
    bits = np.unpackbits(np.frombuffer(payload, dtype=np.uint8))

    flat = cover.flatten()  # copy, the original array is not changed
    flat[: bits.size] = (flat[: bits.size] & 0xFE) | bits
    return flat.reshape(cover.shape)


def reveal_text(stego):
    flat = stego.flatten()
    header = np.packbits(flat[: HEADER_BYTES * 8] & 1).tobytes()
    if header[: len(MAGIC)] != MAGIC:
        raise ValueError("No hidden message found in this image.")
    length = int.from_bytes(header[len(MAGIC):], "big")
    end = (HEADER_BYTES + length) * 8
    if end > flat.size:
        raise ValueError("Hidden message header is corrupted.")
    data = np.packbits(flat[HEADER_BYTES * 8 : end] & 1).tobytes()
    return data.decode("utf-8")


# ---------- image in image ----------

def hide_image(cover, secret):
    """Keep the top 4 bits of the cover and put the top 4 bits of the secret below them."""
    secret_img = Image.fromarray(secret).resize((cover.shape[1], cover.shape[0]))
    secret_resized = np.array(secret_img, dtype=np.uint8)
    return (cover & 0xF0) | (secret_resized >> 4)


def reveal_image(stego):
    """Shift the hidden 4 bits back up to get an approximate copy of the secret image."""
    return (stego & 0x0F) << 4


# ---------- command line ----------

def main(argv=None):
    parser = argparse.ArgumentParser(description="Hide text or an image inside an image.")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("hide-text", help="hide a text message")
    p.add_argument("cover"); p.add_argument("output"); p.add_argument("message")

    p = sub.add_parser("reveal-text", help="read a hidden text message")
    p.add_argument("image")

    p = sub.add_parser("hide-image", help="hide one image inside another")
    p.add_argument("cover"); p.add_argument("secret"); p.add_argument("output")

    p = sub.add_parser("reveal-image", help="extract a hidden image")
    p.add_argument("image"); p.add_argument("output")

    args = parser.parse_args(argv)
    try:
        if args.command == "hide-text":
            _save_png(hide_text(_load_rgb(args.cover), args.message), args.output)
            print(f"Message hidden in {args.output}")
        elif args.command == "reveal-text":
            print(reveal_text(_load_rgb(args.image)))
        elif args.command == "hide-image":
            _save_png(hide_image(_load_rgb(args.cover), _load_rgb(args.secret)), args.output)
            print(f"Image hidden in {args.output}")
        elif args.command == "reveal-image":
            _save_png(reveal_image(_load_rgb(args.image)), args.output)
            print(f"Hidden image saved to {args.output}")
    except (ValueError, FileNotFoundError) as err:
        print(f"Error: {err}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
