"""Generador de carteles 1080x1080 para redes de Kendall AC Repairs.

Cartel simple (un solo cuadro con número):
  python3 cartel-redes.py simple salida.png "TITULAR" "línea 1|línea 2" "Llama ahora"

Carrusel de blog (3 láminas: pregunta / dato / cierre), crea salida-1.png, -2.png, -3.png:
  python3 cartel-redes.py carrusel salida "¿REPARAR O CAMBIAR?" \
      "Si tu equipo tiene más de 12 años|y la reparación pasa de $800...|casi siempre conviene cambiar" \
      "La guía completa está en el blog|Link en comentarios" "Llama ahora"
  (la lámina 2 admite hasta 4 líneas separadas con |; la lámina 3 admite 2)
  Añade "en" como último argumento para los rótulos en inglés.

Requiere Pillow y las fuentes en ./fonts/ (se descargan solas del repo google/fonts).
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


def fit(d, text, path, weight, size, max_w, min_size=40):
    f = font(path, size, weight)
    while d.textlength(text, font=f) > max_w and size > min_size:
        size -= 4
        f = font(path, size, weight)
    return f


def center(d, y, text, f, fill):
    d.text(((1080 - d.textlength(text, font=f)) / 2, y), text, font=f, fill=fill)


TEMA = os.environ.get("TEMA", "")  # "" o "halloween"
PURPLE = "#6b3fa0"


def pumpkin(d, cx, cy, r):
    d.ellipse([cx - r, cy - r * 0.8, cx + r, cy + r * 0.8], fill=ORANGE)
    for k in (-0.45, 0, 0.45):
        d.arc([cx + k * r - r * 0.55, cy - r * 0.8, cx + k * r + r * 0.55, cy + r * 0.8], 0, 360, fill="#d95a12", width=4)
    d.rectangle([cx - r * 0.08, cy - r * 1.05, cx + r * 0.08, cy - r * 0.7], fill="#2e7d32")
    e = r * 0.22
    d.polygon([(cx - r * 0.45, cy - r * 0.05), (cx - r * 0.2, cy - r * 0.05), (cx - r * 0.33, cy - r * 0.35)], fill=NAVY)
    d.polygon([(cx + r * 0.45, cy - r * 0.05), (cx + r * 0.2, cy - r * 0.05), (cx + r * 0.33, cy - r * 0.35)], fill=NAVY)
    d.polygon([(cx - r * 0.5, cy + r * 0.2), (cx + r * 0.5, cy + r * 0.2), (cx + r * 0.3, cy + r * 0.5), (cx - r * 0.3, cy + r * 0.5)], fill=NAVY)
    d.rectangle([cx - r * 0.1, cy + r * 0.2, cx + r * 0.1, cy + r * 0.32], fill=ORANGE)


def bat(d, cx, cy, w):
    h = w * 0.35
    d.polygon([(cx - w / 2, cy - h * 0.3), (cx - w * 0.25, cy - h), (cx - w * 0.08, cy - h * 0.4), (cx, cy - h * 0.6),
               (cx + w * 0.08, cy - h * 0.4), (cx + w * 0.25, cy - h), (cx + w / 2, cy - h * 0.3),
               (cx + w * 0.3, cy), (cx + w * 0.15, cy + h * 0.3), (cx, cy + h * 0.1),
               (cx - w * 0.15, cy + h * 0.3), (cx - w * 0.3, cy)], fill=PURPLE)


def base_canvas():
    im = Image.new("RGB", (1080, 1080), NAVY)
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, 1080, 18], fill=ORANGE)
    if TEMA == "halloween":
        d.rectangle([0, 18, 1080, 30], fill=PURPLE)
        bat(d, 150, 110, 120)
        bat(d, 930, 90, 90)
        bat(d, 980, 300, 70)
        pumpkin(d, 1018, 938, 38)
    return im, d


def snowflake(d, cx=540, cy=215, r=70):
    for ang in (0, 60, 120):
        dx, dy = r * math.cos(math.radians(ang)), r * math.sin(math.radians(ang))
        d.line([cx - dx, cy - dy, cx + dx, cy + dy], fill=SKY, width=10)
    d.ellipse([cx - 14, cy - 14, cx + 14, cy + 14], fill=NAVY, outline=SKY, width=8)


def footer(d):
    d.rectangle([0, 980, 1080, 1080], fill=FOOT)
    center(d, 1008, BRAND, font(F_DM, 36, "Medium"), WHITE)


def phone_box(d, y=750):
    d.rounded_rectangle([110, y, 970, y + 155], radius=28, fill=ORANGE)
    center(d, y + 15, PHONE, font(F_JAK, 104, "ExtraBold"), WHITE)


def page_dots(d, n, i):
    x0 = 540 - (n - 1) * 22
    for k in range(n):
        x = x0 + k * 44
        d.ellipse([x - 9, 940, x + 9, 958], fill=ORANGE if k == i else SKY)


def simple(out, headline, sub_lines, cta):
    im, d = base_canvas()
    snowflake(d)
    hf = fit(d, headline, F_JAK, "ExtraBold", 150, 960)
    center(d, 320 + (150 - hf.size) // 2, headline, hf, WHITE)
    y = 510
    for line in sub_lines[:3]:
        center(d, y, line, fit(d, line, F_DM, "Medium", 50, 940), SKY)
        y += 66
    center(d, 690, cta, font(F_DM, 40, "Medium"), WHITE)
    phone_box(d)
    footer(d)
    im.save(out, "PNG", optimize=True)
    print("ok", out)


def carrusel(prefix, question, fact_lines, close_lines, cta, lang="es"):
    swipe = "Desliza →" if lang == "es" else "Swipe →"
    read = "Léelo en el blog" if lang == "es" else "Read it on the blog"
    # Lámina 1: la pregunta
    im, d = base_canvas()
    snowflake(d)
    words = question.split()
    if d.textlength(question, font=font(F_JAK, 120, "ExtraBold")) <= 940 or len(words) < 2:
        lines = [question]
    else:
        h = len(words) // 2
        lines = [" ".join(words[:h]), " ".join(words[h:])]
    y = 380 if len(lines) == 2 else 440
    for ln in lines:
        f = fit(d, ln, F_JAK, "ExtraBold", 120, 940, 70)
        center(d, y, ln, f, WHITE)
        y += f.size + 20
    center(d, 800, swipe, font(F_DM, 46, "Medium"), ORANGE)
    page_dots(d, 3, 0)
    footer(d)
    im.save(f"{prefix}-1.png", "PNG", optimize=True)
    # Lámina 2: el dato
    im, d = base_canvas()
    n = min(len(fact_lines), 4)
    y = 500 - (n * 86) // 2
    d.rectangle([110, y - 6, 128, y + n * 86 - 14], fill=ORANGE)
    size = min(fit(d, ln, F_DM, "Medium", 58, 820, 40).size for ln in fact_lines[:4])
    f = font(F_DM, size, "Medium")
    for ln in fact_lines[:4]:
        d.text((170, y), ln, font=f, fill=WHITE)
        y += 86
    page_dots(d, 3, 1)
    footer(d)
    im.save(f"{prefix}-2.png", "PNG", optimize=True)
    # Lámina 3: cierre con blog + número
    im, d = base_canvas()
    center(d, 150, read, font(F_JAK, 72, "ExtraBold"), WHITE)
    y = 290
    for ln in close_lines[:2]:
        center(d, y, ln, fit(d, ln, F_DM, "Medium", 50, 900), SKY)
        y += 66
    center(d, 470, "kendallacrepairs.com/blog", font(F_DM, 54, "Medium"), ORANGE)
    center(d, 690, cta, font(F_DM, 40, "Medium"), WHITE)
    phone_box(d, 750)
    page_dots(d, 3, 2)
    footer(d)
    im.save(f"{prefix}-3.png", "PNG", optimize=True)
    print("ok", prefix + "-1/2/3.png")


if __name__ == "__main__":
    ensure_fonts()
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    if mode == "simple":
        out, headline, sub, cta = sys.argv[2:6]
        simple(out, headline, sub.split("|"), cta)
    elif mode == "carrusel":
        prefix, question, fact, close, cta = sys.argv[2:7]
        lang = sys.argv[7] if len(sys.argv) > 7 else "es"
        carrusel(prefix, question, fact.split("|"), close.split("|"), cta, lang)
    else:
        print(__doc__)
