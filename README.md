# Steganography in Python: hide text or an image inside an image

A small command-line tool that hides a secret **text message** or a whole **secret image** inside an ordinary-looking picture, and gets it back out.

I first built this as a college project. This version is a cleaned-up rewrite: it adds image-in-image hiding, a message header so it can tell whether an image actually contains a secret, PNG output, and tests.

## How it works

**Text in image (LSB):** every pixel has red, green and blue values from 0 to 255. The tool turns the message into bits and writes one bit into the last bit of each colour value. That changes each value by at most 1, which the eye can't see. A small header ("STG1" + message length) goes first, so reading stops at the right place.

**Image in image (4-bit):** the tool keeps the top 4 bits of the cover image and puts the top 4 bits of the secret image into the bottom 4 bits. You can still see the cover picture, and shifting those 4 bits back up recovers a slightly lower-quality copy of the secret.

**Why PNG only:** JPEG compression changes pixel values slightly, which destroys hidden bits. The tool refuses to save as .jpg.

| Mode | Capacity | What comes back |
|---|---|---|
| Text | about (width × height × 3) / 8 bytes, e.g. 1920×1080 ≈ 777 KB | The exact message, UTF-8 (Hindi, Kannada etc. work) |
| Image | One image the same size as the cover (resized if needed) | The secret with 16 colour levels per channel instead of 256 |

## Usage

~~~bash
pip install -r requirements.txt

# hide and read a message
python stego.py hide-text cover.png secret.png "Meet at 6 pm"
python stego.py reveal-text secret.png

# hide and extract an image
python stego.py hide-image cover.png hidden_photo.jpg out.png
python stego.py reveal-image out.png recovered.png
~~~

## Tests

~~~bash
python -m pytest -q
~~~

The tests cover the text round trip (including non-English text), that pixels change by at most 1, that the original image isn't modified, messages that are too long, images with no hidden message, the image round trip, saving and reloading through PNG, and refusing JPEG output.

## Limits

- This hides data; it doesn't encrypt it. Anyone who knows the method can read the message, so encrypt it first if it's sensitive.
- Resizing, cropping, filters or re-saving as JPEG (as most chat apps do) destroy the hidden data.

## Tech

Python · NumPy · Pillow · pytest
