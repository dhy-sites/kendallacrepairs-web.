#!/usr/bin/env python3
"""Reel vertical 1080x1920 de Kendall AC Repairs a partir de un guion JSON.

Uso:  python3 reel-redes.py guion.json static/social/reel-<tema>-<fecha>-<es|en>.mp4
      (TEMA=halloween delante para el tema de temporada; o "tema" en el JSON)

Guion JSON:
{
  "lang": "es",                       # "es" o "en"
  "tema": "halloween",                # opcional: null | "halloween"
  "escenas": [
    {"tipo": "titulo", "lineas": ["¿POR QUÉ", "DURAN MENOS", "*LOS AIRES", "*EN KENDALL?"]},
    {"tipo": "dato", "grande": "3,000", "lineas": ["horas de uso", "al año"], "nota": "En otros estados: la mitad."},
    {"tipo": "frase", "lineas": ["Un aire de", "*10 años", "aquí trabajó", "como uno de", "*20"]},
    {"tipo": "cierre", "pregunta": ["¿Cuántos años", "tiene el tuyo?"], "nota": ["Guía completa en el blog"]}
  ]
}
Una línea que empieza con "*" sale en naranja. 4 a 6 escenas. Duración total 12-20 s.
Necesita: playwright (Chromium) y ffmpeg.
"""
import html, json, os, subprocess, sys, tempfile

from playwright.sync_api import sync_playwright

NAVY = '#0b2545'; ORANGE = '#f26b1d'; SKY = '#9fd6ff'; PURPLE = '#6d3fb0'
PHONE_TXT = '(305) 363-7976'; WEB = 'kendallacrepairs.com'

CSS = f"""
body{{margin:0}}
.s{{width:1080px;height:1920px;background:{NAVY};color:#fff;position:relative;overflow:hidden;
  font-family:'Plus Jakarta Sans','Inter Display','Inter','DejaVu Sans',sans-serif;display:flex;flex-direction:column;justify-content:center;padding:0 90px;box-sizing:border-box}}
.top{{position:absolute;left:0;right:0;top:0;height:22px;background:{ORANGE}}}
.top2{{position:absolute;left:0;right:0;top:22px;height:12px;background:{PURPLE}}}
.foot{{position:absolute;left:0;right:0;bottom:0;height:150px;background:#06182f;display:flex;align-items:center;justify-content:center;font-size:40px;font-weight:600;color:#dbe8f5}}
.h{{font-weight:800;line-height:1.02;letter-spacing:-2px;white-space:nowrap}}
.bar{{border-left:16px solid {ORANGE};padding-left:44px}}
.k{{color:{ORANGE}}}
.sm{{color:{SKY};font-weight:600}}
"""
BAT = '<svg style="position:absolute;{p}" width="{w}" viewBox="0 0 120 50"><path d="M60 18 L52 8 L50 20 C40 8 22 4 0 10 C14 16 18 28 16 40 C26 30 38 30 46 38 C50 30 56 28 60 32 C64 28 70 30 74 38 C82 30 94 30 104 40 C102 28 106 16 120 10 C98 4 80 8 70 20 L68 8 Z" fill="' + PURPLE + '"/></svg>'
PK = '''<svg style="position:absolute;right:70px;bottom:190px" width="130" height="120" viewBox="0 0 150 140"><rect x="68" y="4" width="14" height="30" rx="5" fill="#3f6b1f"/>
<ellipse cx="45" cy="85" rx="38" ry="48" fill="#e2620f"/><ellipse cx="105" cy="85" rx="38" ry="48" fill="#e2620f"/><ellipse cx="75" cy="85" rx="40" ry="52" fill="#f47c20"/>
<path d="M50 72 l14 -14 l6 18 Z M100 72 l-14 -14 l6 18 Z" fill="#3a1a05"/><path d="M44 100 q31 26 62 0 l-8 10 l-8 -6 l-8 8 l-8 -8 l-8 8 l-8 -8 l-8 6 Z" fill="#3a1a05"/></svg>'''
SNOW = f'<svg width="150" height="150" viewBox="0 0 24 24" fill="none" stroke="{SKY}" stroke-width="1.6" stroke-linecap="round" style="margin-bottom:60px"><line x1="12" y1="2" x2="12" y2="22"/><line x1="3.3" y1="7" x2="20.7" y2="17"/><line x1="3.3" y1="17" x2="20.7" y2="7"/><circle cx="12" cy="12" r="1.6"/></svg>'
PHONE = '<svg width="64" height="64" viewBox="0 0 24 24" fill="#fff"><path d="M6.6 10.8c1.4 2.8 3.8 5.1 6.6 6.6l2.2-2.2c.3-.3.7-.4 1-.2 1.1.4 2.3.6 3.6.6.6 0 1 .4 1 1V20c0 .6-.4 1-1 1C10.6 21 3 13.4 3 4c0-.6.4-1 1-1h3.5c.6 0 1 .4 1 1 0 1.3.2 2.5.6 3.6.1.3 0 .7-.2 1L6.6 10.8z"/></svg>'


def size_for(lines, maxpx, width=900, k=0.62):
    longest = max(len(l.lstrip('*')) for l in lines) or 1
    return int(min(maxpx, width / (longest * k)))


def lines_html(lines, px):
    out = []
    for l in lines:
        cls = 'h k' if l.startswith('*') else 'h'
        out.append(f'<div class="{cls}" style="font-size:{px}px">{html.escape(l.lstrip("*"))}</div>')
    return ''.join(out)


def frame(inner, tema):
    deco = ''
    if tema == 'halloween':
        deco = (BAT.replace('{p}', 'left:80px;top:150px').replace('{w}', '190')
                + BAT.replace('{p}', 'right:90px;top:120px').replace('{w}', '150')
                + BAT.replace('{p}', 'right:140px;top:330px').replace('{w}', '100') + PK)
    top2 = '<div class="top2"></div>' if tema == 'halloween' else ''
    return (f'<div class="s"><div class="top"></div>{top2}{deco}{inner}'
            f'<div class="foot">Kendall AC Repairs · Kendall, FL</div></div>')


def scene_html(e, lang, tema):
    t = e['tipo']
    if t == 'titulo':
        px = size_for(e['lineas'], 160)
        return frame(f'<div style="text-align:center">{SNOW}{lines_html(e["lineas"], px)}</div>', tema), 3.2
    if t == 'dato':
        big = html.escape(e['grande'])
        px = size_for(e['lineas'], 100, width=860)
        nota = f'<div class="sm" style="font-size:52px;margin-top:40px">{html.escape(e["nota"])}</div>' if e.get('nota') else ''
        bpx = size_for([e['grande']], 240, width=860, k=0.6)
        return frame(f'<div class="bar"><div class="h k" style="font-size:{bpx}px">{big}</div>{lines_html(e["lineas"], px)}{nota}</div>', tema), 3.0
    if t == 'frase':
        px = size_for(e['lineas'], 150, width=860)
        return frame(f'<div class="bar">{lines_html(e["lineas"], px)}</div>', tema), 3.4
    if t == 'cierre':
        px = size_for(e['pregunta'], 112)
        nota = ''.join(f'<div>{html.escape(n)}</div>' for n in e.get('nota', []))
        call = 'Call' if lang == 'en' else '¿Dudas? Llama'
        inner = (f'<div style="text-align:center">{lines_html(e["pregunta"], px)}'
                 f'<div class="sm" style="font-size:54px;margin:50px 0 90px">{nota}</div>'
                 f'<div style="font-size:50px;font-weight:600;margin-bottom:24px">{call}</div>'
                 f'<div style="display:flex;align-items:center;justify-content:center;gap:24px;background:{ORANGE};border-radius:36px;padding:44px 24px">{PHONE}'
                 f'<span class="h" style="font-size:92px;letter-spacing:-1px">{PHONE_TXT}</span></div>'
                 f'<div style="font-size:48px;font-weight:700;color:{ORANGE};margin-top:50px">{WEB}</div></div>')
        return frame(inner, tema), 4.4
    raise SystemExit(f'tipo de escena desconocido: {t}')


def main():
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    g = json.load(open(sys.argv[1]))
    out = sys.argv[2]
    tema = os.environ.get('TEMA') or g.get('tema')
    lang = g.get('lang', 'es')
    escenas = g['escenas']
    if not 4 <= len(escenas) <= 6 or escenas[-1]['tipo'] != 'cierre':
        raise SystemExit('Hacen falta 4-6 escenas y la última debe ser "cierre".')
    tmp = tempfile.mkdtemp(prefix='reel-')
    durs = []
    with sync_playwright() as p:
        b = p.chromium.launch(); pg = b.new_page(viewport={'width': 1080, 'height': 1920})
        for i, e in enumerate(escenas):
            body, d = scene_html(e, lang, tema)
            path = f'{tmp}/s{i}.html'
            open(path, 'w').write(f'<!doctype html><html lang="{lang}"><head><meta charset="utf-8"><style>{CSS}</style></head><body>{body}</body></html>')
            pg.goto('file://' + path); pg.wait_for_timeout(300)
            pg.screenshot(path=f'{tmp}/s{i}.png'); durs.append(d)
        b.close()
    fps, t = 30, 0.4
    cmd = ['ffmpeg', '-y', '-loglevel', 'error']
    for i in range(len(durs)):
        cmd += ['-i', f'{tmp}/s{i}.png']
    filt = []
    for i, d in enumerate(durs):
        n = int(d * fps)
        filt.append(f"[{i}:v]scale=1188:2112,zoompan=z='1+0.06*on/{n}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={n}:s=1080x1920:fps={fps},format=yuv420p,setsar=1[v{i}]")
    prev, off = 'v0', 0.0
    for i in range(1, len(durs)):
        off += durs[i - 1] - t
        filt.append(f'[{prev}][v{i}]xfade=transition=slideup:duration={t}:offset={off:.2f}[x{i}]')
        prev = f'x{i}'
    os.makedirs(os.path.dirname(out) or '.', exist_ok=True)
    cmd += ['-filter_complex', ';'.join(filt), '-map', f'[{prev}]', '-c:v', 'libx264', '-preset', 'medium',
            '-crf', '20', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', out]
    subprocess.run(cmd, check=True)
    # hoja de contacto para revisar con Read
    sheet = out.rsplit('.', 1)[0] + '-revision.png'
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', out, '-vf',
                    f'fps=1/3,scale=270:480,tile={len(durs)}x1', '-frames:v', '1', sheet], check=True)
    print(f'ok {out} ({sum(durs) - t * (len(durs) - 1):.1f} s) · revisión: {sheet}')


if __name__ == '__main__':
    main()
