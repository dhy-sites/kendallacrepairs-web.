"""Generador de carteles 1080x1080 para redes de Kendall AC Repairs.

Uso:
  python3 cartel.py salida.png "TITULAR" "línea 1|línea 2" "Llama ahora"
  (en inglés: ... "Call now")

Requiere Pillow y las fuentes en ./fonts/ (PlusJakartaSans.ttf y DMSans.ttf).
Si no están, se descargan del repo google/fonts.
"""
import math, os, sys, urllib.request
from PIL import Image, ImageDraw, ImageFont

NAVY, ORANGE, WHITE, SKY, FOOT = "#0b2545", "#f26b1d", "#ffffff", "#8fb8de", "#071a33"
PHONE = "(305) 363-7976"
BRAND = "Kendall AC Repairs  ·  Kendall, FL"
FONTS = {
    "fonts/PlusJakartaSans.ttf": "https://raw.githubusercontent.com/google/fonts/main/ofl/plusjakartasans/PlusJakartaSans%5Bwght%5D.ttf",
    "fonts/DMSans.ttf": "https://raw.githubusercontent.com/google/fonts/main/ofl/dmsans/DMSans%5Bopsz,wght%5D.ttf",
}
F_JAK, F_DM = list(FONTS)


def ensure_fonts():
    os.makedirs("fonts", exist_ok=True)
    for path, url in FONTS.items():
        if not os.path.exists(path):
            urllib.request.urlretrieve(url, path)


def font(path, size, weight):
    f = ImageFont.truetype(path, size)
    try:
        f.set_variation_by_name(weight)
    except Exception:
        pass
    return f


def fit(d, text, path, weight, size, max_w):
    f = font(path, size, weight)
    while d.textlength(text, font=f) > max_w and size > 40:
        size -= 4
        f = font(path, size, weight)
    return f


def center(d, y, text, f, fill):
    d.text(((1080 - d.textlength(text, font=f)) / 2, y), text, font=f, fill=fill)


def make(out, headline, sub_lines, cta):
    ensure_fonts()
    im = Image.new("RGB", (1080, 1080), NAVY)
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, 1080, 18], fill=ORANGE)
    cx, cy, r = 540, 215, 70
    for ang in (0, 60, 120):
        dx, dy = r * math.cos(math.radians(ang)), r * math.sin(math.radians(ang))
        d.line([cx - dx, cy - dy, cx + dx, cy + dy], fill=SKY, width=10)
    d.ellipse([cx - 14, cy - 14, cx + 14, cy + 14], fill=NAVY, outline=SKY, width=8)
    hf = fit(d, headline, F_JAK, "ExtraBold", 150, 960)
    center(d, 320 + (150 - hf.size) // 2, headline, hf, WHITE)
    y = 510
    for line in sub_lines[:3]:
        center(d, y, line, fit(d, line, F_DM, "Medium", 50, 940), SKY)
        y += 66
    center(d, 690, cta, font(F_DM, 40, "Medium"), WHITE)
    d.rounded_rectangle([110, 750, 970, 905], radius=28, fill=ORANGE)
    center(d, 765, PHONE, font(F_JAK, 104, "ExtraBold"), WHITE)
    d.rectangle([0, 980, 1080, 1080], fill=FOOT)
    center(d, 1008, BRAND, font(F_DM, 36, "Medium"), WHITE)
    im.save(out, "PNG", optimize=True)
    print("ok", out)


if __name__ == "__main__":
    out, headline, sub, cta = sys.argv[1:5]
    make(out, headline, sub.split("|"), cta)
