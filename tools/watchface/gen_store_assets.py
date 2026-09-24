"""Generates the Google Play store graphics for the "Aurora" watch face.

Run from the project root:  python3 tools/watchface/gen_store_assets.py
Output: playstore/  (icon 512x512, feature graphic 1024x500, screenshot)
"""
import os

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
PREVIEW = os.path.join(HERE, "../../watchface/src/main/res/drawable/preview.png")
OUT = os.path.join(HERE, "../../playstore")
FONT = "/System/Library/Fonts/Avenir Next.ttc"

WHITE = (240, 242, 250)
ORANGE = (255, 150, 90)


def backdrop(w, h):
    """Dark night sky with blue, violet and orange aurora glows."""
    img = Image.new("RGBA", (w, h), (8, 8, 18, 255))
    for cx, cy, r, color in [
        (0.10, 0.20, 0.45, (40, 90, 220, 200)),
        (0.55, 0.95, 0.50, (150, 60, 200, 170)),
        (0.95, 0.60, 0.40, (255, 120, 70, 150)),
    ]:
        layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        rr = r * max(w, h)
        ImageDraw.Draw(layer).ellipse([cx * w - rr, cy * h - rr, cx * w + rr, cy * h + rr], fill=color)
        img.alpha_composite(layer.filter(ImageFilter.GaussianBlur(rr * 0.6)))
    return img


def round_face(size):
    """The preview cut to a circle, with transparent corners."""
    face = Image.open(PREVIEW).convert("RGBA").resize((size, size), Image.LANCZOS)
    mask = Image.new("L", (size * 4, size * 4), 0)
    ImageDraw.Draw(mask).ellipse([0, 0, size * 4 - 1, size * 4 - 1], fill=255)
    face.putalpha(mask.resize((size, size), Image.LANCZOS))
    return face


def paste_with_glow(canvas, face, x, y, blur=22):
    glow = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    glow.paste((120, 110, 255, 255), (x, y), face.split()[3].point(lambda a: a * 0.5))
    canvas.alpha_composite(glow.filter(ImageFilter.GaussianBlur(blur)))
    canvas.alpha_composite(face, (x, y))


def icon():
    img = backdrop(512, 512)
    paste_with_glow(img, round_face(430), 41, 41, blur=16)
    img.convert("RGB").save(os.path.join(OUT, "icon_512.png"))


def feature_graphic():
    w, h = 1024, 500
    img = backdrop(w, h)
    paste_with_glow(img, round_face(420), w - 420 - 70, (h - 420) // 2)

    d = ImageDraw.Draw(img)
    d.text((70, 150), "Aurora", font=ImageFont.truetype(FONT, 96, index=0), fill=WHITE)
    d.line([(74, 270), (330, 270)], fill=ORANGE, width=3)
    d.text((72, 294), "Wear OS Watch Face", font=ImageFont.truetype(FONT, 30, index=0), fill=ORANGE)
    img.convert("RGB").save(os.path.join(OUT, "feature_graphic_1024x500.png"))


def screenshot():
    # Play wants square Wear OS screenshots without a round mask
    Image.open(PREVIEW).convert("RGB").save(os.path.join(OUT, "screenshot_1.png"))


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    icon()
    feature_graphic()
    screenshot()
