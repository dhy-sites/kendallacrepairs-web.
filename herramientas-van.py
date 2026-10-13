import sys, numpy as np, cv2
from PIL import Image, ImageEnhance

SRC = sys.argv[1]; OUT = sys.argv[2]
LOGO = '/home/claude/logo/logo-horizontal.png'

img = cv2.imread(SRC, cv2.IMREAD_COLOR)
h, w = img.shape[:2]

# 1) Borrar el logo deformado de la IA (inpaint)
mask = np.zeros((h, w), np.uint8)
cv2.rectangle(mask, (428, 333), (550, 375), 255, -1)
img = cv2.inpaint(img, mask, 9, cv2.INPAINT_TELEA)
# suavizar la zona para que no queden manchas
blur = cv2.GaussianBlur(img, (0, 0), 6)
m3 = cv2.GaussianBlur(mask, (0, 0), 3)[..., None] / 255.0
img = (img * (1 - m3) + blur * m3).astype(np.uint8)

# 2) Luz más neutra: quitar parte del tono naranja del atardecer
f = img.astype(np.float32)
f[..., 2] *= 0.93   # rojo
f[..., 1] *= 0.985  # verde
f[..., 0] *= 1.06   # azul
img = np.clip(f, 0, 255).astype(np.uint8)
pil = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
pil = ImageEnhance.Color(pil).enhance(0.9)
pil = ImageEnhance.Contrast(pil).enhance(1.04)

# 3) Pegar el logo real con una ligera perspectiva (el costado va un poco en ángulo)
logo = Image.open(LOGO).convert('RGBA')
lw = 128
lh = int(logo.height * lw / logo.width)
logo = logo.resize((lw * 3, lh * 3), Image.LANCZOS)  # trabajar grande y reducir
L = cv2.cvtColor(np.array(logo), cv2.COLOR_RGBA2BGRA)
H3, W3 = L.shape[:2]
x0, y0 = 428, 330
src = np.float32([[0, 0], [W3, 0], [W3, H3], [0, H3]])
dst = np.float32([[x0, y0], [x0 + lw, y0 + 1], [x0 + lw, y0 + lh - 1], [x0, y0 + lh]])
M = cv2.getPerspectiveTransform(src, dst)
warp = cv2.warpPerspective(L, M, (w, h), flags=cv2.INTER_AREA, borderValue=(0, 0, 0, 0))
layer = Image.fromarray(cv2.cvtColor(warp, cv2.COLOR_BGRA2RGBA))
# integrar con la luz: un poco menos de opacidad y tono cálido leve
r, g, b, a = layer.split()
a = a.point(lambda v: int(v * 0.93))
layer = Image.merge('RGBA', (r, g, b, a))
pil = pil.convert('RGBA'); pil.alpha_composite(layer)

# 4) Teléfono opcional (cuando esté el de Quo)
if len(sys.argv) > 3:
    from PIL import ImageDraw, ImageFont
    d = ImageDraw.Draw(pil)
    font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf', 15)
    d.text((x0 + 4, y0 + lh + 4), sys.argv[3], font=font, fill=(16, 37, 66, 235))

pil = pil.convert('RGB')
pil = pil.resize((1600, int(pil.height * 1600 / pil.width)), Image.LANCZOS)
pil.save(OUT, 'WEBP', quality=82)
pil.crop((440, 340, 760, 500)).resize((960, 480)).save(OUT.replace('.webp', '_zoom.png'))
print(pil.size)
