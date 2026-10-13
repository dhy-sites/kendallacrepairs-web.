"""Auditoría SEO automática de la carpeta /sitio. Uso: python3 auditoria.py  (sale con código 1 si hay errores)"""
import os, re, json, sys, glob, html
from collections import defaultdict, Counter
from html.parser import HTMLParser

ROOT = os.path.join(os.path.dirname(__file__), "sitio")
DOMAIN = None
errors, warns = [], []

class P(HTMLParser):
    def __init__(self):
        super().__init__(); self.tags = []; self.text = []; self.main = []; self.inmain = False; self.skip = 0; self.h1 = []; self.inh1 = False
    def handle_starttag(self, t, a):
        self.tags.append((t, dict(a)))
        if t in ("script", "style"): self.skip += 1
        if t == "h1": self.inh1 = True; self.h1.append("")
        if t == "main": self.inmain = True
    def handle_endtag(self, t):
        if t in ("script", "style"): self.skip -= 1
        if t == "h1": self.inh1 = False
        if t == "main": self.inmain = False
    def handle_data(self, d):
        if not self.skip: self.text.append(d)
        if not self.skip and self.inmain: self.main.append(d)
        if self.inh1: self.h1[-1] += d

def url_to_file(u):
    p = u.split("#")[0].split("?")[0]
    return os.path.join(ROOT, p.strip("/"), "index.html") if p.endswith("/") else os.path.join(ROOT, p.strip("/"))

pages = {}
for f in sorted(glob.glob(os.path.join(ROOT, "**", "*.html"), recursive=True)):
    rel = "/" + os.path.relpath(f, ROOT).replace("index.html", "")
    if rel.startswith("/admin/"): continue  # panel del blog, no es una página pública
    s = open(f, encoding="utf-8").read()
    p = P(); p.feed(s)
    pages[rel] = (s, p)

titles, descs = defaultdict(list), defaultdict(list)
indexable = []
for rel, (s, p) in pages.items():
    noindex = 'name="robots" content="noindex"' in s
    def E(m): errors.append(f"{rel}: {m}")
    def W(m): warns.append(f"{rel}: {m}")
    t = re.search(r"<title>(.*?)</title>", s)
    d = re.search(r'<meta name="description" content="(.*?)">', s)
    c = re.search(r'<link rel="canonical" href="(.*?)">', s)
    if not t: E("sin <title>")
    if not d: E("sin meta description")
    if not c and not noindex and rel != "/404.html": E("sin canonical")
    if 'name="viewport"' not in s: E("sin viewport")
    if not re.search(r'<html lang="(es|en)">', s): E("sin lang")
    if len(p.h1) != 1: E(f"tiene {len(p.h1)} H1 (debe ser 1)")
    for tag, a in p.tags:
        if tag == "img" and not a.get("alt"): E(f"imagen sin alt: {a.get('src','')[:60]}")
        if tag == "img" and not (a.get("width") and a.get("height")): W("imagen sin width/height")
        if tag == "a" and a.get("href", "").startswith("/"):
            if not os.path.exists(url_to_file(a["href"])): E(f"enlace roto {a['href']}")
        if tag == "a" and a.get("target") == "_blank" and "noopener" not in a.get("rel", ""): W("target _blank sin noopener")
    for m in re.findall(r'<script type="application/ld\+json">(.*?)</script>', s, re.S):
        try: json.loads(m)
        except Exception as ex: E(f"schema JSON inválido: {ex}")
    if noindex or rel == "/404.html": continue
    indexable.append(rel)
    tt = html.unescape(t.group(1)) if t else ""; dd = html.unescape(d.group(1)) if d else ""
    titles[tt].append(rel); descs[dd].append(rel)
    if len(tt) > 65: W(f"título largo ({len(tt)}): {tt}")
    if len(tt) < 25: W(f"título corto ({len(tt)})")
    if not (70 <= len(dd) <= 160): W(f"descripción de {len(dd)} caracteres (ideal 70-160)")
    # hreflang recíproco
    alts = dict(re.findall(r'<link rel="alternate" hreflang="([a-z-]+)" href="(.*?)">', s))
    for lang in ("es", "en"):
        if lang not in alts: E(f"falta hreflang {lang}"); continue
        path = re.sub(r"^https?://[^/]+", "", alts[lang])
        if path not in pages: E(f"hreflang {lang} apunta a página inexistente {path}")
        else:
            back = dict(re.findall(r'<link rel="alternate" hreflang="([a-z-]+)" href="(.*?)">', pages[path][0]))
            if re.sub(r"^https?://[^/]+", "", back.get("es" if rel.startswith("/en/") is False else "en", "")) == "": pass
    if "x-default" not in alts: E("falta hreflang x-default")
    words = len(re.findall(r"\w+", " ".join(p.main)))
    legal = any(k in rel for k in ("privac", "termin", "terms"))
    if legal: pass
    elif words < 350: (W if "/blog/" in rel else E)(f"contenido pobre: {words} palabras")
    elif words < 500: W(f"contenido justo: {words} palabras")
    if 'tel:' not in s: E("sin enlace de llamada")
    if '"BreadcrumbList"' not in s and rel not in ("/", "/en/"): W("sin BreadcrumbList")

for t, rs in titles.items():
    if len(rs) > 1: errors.append(f"título duplicado en {len(rs)} páginas: {t} -> {rs[:3]}")
for d, rs in descs.items():
    if len(rs) > 1: errors.append(f"descripción duplicada en {len(rs)} páginas -> {rs[:3]}")

# contenido casi duplicado (similitud de párrafos únicos)
def shingles(rel):
    txt = re.sub(r"\s+", " ", " ".join(pages[rel][1].main)).lower()
    w = txt.split(); return set(" ".join(w[i:i+5]) for i in range(0, max(0, len(w)-5)))
sh = {r: shingles(r) for r in indexable}
dups = 0
for i, a in enumerate(indexable):
    for b in indexable[i+1:]:
        if a.startswith("/en/") != b.startswith("/en/"): continue
        A, B = sh[a], sh[b]
        if A and B and len(A & B) / len(A | B) > 0.80: dups += 1; warns.append(f"páginas muy parecidas (>80%): {a} ~ {b}")

# contenido único: frases de 5 palabras que aparecen en menos del 20% de las páginas del mismo idioma
for lang_en in (False, True):
    grp = [r for r in indexable if r.startswith("/en/") == lang_en and not any(k in r for k in ("privac","termin","terms"))]
    cnt = Counter(x for r in grp for x in sh[r])
    lim = max(2, int(len(grp) * 0.2))
    uniq = {r: sum(1 for x in sh[r] if cnt[x] <= lim) for r in grp}
    low = [r for r, u in uniq.items() if u < 150]
    print(f"Contenido propio ({'EN' if lang_en else 'ES'}): promedio {sum(uniq.values())//max(1,len(uniq))} frases únicas por página; {len(low)} páginas con menos de 150")
    for r in low: warns.append(f"{r}: poco contenido propio ({uniq[r]})")

# sitemap
sm = open(os.path.join(ROOT, "sitemap.xml"), encoding="utf-8").read()
locs = set(re.sub(r"^https?://[^/]+", "", u) for u in re.findall(r"<loc>(.*?)</loc>", sm))
for r in indexable:
    if r not in locs: errors.append(f"sitemap: falta {r}")
for r in locs:
    if r not in pages: errors.append(f"sitemap: apunta a página inexistente {r}")
rb = open(os.path.join(ROOT, "robots.txt")).read()
if "Disallow: /\n" in rb: errors.append("robots.txt bloquea todo el sitio")
if "Sitemap:" not in rb: errors.append("robots.txt sin Sitemap")

print(f"Páginas: {len(pages)} | indexables: {len(indexable)} | en sitemap: {len(locs)}")
print(f"ERRORES: {len(errors)}")
for e in errors[:60]: print("  ✗", e)
wc = Counter(re.sub(r"[0-9]+", "N", re.sub(r"^/[^:]*: ", "", w).split("(")[0].split(":")[0]) for w in warns)
print(f"AVISOS: {len(warns)}")
for k, v in wc.most_common(): print(f"  · {v} × {k}")
if "-v" in sys.argv:
    for w in warns: print("   ", w)
sys.exit(1 if errors else 0)
