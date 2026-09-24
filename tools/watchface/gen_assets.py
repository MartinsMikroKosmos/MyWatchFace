"""Generates the bitmap assets for the "Aurora" (left) watch face design."""
import math
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../watchface/src/main/res/drawable/")
S = 450


def glow(img, cx, cy, radius, color, strength):
    y, x = np.mgrid[0:S, 0:S].astype(np.float32)
    d2 = ((x - cx) ** 2 + (y - cy) ** 2) / (radius ** 2)
    g = np.exp(-d2)[..., None] * strength
    return img + g * np.array(color, dtype=np.float32)[None, None, :]


def background():
    y, x = np.mgrid[0:S, 0:S].astype(np.float32)
    r = np.sqrt((x - S / 2) ** 2 + (y - S / 2) ** 2) / (S / 2)
    base = np.zeros((S, S, 3), np.float32)
    inner = np.array([8, 9, 18], np.float32)
    outer = np.array([16, 16, 34], np.float32)
    base += inner + (outer - inner) * np.clip(r, 0, 1)[..., None] ** 1.6

    base = glow(base, -20, 200, 105, (30, 140, 255), 0.70)
    base = glow(base, 30, 340, 80, (40, 200, 255), 0.25)
    base = glow(base, 430, 60, 120, (150, 60, 230), 0.50)
    base = glow(base, 480, 290, 105, (255, 110, 40), 0.65)
    base = glow(base, 330, 470, 100, (200, 50, 150), 0.30)
    base = glow(base, 110, 10, 90, (90, 60, 200), 0.20)

    # Darken the centre so text stays readable.
    vign = np.clip(1.0 - np.exp(-((r / 0.70) ** 4)) * 0.6, 0, 1)
    base *= vign[..., None]

    img = Image.fromarray(np.clip(base, 0, 255).astype(np.uint8), "RGB").convert("RGBA")

    # Faint dot grid, fading towards the centre.
    dots = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    dd = ImageDraw.Draw(dots)
    for gy in range(0, S, 9):
        for gx in range(0, S, 9):
            rr = math.hypot(gx - S / 2, gy - S / 2) / (S / 2)
            a = int(max(0.0, rr - 0.45) * 60)
            if a > 0:
                dd.point((gx, gy), fill=(160, 170, 255, a))
    img = Image.alpha_composite(img, dots)

    # Geometric glow lines (chevrons) on left and right edges, drawn at 4x.
    k = 4
    lines = Image.new("RGBA", (S * k, S * k), (0, 0, 0, 0))
    ld = ImageDraw.Draw(lines)

    def poly(pts, col, w=1):
        ld.line([(px * k, py * k) for px, py in pts], fill=col, width=w * k, joint="curve")

    poly([(70, 120), (28, 200), (70, 280)], (80, 190, 255, 150))
    poly([(58, 150), (38, 200), (58, 250)], (80, 190, 255, 90))
    poly([(20, 300), (60, 340), (30, 380)], (170, 90, 255, 110))
    poly([(380, 120), (422, 200), (380, 280)], (255, 140, 70, 150))
    poly([(392, 150), (412, 200), (392, 250)], (255, 140, 70, 90))
    poly([(330, 40), (400, 80), (440, 150)], (180, 100, 255, 110))
    poly([(430, 300), (395, 345), (425, 385)], (255, 110, 60, 110))
    lines = lines.resize((S, S), Image.LANCZOS)
    blur = lines.filter(ImageFilter.GaussianBlur(3))
    img = Image.alpha_composite(img, blur)
    img = Image.alpha_composite(img, lines)

    # Divider lines that fade out at both ends.
    div = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    for yy, x0, x1 in ((111, 95, 355), (279, 80, 370)):
        for xx in range(x0, x1):
            t = (xx - x0) / (x1 - x0)
            a = int(math.sin(t * math.pi) ** 0.7 * 55)
            div.putpixel((xx, yy), (200, 205, 255, a))
    img = Image.alpha_composite(img, div)

    # Round crop (outside is black anyway on device).
    mask = Image.new("L", (S * k, S * k), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, S * k - 1, S * k - 1), fill=255)
    mask = mask.resize((S, S), Image.LANCZOS)
    out = Image.new("RGBA", (S, S), (0, 0, 0, 255))
    out.paste(img, (0, 0), mask)
    out.convert("RGB").save(OUT + "bg_aurora.png", optimize=True)


# ---------- Icons (drawn at 8x, downsampled) ----------
K = 8


def canvas(w, h):
    im = Image.new("RGBA", (w * K, h * K), (0, 0, 0, 0))
    return im, ImageDraw.Draw(im)


def save(im, w, h, name):
    im.resize((w * 2, h * 2), Image.LANCZOS).save(OUT + name + ".png")


def sc(v):
    return [c * K for c in v]


def sun(d, cx, cy, r, col=(255, 196, 40, 255), rays=True):
    if rays:
        for i in range(8):
            a = i * math.pi / 4
            x0, y0 = cx + math.cos(a) * r * 1.45, cy + math.sin(a) * r * 1.45
            x1, y1 = cx + math.cos(a) * r * 1.9, cy + math.sin(a) * r * 1.9
            d.line(sc((x0, y0, x1, y1)), fill=col, width=int(r * 0.32 * K))
    d.ellipse(sc((cx - r, cy - r, cx + r, cy + r)), fill=col)


def moon(im, cx, cy, r, col=(230, 225, 255, 255)):
    d = ImageDraw.Draw(im)
    d.ellipse(sc((cx - r, cy - r, cx + r, cy + r)), fill=col)
    d.ellipse(sc((cx - r * 0.35, cy - r * 1.15, cx + r * 1.45, cy + r * 0.65)), fill=(0, 0, 0, 0))


def cloud(d, x, y, w, col=(236, 240, 248, 255)):
    h = w * 0.55
    d.ellipse(sc((x, y + h * 0.35, x + w * 0.45, y + h)), fill=col)
    d.ellipse(sc((x + w * 0.18, y, x + w * 0.72, y + h * 0.9)), fill=col)
    d.ellipse(sc((x + w * 0.5, y + h * 0.25, x + w, y + h)), fill=col)
    d.rectangle(sc((x + w * 0.22, y + h * 0.6, x + w * 0.8, y + h)), fill=col)


def weather_icons():
    n = 48
    # sunny
    im, d = canvas(n, n); sun(d, 24, 24, 9); save(im, n, n, "wx_sun")
    # clear night
    im, d = canvas(n, n); moon(im, 24, 24, 13); save(im, n, n, "wx_moon")
    # partly cloudy day
    im, d = canvas(n, n); sun(d, 18, 17, 7.5); cloud(d, 12, 20, 33); save(im, n, n, "wx_partly_day")
    # partly cloudy night
    im, d = canvas(n, n); moon(im, 17, 16, 10); d = ImageDraw.Draw(im); cloud(d, 12, 20, 33)
    save(im, n, n, "wx_partly_night")
    # cloudy
    im, d = canvas(n, n); cloud(d, 18, 8, 26, (150, 158, 178, 255)); cloud(d, 5, 16, 36); save(im, n, n, "wx_cloud")
    # rain
    im, d = canvas(n, n); cloud(d, 6, 5, 36)
    for i, x in enumerate((14, 23, 32)):
        d.line(sc((x, 30, x - 3, 40)), fill=(90, 170, 255, 255), width=int(2.6 * K))
    save(im, n, n, "wx_rain")
    # snow
    im, d = canvas(n, n); cloud(d, 6, 5, 36)
    for x, y in ((14, 33), (24, 38), (34, 33)):
        d.ellipse(sc((x - 2.5, y - 2.5, x + 2.5, y + 2.5)), fill=(220, 240, 255, 255))
    save(im, n, n, "wx_snow")
    # thunder
    im, d = canvas(n, n); cloud(d, 6, 5, 36, (170, 176, 196, 255))
    d.polygon(sc((25, 26, 18, 37, 23, 37, 20, 45, 30, 33, 25, 33, 28, 26)), fill=(255, 205, 50, 255))
    save(im, n, n, "wx_storm")
    # fog
    im, d = canvas(n, n)
    for i, (x0, x1) in enumerate(((10, 38), (6, 34), (12, 40), (8, 30))):
        y = 14 + i * 7
        d.line(sc((x0, y, x1, y)), fill=(200, 206, 220, 255), width=int(3 * K))
    save(im, n, n, "wx_fog")
    # wind
    im, d = canvas(n, n)
    col = (200, 220, 240, 255)
    d.line(sc((6, 18, 30, 18)), fill=col, width=int(3 * K))
    d.arc(sc((25, 8, 35, 18)), 180, 90 + 360, fill=col, width=int(3 * K))
    d.line(sc((6, 27, 38, 27)), fill=col, width=int(3 * K))
    d.line(sc((6, 36, 26, 36)), fill=col, width=int(3 * K))
    d.arc(sc((21, 36, 31, 46)), 270, 180, fill=col, width=int(3 * K))
    save(im, n, n, "wx_wind")


def small_icons():
    # heart with pulse line
    n = 28
    im, d = canvas(n, n)
    red = (255, 72, 88, 255)
    d.ellipse(sc((2, 4, 15, 17)), fill=red)
    d.ellipse(sc((13, 4, 26, 17)), fill=red)
    d.polygon(sc((2.6, 12, 25.4, 12, 14, 25)), fill=red)
    d.line(sc((3, 13, 9, 13, 11.5, 8.5, 15, 18, 17.5, 11, 19, 13, 25, 13)),
           fill=(40, 10, 20, 255), width=int(2 * K), joint="curve")
    save(im, n, n, "ic_heart")

    # sneaker (steps)
    n = 22
    im, d = canvas(n, n)
    g = (60, 214, 120, 255)
    d.polygon(sc((3, 6, 9, 6, 11, 11, 18, 13, 20, 16, 20, 18, 3, 18)), fill=g)
    d.line(sc((7, 9, 10, 8.5)), fill=(20, 60, 35, 255), width=int(1.3 * K))
    d.line(sc((8, 12, 11, 11.5)), fill=(20, 60, 35, 255), width=int(1.3 * K))
    save(im, n, n, "ic_steps")

    # activity: circular arrow with flame dot
    im, d = canvas(n, n)
    o = (255, 140, 60, 255)
    d.arc(sc((3, 3, 19, 19)), 300, 240 + 360, fill=o, width=int(2 * K))
    d.polygon(sc((14.5, 1.5, 19.5, 4.5, 14.5, 7.5)), fill=o)
    d.ellipse(sc((8, 8, 14, 14)), fill=o)
    save(im, n, n, "ic_activity")

    # location pin
    im, d = canvas(n, n)
    b = (80, 150, 255, 255)
    d.ellipse(sc((5, 2, 17, 14)), fill=b)
    d.polygon(sc((5.6, 10.5, 16.4, 10.5, 11, 20)), fill=b)
    d.ellipse(sc((8.5, 5.5, 13.5, 10.5)), fill=(0, 0, 0, 0))
    save(im, n, n, "ic_pin")

    # message bubble
    im, d = canvas(n, n)
    w = (215, 220, 235, 255)
    d.rounded_rectangle(sc((2, 3, 20, 16)), radius=3 * K, fill=w)
    d.polygon(sc((5, 15, 5, 20, 10, 15)), fill=w)
    for yy, x1 in ((7, 16), (10.5, 13)):
        d.line(sc((6, yy, x1, yy)), fill=(30, 30, 45, 255), width=int(1.6 * K))
    save(im, n, n, "ic_message")

    # small battery
    n = 16
    im, d = canvas(n, 24)
    gcol = (160, 165, 180, 255)
    d.rounded_rectangle(sc((5, 1, 11, 4)), radius=1 * K, fill=gcol)
    d.rounded_rectangle(sc((2, 3, 14, 23)), radius=2.5 * K, fill=gcol)
    save(im, n, 24, "ic_battery")

    # plus (empty complication)
    n = 22
    im, d = canvas(n, n)
    c = (200, 205, 220, 255)
    d.line(sc((11, 4, 11, 18)), fill=c, width=int(2.4 * K))
    d.line(sc((4, 11, 18, 11)), fill=c, width=int(2.4 * K))
    save(im, n, n, "ic_plus")


if __name__ == "__main__":
    background()
    weather_icons()
    small_icons()
    print("done")
