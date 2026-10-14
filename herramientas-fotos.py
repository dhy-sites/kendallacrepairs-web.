import numpy as np, cv2, os
from PIL import Image, ImageEnhance, ImageFilter

SP = os.path.dirname(os.path.abspath(__file__))
OUT = '/home/claude/kendallacrepairs-web./static/img'
LOGO = '/home/claude/logo/logo-horizontal.png'
fs = open(os.path.join(SP, 'orden.txt')).read().split('\n')
F = lambda n: os.path.join(SP, fs[n - 1])

NOMBRES = {"portada": "reparacion-aire-acondicionado-kendall", "por-que-elegirnos": "tecnico-aire-acondicionado-kendall-miami",
           "barrio-calle": "calle-residencial-kendall-aire-acondicionado", "barrio-townhouses": "townhouses-condensadores-ac-miami-dade",
           "barrio-patio": "mini-split-patio-casa-miami", "manometros": "revision-presion-refrigerante-ac-miami"}

def save(im, key, w):
    """Guarda 3 versiones: JPG (respaldo y redes), WebP grande y WebP de 800 px (celulares)."""
    name = NOMBRES.get(key, key + "-kendall")
    im = im.convert('RGB')
    if im.width > w:
        im = im.resize((w, round(im.height * w / im.width)), Image.LANCZOS)
    p = f'{OUT}/{name}.jpg'
    q = 82
    while True:
        im.save(p, 'JPEG', quality=q, optimize=True, progressive=True)
        if os.path.getsize(p) < 260_000 or q <= 60: break
        q -= 4
    im.save(f'{OUT}/{name}.webp', 'WEBP', quality=78, method=6)
    sm = im.resize((800, round(im.height * 800 / im.width)), Image.LANCZOS)
    sm.save(f'{OUT}/{name}-800.webp', 'WEBP', quality=76, method=6)
    print(f"{name:45s} {im.size} jpg {os.path.getsize(p)//1024}KB webp {os.path.getsize(f'{OUT}/{name}.webp')//1024}KB 800 {os.path.getsize(f'{OUT}/{name}-800.webp')//1024}KB")

def crop_ratio(im, r, ybias=0.4):
    W, H = im.size
    if W / H > r:
        nw = round(H * r); x = (W - nw) // 2
        return im.crop((x, 0, x + nw, H))
    nh = round(W / r); y = round((H - nh) * ybias)
    return im.crop((0, y, W, y + nh))

def neutral(im, k=1.0):
    f = np.asarray(im.convert('RGB')).astype(np.float32)
    f[..., 0] *= 1 - 0.07 * k; f[..., 1] *= 1 - 0.015 * k; f[..., 2] *= 1 + 0.06 * k
    im = Image.fromarray(np.clip(f, 0, 255).astype(np.uint8))
    return ImageEnhance.Contrast(ImageEnhance.Color(im).enhance(0.9)).enhance(1.04)

def inpaint(im, shapes):
    a = cv2.cvtColor(np.asarray(im.convert('RGB')), cv2.COLOR_RGB2BGR)
    m = np.zeros(a.shape[:2], np.uint8)
    for kind, *c in shapes:
        if kind == 'circle': cv2.circle(m, (c[0], c[1]), c[2], 255, -1)
        else: cv2.rectangle(m, (c[0], c[1]), (c[2], c[3]), 255, -1)
    a = cv2.inpaint(a, m, 7, cv2.INPAINT_TELEA)
    return Image.fromarray(cv2.cvtColor(a, cv2.COLOR_BGR2RGB))

os.makedirs(OUT, exist_ok=True)
for f in os.listdir(OUT): os.remove(os.path.join(OUT, f))

# Portada: la camioneta ya editada (logo real + luz corregida)
save(Image.open(os.path.join(SP, 'hero-van.webp')), 'portada', 1600)

# Por qué elegirnos: camioneta de lado (#7) con el logo grande en el panel trasero
im = neutral(Image.open(F(7)))
logo = Image.open(LOGO).convert('RGBA')
lw = 300; lh = round(logo.height * lw / logo.width)
logo = logo.resize((lw, lh), Image.LANCZOS).filter(ImageFilter.GaussianBlur(0.5))
r, g, b, a = logo.split(); logo = Image.merge('RGBA', (r, g, b, a.point(lambda v: int(v * .94))))
im = im.convert('RGBA'); im.alpha_composite(logo, (168, 312))
save(im.crop((110, 0, 110 + round(800 * 4 / 3), 800)), 'por-que-elegirnos', 1000)

# Servicios (16:9)
SVC = {'ac-no-enfria': 10, 'ac-gotea-agua': 11, 'ac-hace-ruido': 12, 'ac-no-enciende': 13,
       'mantenimiento-ac': 14, 'instalacion-ac': 17, 'recarga-gas-ac': 18, 'limpieza-ductos': 19,
       'termostato': 20, 'mini-split': 21}
for name, n in SVC.items():
    save(crop_ratio(Image.open(F(n)), 16 / 9, 0.3), name, 1600)

# Barrios
save(crop_ratio(Image.open(F(22)), 16 / 9, 0.45), 'barrio-calle', 1600)
save(crop_ratio(Image.open(F(23)), 16 / 9, 0.45), 'barrio-townhouses', 1600)
save(crop_ratio(inpaint(Image.open(F(24)), [('circle', 924, 462, 15)]), 16 / 9, 0.5), 'barrio-patio', 1600)
save(crop_ratio(Image.open(F(9)), 16 / 9, 0.35), 'manometros', 1600)
