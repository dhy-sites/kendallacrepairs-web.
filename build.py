"""Genera la web completa en la carpeta /sitio a partir de config.py"""
import os, json, shutil, datetime, html, re
from urllib.parse import quote_plus
from config import SITE, NICHE, AREAS, SERVICES, AUTHOR, ABOUT
from contenido import SVC_EXTRA, AREA_EXTRA, AREA_TIP, AREA_LOCAL
import glob

ROOT = os.path.dirname(os.path.abspath(__file__))

def load_articles():
    """Lee los artículos del blog desde blog/*.json (los que se editan en el panel /admin/)."""
    arts = []
    for f in glob.glob(os.path.join(ROOT, "blog", "*.json")):
        d = json.load(open(f, encoding="utf-8"))
        fecha = str(d.get("fecha", ""))[:10] or datetime.date.today().isoformat()
        rel = [x for x in (d.get("servicios") or []) if x in {sv[0] for sv in SERVICES}][:3] or ["mantenimiento-ac"]
        es = {"title": d["titulo_es"].strip(), "desc": d["desc_es"].strip(), "intro": d.get("intro_es", "").strip(), "body": d.get("cuerpo_es", "")}
        en = {"title": d["titulo_en"].strip(), "desc": d["desc_en"].strip(), "intro": d.get("intro_en", "").strip(), "body": d.get("cuerpo_en", "")}
        arts.append((d["slug_es"].strip(), d["slug_en"].strip(), fecha, int(d.get("pexels") or 6471914), rel, es, en, (d.get("imagen") or "").strip()))
    arts.sort(key=lambda a: a[2], reverse=True)
    return arts

SITE_VERSION = "11"
ARTICLES = load_articles()

OUT = os.path.join(os.path.dirname(__file__), "sitio")
TODAY = datetime.date.today().isoformat()
S = SITE
E = html.escape

UI = {
    "es": {
        "lang": "es", "call": "Llamar ahora", "wa": "WhatsApp", "toggle": "English",
        "form_title": "Pide que te llamen", "form_sub": "Déjanos tus datos y un técnico te contacta hoy.",
        "name": "Tu nombre", "phone": "Teléfono", "problem": "¿Qué le pasa a tu AC?", "zip": "Código postal",
        "choose": "Elige una opción", "other": "Otro", "send": "Quiero que me llamen",
        "privacy_note": "Tus datos solo se usan para coordinar tu servicio.",
        "problems_t": "¿Qué problema tiene tu AC?", "problems_s": "Toca tu caso y llámanos. Te conectamos con el técnico indicado.",
        "call_this": "Llamar por esto →",
        "how_t": "Así de fácil", "how": [("1", "Llamas o escribes", "Nos cuentas el problema en menos de un minuto."),
                                          ("2", "Te conectamos", "Un técnico licenciado de tu zona te contacta y coordina la visita."),
                                          ("3", "Apruebas el precio", "Te dan el precio antes de empezar. Tú decides.")],
        "areas_t": "Zonas que cubrimos", "areas_s": "Servicio en {city} y comunidades cercanas.",
        "faq_t": "Preguntas frecuentes",
        "cta_t": "¿Tu AC está fallando? No esperes a mañana.",
        "trust": ["Atendemos de 7 am a 10 pm, los 7 días", "Diagnóstico de referencia: $75 – $150, precio claro antes de empezar", "Al llamar te atiende una persona, en español", "Técnicos con licencia de Florida"], "book": "Pedir cita",
        "disclaimer": "{brand} es un servicio de referidos operado por {op}. Los trabajos los realizan contratistas independientes con licencia en Florida.",
        "privacy": "Privacidad", "terms": "Términos", "areas_word": "Zonas",
        "area_h1": "{service} en {area}", "area_more": "Otras zonas cercanas",
        "home": "Inicio", "svc_t": "Servicios", "svc_s": "Elige lo que necesitas y te conectamos con el técnico indicado.",
        "signs_t": "Señales de que necesitas este servicio", "svc_more": "Otros servicios", "svc_word": "Servicios",
    },
    "en": {
        "lang": "en", "call": "Call now", "wa": "WhatsApp", "toggle": "Español",
        "form_title": "Get a call back", "form_sub": "Leave your info and a technician will contact you today.",
        "name": "Your name", "phone": "Phone", "problem": "What's wrong with your AC?", "zip": "ZIP code",
        "choose": "Choose one", "other": "Other", "send": "Call me today",
        "privacy_note": "Your info is only used to coordinate your service.",
        "problems_t": "What's wrong with your AC?", "problems_s": "Find your issue and call. We'll connect you with the right technician.",
        "call_this": "Call about this →",
        "how_t": "How it works", "how": [("1", "Call or message", "Tell us the problem in under a minute."),
                                          ("2", "We connect you", "A licensed local technician contacts you to schedule the visit."),
                                          ("3", "You approve the price", "You get the price before any work starts. Your call.")],
        "areas_t": "Areas we serve", "areas_s": "Service in {city} and nearby communities.",
        "faq_t": "Frequently asked questions",
        "cta_t": "AC acting up? Don't wait until tomorrow.",
        "trust": ["Open 7 am to 10 pm, 7 days a week", "Reference diagnostic: $75 – $150, clear price up front", "A real person answers, in English or Spanish", "Florida-licensed technicians"], "book": "Book a visit",
        "disclaimer": "{brand} is a referral service operated by {op}. All work is performed by independent Florida-licensed contractors.",
        "privacy": "Privacy", "terms": "Terms", "areas_word": "Areas",
        "area_h1": "{service} in {area}", "area_more": "Other nearby areas",
        "home": "Home", "svc_t": "Services", "svc_s": "Pick what you need and we'll connect you with the right technician.",
        "signs_t": "Signs you need this service", "svc_more": "Other services", "svc_word": "Services",
    },
}

# rutas por idioma
def base(lang): return "/" if lang == "es" else "/en/"
def area_path(lang, slug): return f"{base(lang)}{NICHE[lang]['slug_prefix']}-{slug}/"
CITY_SLUG = S["city"].lower().replace(" ", "-")
def svc_path(lang, sv): return f"{base(lang)}{sv[0] if lang == 'es' else sv[1]}-{CITY_SLUG}/"
def svc(lang, sv): return sv[2] if lang == "es" else sv[3]
LEGAL = {"es": {"privacy": "/privacidad/", "terms": "/terminos/", "thanks": "/gracias/"},
         "en": {"privacy": "/en/privacy/", "terms": "/en/terms/", "thanks": "/en/thank-you/"}}

def fmt(t, **kw):
    d = dict(city=S["city"], brand=S["brand"], op=S["operator"],
             areas=", ".join(a[0] for a in AREAS))
    d.update(kw)
    return t.format(**d)

# ---------- textos extra del diseño ----------
UI["es"].update({
    "topbar": "Se habla español · Lunes a domingo, 7am – 10pm",
    "tagline": "Reparación de aire acondicionado",
    "nav": [("Servicios", "#servicios"), ("Zonas", "#zonas"), ("Consejos", "blog/"), ("Nosotros", "quienes-somos/")],
    "call_today": "Llama hoy",
    "form_title": "Solicita servicio", "form_sub": "Te llamamos para coordinar la visita, de 7am a 10pm.",
    "trust_icons": [("shield", "Técnicos licenciados", "Contratistas con licencia de Florida y seguro"),
                    ("clock", "Servicio el mismo día", "Según disponibilidad en tu zona"),
                    ("tag", "Precio antes de empezar", "Sin sorpresas: tú apruebas el trabajo"),
                    ("chat", "Hablamos español", "Te atendemos en español o inglés")],
    "svc_t": "Nuestros servicios de aire acondicionado", "svc_s": "Reparación, mantenimiento e instalación para casas y apartamentos en {city} y alrededores.",
    "more": "Ver más",
    "why_t": "Un técnico de confianza, sin perder tiempo buscando",
    "why_p": "Cuando el AC se daña en pleno verano no hay tiempo para llamar a diez compañías. Nos llamas una vez, nos cuentas qué pasa y te conectamos con un técnico licenciado que trabaja en tu zona.",
    "why_list": ["Técnicos con licencia del Estado de Florida y seguro", "Te dan el precio antes de tocar el equipo", "Todas las marcas: Carrier, Trane, Lennox, Goodman, Rheem", "Casas, townhouses, condominios y mini splits"],
    "how_t": "Cómo funciona",
    "areas_t": "Zonas de servicio", "areas_s": "Atendemos {city} y las comunidades cercanas del suroeste de Miami-Dade.",
    "faq_t": "Preguntas frecuentes",
    "cta_t": "¿Tu aire acondicionado dejó de enfriar?", "cta_s": "Llama ahora y te conectamos hoy con un técnico de tu zona.",
    "contact_t": "Contacto", "hours": "Lunes a domingo, 7am – 10pm",
    "map_t": "Mapa de la zona de servicio: {place}",
    "map_note": "Mapa de referencia de la zona que cubrimos. Los técnicos van a tu casa; no es una oficina abierta al público.",
})
UI["en"].update({
    "topbar": "Se habla español · Monday to Sunday, 7am – 10pm",
    "tagline": "Air conditioning repair",
    "nav": [("Services", "#servicios"), ("Areas", "#zonas"), ("Tips", "blog/"), ("About", "about-us/")],
    "call_today": "Call today",
    "form_title": "Request service", "form_sub": "We'll call you back to schedule a visit, 7am to 10pm.",
    "trust_icons": [("shield", "Licensed technicians", "Florida-licensed and insured contractors"),
                    ("clock", "Same-day service", "Based on availability in your area"),
                    ("tag", "Price before work starts", "No surprises: you approve the job"),
                    ("chat", "Se habla español", "We help you in English or Spanish")],
    "svc_t": "Our air conditioning services", "svc_s": "Repair, maintenance and installation for homes and apartments in {city} and nearby.",
    "more": "Learn more",
    "why_t": "A trusted technician, without wasting time searching",
    "why_p": "When your AC breaks in the middle of summer, there's no time to call ten companies. Call us once, tell us what's happening, and we connect you with a licensed technician who works in your area.",
    "why_list": ["Florida state-licensed and insured technicians", "You get the price before anyone touches the unit", "All brands: Carrier, Trane, Lennox, Goodman, Rheem", "Homes, townhouses, condos and mini splits"],
    "how_t": "How it works",
    "areas_t": "Service areas", "areas_s": "We serve {city} and nearby communities in southwest Miami-Dade.",
    "faq_t": "Frequently asked questions",
    "cta_t": "Did your AC stop cooling?", "cta_s": "Call now and we'll connect you today with a technician in your area.",
    "contact_t": "Contact", "hours": "Monday to Sunday, 7am – 10pm",
    "map_t": "Service area map: {place}",
    "map_note": "Reference map of the area we cover. Technicians come to your home; this is not a walk-in office.",
})

def px(i, w=1800):
    # str = foto propia en static/img (versión 9); int = foto de Pexels
    if isinstance(i, str): return f"{SITE['domain']}/img/{i}.jpg"
    return f"https://images.pexels.com/photos/{i}/pexels-photo-{i}.jpeg?auto=compress&cs=tinysrgb&w={w}"
IMG_HERO = px("reparacion-aire-acondicionado-kendall")
SVC_IMG = {"reparacion-ac-emergencia": "revision-presion-refrigerante-ac-miami", "calidad-aire-humedad": "ac-gotea-agua-kendall"}
SVC_IMG.update({s: s + "-kendall" for s in ["ac-no-enfria", "ac-gotea-agua", "ac-hace-ruido", "ac-no-enciende", "mantenimiento-ac",
                                       "instalacion-ac", "recarga-gas-ac", "limpieza-ductos", "termostato", "mini-split"]})
AREA_POOL = ["calle-residencial-kendall-aire-acondicionado", "townhouses-condensadores-ac-miami-dade", "mini-split-patio-casa-miami",
             "revision-presion-refrigerante-ac-miami", "mantenimiento-ac-kendall", "ac-hace-ruido-kendall", "ac-no-enciende-kendall",
             "instalacion-ac-kendall", "recarga-gas-ac-kendall", "reparacion-aire-acondicionado-kendall", "ac-gotea-agua-kendall",
             "ac-no-enfria-kendall", "mini-split-kendall"]
IMG_UNIT = px("tecnico-aire-acondicionado-kendall-miami")

# Texto alternativo de cada foto propia (describe la escena + servicio + zona, sin exagerar)
IMG_ALT = {
 "calle-kendall-lago": ("Calle residencial de Kendall con palmas reales, casas de una planta y un lago al fondo; unidad de aire acondicionado junto a una casa",
                        "Residential street in Kendall with royal palms, single-story homes and a lake in the background; AC unit beside a house"),
 "huracan-condensador-miami": ("Técnico asegurando la unidad exterior de aire acondicionado a su base antes de un huracán en Miami, con paneles en las ventanas",
                               "Technician securing the outdoor AC unit to its pad before a hurricane in Miami, with shutters on the windows"),
 "reparacion-aire-acondicionado-kendall": ("Técnico revisando la unidad exterior de aire acondicionado de una casa en Kendall, Miami",
                                           "Technician checking the outdoor air conditioning unit of a home in Kendall, Miami"),
 "tecnico-aire-acondicionado-kendall-miami": ("Técnico de aire acondicionado midiendo con multímetro una unidad exterior en Kendall",
                                              "AC technician testing an outdoor unit with a multimeter in Kendall"),
 "ac-no-enfria-kendall": ("Técnico midiendo la temperatura del aire en una rejilla de una casa en Kendall porque el AC no enfría",
                          "Technician measuring vent air temperature in a Kendall home because the AC is not cooling"),
 "ac-gotea-agua-kendall": ("Técnico destapando el drenaje del manejador de aire que gotea agua en un clóset",
                           "Technician clearing the condensate drain of a leaking air handler in a closet"),
 "ac-hace-ruido-kendall": ("Técnico revisando con linterna el motor del ventilador de un AC que hace ruido",
                           "Technician inspecting the fan motor of a noisy AC with a flashlight"),
 "ac-no-enciende-kendall": ("Técnico probando con multímetro la caja eléctrica de un aire acondicionado que no enciende",
                            "Technician testing the disconnect box of an AC that won't turn on with a multimeter"),
 "mantenimiento-ac-kendall": ("Mantenimiento de aire acondicionado: limpieza del serpentín de la unidad exterior con manguera",
                              "AC maintenance: rinsing the outdoor condenser coil with a hose"),
 "instalacion-ac-kendall": ("Dos técnicos instalando una unidad nueva de aire acondicionado junto a una casa en Miami-Dade",
                            "Two technicians installing a new air conditioning unit beside a Miami-Dade home"),
 "recarga-gas-ac-kendall": ("Técnico leyendo los manómetros durante la recarga de gas refrigerante de un AC",
                            "Technician reading gauges while recharging AC refrigerant"),
 "limpieza-ductos-kendall": ("Técnico con mascarilla limpiando un ducto de aire acondicionado desde el techo",
                             "Technician with a dust mask cleaning an air duct through a ceiling vent"),
 "termostato-kendall": ("Técnico ajustando un termostato inteligente en la pared de una casa",
                        "Technician adjusting a smart thermostat on a home wall"),
 "mini-split-kendall": ("Técnico limpiando el filtro de un mini split en un dormitorio",
                        "Technician cleaning the filter of a mini split in a bedroom"),
 "calle-residencial-kendall-aire-acondicionado": ("Calle residencial con palmas y técnico revisando un aire acondicionado en Kendall",
                                                  "Residential street with palm trees and a technician checking an AC in Kendall"),
 "townhouses-condensadores-ac-miami-dade": ("Técnico revisando una fila de unidades de aire acondicionado en townhouses de Miami-Dade",
                                            "Technician servicing a row of AC condensers at Miami-Dade townhouses"),
 "mini-split-patio-casa-miami": ("Técnico revisando la unidad exterior de un mini split en el patio de una casa con piscina en Miami",
                                 "Technician servicing a mini split outdoor unit on a Miami home patio with a pool"),
 "revision-presion-refrigerante-ac-miami": ("Técnico conectando manómetros a una unidad exterior para revisar la presión del refrigerante",
                                            "Technician connecting gauges to an outdoor unit to check refrigerant pressure"),
}
IMG_W = {"reparacion-aire-acondicionado-kendall": 1600, "tecnico-aire-acondicionado-kendall-miami": 1000}
_LOCAL_RE = re.compile(r"/img/([a-z0-9-]+)\.jpg$")
def local_name(url): m = _LOCAL_RE.search(url or ""); return m.group(1) if m else None
def img_alt(url, lang, fallback):
    n = local_name(url)
    return IMG_ALT[n][0 if lang == "es" else 1] if n in IMG_ALT else fallback
def picture(url, alt, w, h, lazy=True, style="", sizes="(max-width: 800px) 100vw, 800px", cls="", high=False):
    """<picture> con WebP (800 px y grande) y JPG de respaldo para las fotos propias; <img> normal para el resto."""
    attrs = (f' alt="{E(alt)}" width="{w}" height="{h}"' + (' loading="lazy" decoding="async"' if lazy else "")
             + (' fetchpriority="high"' if high else "") + (f' style="{style}"' if style else ""))
    n = local_name(url)
    if not n: return f'<img src="{E(url)}"{attrs}>' if not cls else f'<img class="{cls}" src="{E(url)}"{attrs}>'
    base = url[: -len(".jpg")]
    c = f' class="{cls}"' if cls else ""
    real_w = IMG_W.get(n, 1200)  # ancho real del archivo grande
    return (f'<picture{c}><source type="image/webp" srcset="{base}-800.webp 800w, {base}.webp {real_w}w" sizes="{sizes}">'
            f'<img src="{url}"{attrs}></picture>')

# ---------- íconos (trazos simples, sin emojis) ----------
ICON_PATHS = {
    "phone": '<path d="M22 16.9v3a2 2 0 0 1-2.2 2 19.8 19.8 0 0 1-8.6-3.1 19.5 19.5 0 0 1-6-6A19.8 19.8 0 0 1 2.1 4.2 2 2 0 0 1 4.1 2h3a2 2 0 0 1 2 1.7c.1.9.4 1.8.7 2.7a2 2 0 0 1-.5 2.1L8 9.8a16 16 0 0 0 6 6l1.3-1.3a2 2 0 0 1 2.1-.4c.9.3 1.8.6 2.7.7a2 2 0 0 1 1.7 2z"/>',
    "wa": '<path d="M3 21l1.6-4.8A8.5 8.5 0 1 1 8 19.6z"/><path d="M9 9.5c0 3 2.5 5.5 5.5 5.5l1-1.5-2-1-1 .8a4 4 0 0 1-1.8-1.8l.8-1-1-2z"/>',
    "shield": '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><path d="m9 12 2 2 4-4"/>',
    "clock": '<circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/>',
    "tag": '<path d="M20.6 13.4 13.4 20.6a2 2 0 0 1-2.8 0L2 12V2h10l8.6 8.6a2 2 0 0 1 0 2.8z"/><circle cx="7" cy="7" r="1.5"/>',
    "chat": '<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>',
    "check": '<path d="M20 6 9 17l-5-5"/>',
    "pin": '<path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0z"/><circle cx="12" cy="10" r="3"/>',
    "arrow": '<path d="M5 12h14M13 5l7 7-7 7"/>',
    "snow": '<path d="M12 2v20M4.9 4.9l14.2 14.2M2 12h20M4.9 19.1 19.1 4.9"/><path d="m9 4 3 2 3-2M9 20l3-2 3 2M4 9l2 3-2 3M20 9l-2 3 2 3"/>',
    "drop": '<path d="M12 2.7s-6 6.6-6 11.3a6 6 0 0 0 12 0C18 9.3 12 2.7 12 2.7z"/>',
    "sound": '<path d="M11 5 6 9H2v6h4l5 4z"/><path d="M15.5 8.5a5 5 0 0 1 0 7M19 5a10 10 0 0 1 0 14"/>',
    "power": '<path d="M12 2v10"/><path d="M18.4 6.6a9 9 0 1 1-12.8 0"/>',
    "wrench": '<path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.8-3.8a6 6 0 0 1-7.9 7.9l-6.9 6.9a2.1 2.1 0 0 1-3-3l6.9-6.9a6 6 0 0 1 7.9-7.9z"/>',
    "box": '<rect x="2" y="6" width="20" height="14" rx="2"/><path d="M6 10h4M6 14h4"/><circle cx="16" cy="13" r="3"/>',
    "gauge": '<path d="M12 14l4-4"/><path d="M3.3 19a10 10 0 1 1 17.4 0z"/>',
    "wind": '<path d="M17.7 7.7A2.5 2.5 0 1 1 19.5 12H2M9.6 4.6A2 2 0 1 1 11 8H2M12.6 19.4A2 2 0 1 0 14 16H2"/>',
    "thermo": '<path d="M14 14.8V4a2 2 0 0 0-4 0v10.8a4 4 0 1 0 4 0z"/>',
    "cloud": '<path d="M7 18a4.5 4.5 0 0 1-.5-9A6 6 0 0 1 18 9.5a4.3 4.3 0 0 1-.5 8.5z"/><path d="M9 21h6"/>',
    "split": '<rect x="2" y="5" width="20" height="9" rx="2"/><path d="M6 11h12M7 18l1-2M12 19v-3M17 18l-1-2"/>',
}
SVC_ICON = {"ac-no-enfria": "snow", "ac-gotea-agua": "drop", "ac-hace-ruido": "sound", "ac-no-enciende": "power",
            "mantenimiento-ac": "wrench", "instalacion-ac": "box", "recarga-gas-ac": "gauge",
            "limpieza-ductos": "wind", "termostato": "thermo", "mini-split": "split",
            "reparacion-ac-emergencia": "clock", "calidad-aire-humedad": "cloud"}

def icon(name, size=24, cls="ic"):
    return (f'<svg class="{cls}" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
            f'stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{ICON_PATHS[name]}</svg>')

LOGO = ('<svg width="40" height="40" viewBox="0 0 40 40" aria-hidden="true"><rect width="40" height="40" rx="9" fill="var(--navy)"/>'
        '<circle cx="20" cy="20" r="13.2" fill="var(--red)"/>'
        '<path d="M20 20L20.00 8.80M20.00 13.28L17.69 10.52M20.00 13.28L22.31 10.52M20 20L10.30 14.40M14.18 16.64L10.64 17.27M14.18 16.64L12.95 13.26M20 20L10.30 25.60M14.18 23.36L12.95 26.74M14.18 23.36L10.64 22.73M20 20L20.00 31.20M20.00 26.72L22.31 29.48M20.00 26.72L17.69 29.48M20 20L29.70 25.60M25.82 23.36L29.36 22.73M25.82 23.36L27.05 26.74M20 20L29.70 14.40M25.82 16.64L27.05 13.26M25.82 16.64L29.36 17.27" fill="none" stroke="#fff" stroke-width="2.3" stroke-linecap="round"/></svg>')
def brand_html(): return E(S['brand']).replace(' AC ', ' <span style="color:var(--red)">AC</span> ', 1)

CSS = """
:root{--navy:#0B2545;--navy2:#13315C;--red:#C8102E;--red2:#A50D26;--ink:#1B2430;--mut:#5B6675;--line:#E3E7EC;--soft:#F3F5F8}
*{box-sizing:border-box}html{scroll-behavior:auto}.ptw{overflow-x:auto;margin:18px 0 10px}.ptable{width:100%;border-collapse:collapse;background:#fff;font-size:17px}.ptable th,.ptable td{padding:11px 14px;border-bottom:1px solid #D9E1EA;text-align:left}.ptable th{background:var(--navy);color:#fff;font-size:14px;text-transform:uppercase;letter-spacing:.04em}.ptable td:last-child{white-space:nowrap;font-weight:700;color:var(--navy)}.pnote{font-size:15px;color:#55657A}
body{margin:0;font-family:"Source Sans 3",system-ui,-apple-system,"Segoe UI",Arial,sans-serif;font-size:17px;color:var(--ink);background:#fff;line-height:1.6;padding-bottom:62px}
h1,h2,h3,.cond{font-family:"Barlow Condensed","Arial Narrow",Arial,sans-serif;font-weight:700;line-height:1.08;letter-spacing:.2px}
a{color:var(--navy2)}img{max-width:100%;display:block}
.wrap{max-width:1180px;margin:0 auto;padding:0 16px}
.ic{flex:none}
/* barra superior */
.topbar{background:var(--navy);color:#C9D4E3;font-size:14px}
.topbar .wrap{display:flex;justify-content:space-between;align-items:center;min-height:36px;gap:10px}
.topbar a{color:#fff;font-weight:700;text-decoration:none}
/* cabecera */
.hdr{background:#fff;border-bottom:1px solid var(--line);position:sticky;top:0;z-index:20}
.hdr .wrap{display:flex;align-items:center;justify-content:space-between;gap:16px;min-height:74px}
.brand{display:flex;align-items:center;gap:10px;text-decoration:none;color:var(--navy)}
.brand b{display:block;font-family:"Barlow Condensed",Arial,sans-serif;font-size:24px;line-height:1;text-transform:uppercase;letter-spacing:.5px}
.brand small{display:block;font-size:12.5px;color:var(--mut);text-transform:uppercase;letter-spacing:1px;margin-top:3px}
.menu{display:flex;align-items:center;gap:22px}
.menu a{color:var(--ink);text-decoration:none;font-weight:600;font-size:16px}
.menu a:hover{color:var(--red)}
.callbtn{display:flex;align-items:center;gap:10px;background:var(--red);color:#fff!important;padding:9px 16px;border-radius:4px;line-height:1.15}
.callbtn small{display:block;font-size:12px;text-transform:uppercase;letter-spacing:.8px;opacity:.9;font-weight:600}
.callbtn strong{display:block;font-size:19px;font-family:"Barlow Condensed",Arial,sans-serif}
.callbtn:hover{background:var(--red2)}
/* hero */
.hero{position:relative;color:#fff;background:var(--navy) center/cover no-repeat}
.hero{overflow:hidden}.hbg,.hbg img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}.hero:before{z-index:1;content:"";position:absolute;inset:0;background:linear-gradient(90deg,rgba(8,26,50,.94) 0%,rgba(8,26,50,.82) 45%,rgba(8,26,50,.45) 100%)}
.hero .wrap{position:relative;z-index:2;display:grid;grid-template-columns:minmax(0,1fr);gap:28px;padding-top:44px;padding-bottom:48px}
.crumb{font-size:14px;color:#C9D4E3;margin-bottom:10px}.crumb a{color:#fff}
.eyebrow{display:inline-block;font-size:14px;font-weight:700;text-transform:uppercase;letter-spacing:1.4px;color:#fff;border-left:3px solid var(--red);padding-left:10px;margin-bottom:14px}
.hero h1{font-size:40px;margin:0 0 14px;text-transform:uppercase}
.hero p.sub{font-size:19px;color:#E4EAF2;margin:0 0 24px;max-width:600px}
.btns{display:flex;flex-wrap:wrap;gap:12px}
.btn{display:inline-flex;align-items:center;justify-content:center;gap:9px;padding:14px 22px;border-radius:4px;font-weight:700;text-decoration:none;font-size:17px;border:2px solid transparent;cursor:pointer;font-family:inherit}
.b-call{background:var(--red);color:#fff}.b-call:hover{background:var(--red2)}
.b-ghost{border-color:#fff;color:#fff;background:transparent}.b-ghost:hover{background:#fff;color:var(--navy)}
.b-navy{background:var(--navy);color:#fff}
.hero ul.ticks{list-style:none;padding:0;margin:24px 0 0;display:grid;gap:8px;font-size:16px}
.hero p.zones{margin:16px 0 0;font-size:15px;color:#C9D6E6;display:flex;gap:6px;align-items:flex-start}.hero p.zones .ic{flex:none;margin-top:3px}
.hero ul.ticks li{display:flex;gap:8px;align-items:center}.hero ul.ticks .ic{color:#7FD1A0}
/* formulario */
.card-form{background:#fff;color:var(--ink);border-radius:6px;padding:24px;border-top:5px solid var(--red);box-shadow:0 18px 40px rgba(0,0,0,.25)}
.card-form h2{margin:0 0 4px;font-size:28px;text-transform:uppercase;color:var(--navy)}
.card-form p{margin:0 0 12px;color:var(--mut);font-size:15px}
label{display:block;font-size:14px;font-weight:700;margin:12px 0 5px;color:var(--ink)}
input,select{width:100%;padding:12px;border:1px solid #C7CFD9;border-radius:4px;font-size:16px;font-family:inherit;background:#fff}
input:focus,select:focus{outline:2px solid var(--navy2);border-color:var(--navy2)}
.card-form .btn{width:100%;margin-top:16px}
.note{font-size:13px;color:var(--mut);margin-top:10px;text-align:center}
.hide{display:none}
/* franja de confianza */
.trust{background:var(--soft);border-bottom:1px solid var(--line)}
.trust .wrap{display:grid;grid-template-columns:1fr 1fr;gap:18px;padding-top:24px;padding-bottom:24px}
.trust div{display:flex;gap:12px;align-items:flex-start}
.trust .ic{color:var(--red);margin-top:2px}
.trust b{display:block;font-size:16px;color:var(--navy)}.trust span{font-size:14px;color:var(--mut);line-height:1.4;display:block}
/* secciones */
section.blk{padding:60px 0}section.soft{background:var(--soft)}
.head{max-width:720px;margin-bottom:30px}
.kicker{font-size:14px;font-weight:700;text-transform:uppercase;letter-spacing:1.4px;color:var(--red);margin:0 0 6px}
h2.t{font-size:36px;margin:0 0 10px;color:var(--navy);text-transform:uppercase}
h1.t{margin:8px 0 10px;color:var(--navy);text-transform:uppercase}
@media(max-width:560px){h1.t{font-size:34px!important}}
p.s{margin:0;color:var(--mut);font-size:18px}
.grid{display:grid;gap:18px}
.svc{display:flex;flex-direction:column;background:#fff;border:1px solid var(--line);border-radius:6px;padding:24px;text-decoration:none;color:var(--ink);transition:border-color .15s,box-shadow .15s}
.svc:hover{border-color:var(--navy2);box-shadow:0 8px 22px rgba(11,37,69,.08)}
.svc .ibox{width:48px;height:48px;border-radius:6px;background:#EAF0F7;color:var(--navy2);display:flex;align-items:center;justify-content:center;margin-bottom:14px}
.svc h3{font-size:23px;margin:0 0 8px;color:var(--navy);text-transform:uppercase}
.svc p{margin:0 0 14px;color:var(--mut);font-size:16px;flex:1}
.svc .more{display:flex;align-items:center;gap:6px;color:var(--red);font-weight:700;font-size:15px}
/* por qué */
.split{display:grid;gap:30px;align-items:center}
.split .photo{border-radius:6px;overflow:hidden;background:#D9E1EA;aspect-ratio:4/3}
.split .photo img{width:100%;height:100%;object-fit:cover}
ul.checks{list-style:none;padding:0;margin:20px 0}
ul.checks li{display:flex;gap:10px;margin:10px 0}ul.checks .ic{color:var(--red);margin-top:3px}
.honest{font-size:14px;color:var(--mut);border-left:3px solid var(--line);padding-left:12px}
/* pasos */
.steps{counter-reset:s}
.step{border-top:3px solid var(--navy);padding-top:16px}
.step .n{font-family:"Barlow Condensed",Arial,sans-serif;font-size:42px;color:var(--red);line-height:1;font-weight:700}
.step h3{font-size:22px;margin:6px 0;color:var(--navy);text-transform:uppercase}.step p{margin:0;color:var(--mut)}
/* zonas */
.areas{display:grid;grid-template-columns:1fr 1fr;gap:4px 18px;list-style:none;padding:0;margin:0}
.areas a{display:flex;align-items:center;gap:8px;padding:10px 0;border-bottom:1px solid var(--line);text-decoration:none;color:var(--ink);font-weight:600}
.areas a:hover{color:var(--red)}.areas .ic{color:var(--red)}
/* mapa de la zona */
.zmap{display:grid;gap:26px;align-items:start}
.mapbox{border-radius:6px;overflow:hidden;border:1px solid var(--line);background:#D9E1EA;aspect-ratio:4/3;max-width:100%}
.mapbox iframe{width:100%;height:100%;border:0;display:block}
.mapnote{font-size:13.5px;color:var(--mut);margin:8px 0 0}
/* datos de la zona */
.facts{border:1px solid var(--line);border-radius:6px;padding:16px 18px;margin:4px 0 18px;background:#fff}
.facts b{color:var(--navy);font-size:17px}
.facts dl{display:grid;grid-template-columns:minmax(0,max-content) minmax(0,1fr);gap:6px 16px;margin:10px 0 0}
.facts dt{font-weight:700;color:var(--mut);font-size:15px}.facts dd{margin:0;font-size:15px}
@media(max-width:560px){.facts dl{grid-template-columns:1fr}.facts dd{margin-bottom:6px}}
/* texto de página */
.prose{max-width:780px}.prose p{margin:0 0 16px}
/* faq */
details{border-bottom:1px solid var(--line);padding:16px 0}
summary{font-weight:700;cursor:pointer;list-style:none;display:flex;justify-content:space-between;gap:12px;font-size:18px;color:var(--navy)}
summary::-webkit-details-marker{display:none}
summary:after{content:"+";font-size:24px;line-height:1;color:var(--red)}
details[open] summary:after{content:"–"}
details p{margin:10px 0 0;color:var(--mut)}
/* cta */
.cta{background:var(--red);color:#fff}
.cta .wrap{display:flex;flex-wrap:wrap;align-items:center;justify-content:space-between;gap:20px;padding-top:40px;padding-bottom:40px}
.cta h2{font-size:34px;margin:0 0 4px;text-transform:uppercase}.cta p{margin:0;color:#FFE3E7}
.cta .big{display:flex;align-items:center;gap:10px;font-family:"Barlow Condensed",Arial,sans-serif;font-size:40px;font-weight:700;color:#fff;text-decoration:none}
/* pie */
footer{background:var(--navy);color:#B9C6D6;font-size:15px;padding:48px 0 24px}
footer .cols{display:grid;gap:28px}
footer .fh{color:#fff;font-family:"Barlow Condensed",Arial,sans-serif;font-size:19px;text-transform:uppercase;letter-spacing:.6px;margin:0 0 12px}
footer a{color:#E6ECF3;text-decoration:none}footer a:hover{text-decoration:underline}
footer ul{list-style:none;padding:0;margin:0}footer li.soc{display:flex;gap:10px;margin-top:12px}footer li.soc a{display:inline-flex;align-items:center;justify-content:center;width:38px;height:38px;border-radius:50%}footer li.soc a:hover{opacity:.85;text-decoration:none}footer li{margin:5px 0}
footer .legalrow{border-top:1px solid rgba(255,255,255,.12);margin-top:32px;padding-top:18px;font-size:13.5px}
footer .legalrow a{margin-right:16px;text-decoration:underline}
.fbrand{display:flex;align-items:center;gap:10px;color:#fff;margin-bottom:12px}
.fbrand b{font-family:"Barlow Condensed",Arial,sans-serif;font-size:22px;text-transform:uppercase}
/* legal */
.legal{max-width:760px}.legal h1{color:var(--navy);font-size:40px;text-transform:uppercase}.legal h2{font-size:24px;color:var(--navy);margin-top:28px}
.center{text-align:center}.center .btns{justify-content:center}
/* aviso instalar app */
.appbar{position:fixed;left:12px;right:12px;bottom:66px;z-index:31;display:none;align-items:center;gap:12px;background:#fff;border:1px solid var(--line);border-radius:8px;padding:10px 12px;box-shadow:0 8px 26px rgba(11,37,69,.22);font-size:15px;line-height:1.3}
.appbar.on{display:flex}
.appbar img{width:40px;height:40px;border-radius:9px;flex:none}.appbar b{display:block;color:var(--navy)}.appbar span{color:var(--mut);font-size:13.5px}
.appbar .ok{margin-left:auto;background:var(--navy);color:#fff;border:0;border-radius:4px;padding:9px 14px;font-weight:700;font-family:inherit;font-size:15px;cursor:pointer;white-space:nowrap}
.appbar .x{background:none;border:0;color:var(--mut);font-size:22px;line-height:1;padding:4px;cursor:pointer}
@media(min-width:900px){.appbar{left:auto;right:20px;bottom:20px;max-width:380px}}
/* barra móvil */
.bar{position:fixed;left:0;right:0;bottom:0;display:grid;grid-template-columns:3fr 2fr;z-index:30;box-shadow:0 -3px 12px rgba(0,0,0,.18)}
.bar a{display:flex;align-items:center;justify-content:center;gap:8px;padding:15px 6px;color:#fff;font-weight:700;text-decoration:none;font-size:17px;white-space:nowrap}
.bar .c{background:var(--red)}.bar .f{background:var(--navy)}
@media(min-width:600px) and (max-width:899px){.g5{grid-template-columns:1fr 1fr}}
@media(min-width:1100px){.g5{grid-template-columns:repeat(5,1fr)}.g5 .svc{padding:20px}.g5 .svc h3{font-size:21px}}
.callbtn strong{white-space:nowrap}
.topbar .show-s{display:none}.topbar .lang{display:inline-flex;align-items:center;gap:6px;border:1px solid rgba(255,255,255,.35);padding:3px 10px;border-radius:3px}
@media(max-width:899px){.menu .nl{display:none}.topbar .hide-s{display:none}.topbar .show-s{display:inline}}
@media(max-width:560px){.callbtn small{display:none}.callbtn{padding:10px 12px}.callbtn strong{font-size:17px}.brand b{font-size:18px}.brand svg{width:34px;height:34px}.brand small{display:none}.hero h1{font-size:34px}h2.t{font-size:30px}}
@media(min-width:900px){
 body{padding-bottom:0}.bar{display:none}
 .hero .wrap{grid-template-columns:minmax(0,1.25fr) minmax(0,1fr);align-items:center;padding-top:72px;padding-bottom:80px}
 .hero h1{font-size:58px}
 .trust .wrap{grid-template-columns:repeat(4,1fr)}
 .g3{grid-template-columns:repeat(3,1fr)}.g2{grid-template-columns:1fr 1fr}.g5{grid-template-columns:repeat(3,1fr)}
 .split{grid-template-columns:1fr 1fr;gap:56px}
 .areas{grid-template-columns:repeat(3,1fr)}
 .zmap{grid-template-columns:minmax(0,1fr) minmax(0,1fr)}.zmap .areas{grid-template-columns:1fr 1fr}
 footer .cols{grid-template-columns:1.4fr 1fr 1fr 1fr}
}
"""

FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
         '<link href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@600;700&family=Source+Sans+3:wght@400;600;700&display=swap" rel="stylesheet">')


def gmap(lang, place, zoom=12):
    """Mapa de Google de la ZONA (sin pin de dirección). Carga diferida para no afectar la velocidad."""
    u = UI[lang]
    q = quote_plus(f"{place}, {S['county']} County, {S['state']}")
    return (f'<div><div class="mapbox"><iframe src="https://maps.google.com/maps?q={q}&amp;z={zoom}&amp;output=embed" '
            f'title="{E(u["map_t"].format(place=place))}" loading="lazy" referrerpolicy="no-referrer-when-downgrade" allowfullscreen></iframe></div>'
            f'<p class="mapnote">{u["map_note"]}</p></div>')

def schema_business(lang):
    n = NICHE[lang]
    return {
        "@context": "https://schema.org", "@type": "HVACBusiness",
        "name": S["brand"], "url": S["domain"] + base(lang), "image": IMG_HERO,
        "telephone": S["phone_tel"], "email": S["email"],
        "description": fmt(n["hero_sub"]),
        "areaServed": [{"@type": "Place", "name": f"{a[0]}, {S['state']}"} for a in AREAS] +
                      [{"@type": "City", "name": f"{S['city']}, {S['state']}"}],
        "openingHoursSpecification": [{"@type": "OpeningHoursSpecification",
            "dayOfWeek": ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"],
            "opens": "07:00", "closes": "22:00"}],
        "priceRange": "$$", "knowsLanguage": ["es", "en"],
        "sameAs": [u for _, u in S.get("social", [])],
        "hasOfferCatalog": {"@type": "OfferCatalog", "name": UI[lang]["svc_t"],
            "itemListElement": [{"@type": "Offer", "itemOffered": {"@type": "Service", "name": svc(lang, sv)["name"],
                                 "url": S["domain"] + svc_path(lang, sv)}} for sv in SERVICES]},
    }

def schema_website(lang):
    # le dice a Google el nombre del sitio que debe mostrar en los resultados
    return {"@context": "https://schema.org", "@type": "WebSite", "name": S["brand"],
            "alternateName": S["domain"].split("//")[1], "url": S["domain"] + "/", "inLanguage": lang}

def schema_faq(lang):
    return {"@context": "https://schema.org", "@type": "FAQPage",
            "mainEntity": [{"@type": "Question", "name": fmt(q),
                            "acceptedAnswer": {"@type": "Answer", "text": fmt(a)}} for q, a in NICHE[lang]["faq"]]}

ALTS = {}
PAGE_IMG = {}
def head(lang, title, desc, path, alt_path, schemas, img=None):
    other = "en" if lang == "es" else "es"
    es_path = path if lang == "es" else alt_path
    ALTS[path] = {"es": es_path, "en": path if lang == "en" else alt_path}
    if len(title) > 62 and title.endswith(" | " + S["brand"]): title = title[: -len(" | " + S["brand"])]
    extra = ""
    if img: PAGE_IMG[path] = img
    if img and local_name(img):
        b = img[: -len(".jpg")]
        extra += f'<link rel="preload" as="image" type="image/webp" imagesrcset="{b}-800.webp 800w, {b}.webp {IMG_W.get(local_name(img), 1200)}w" imagesizes="100vw" fetchpriority="high">\n'
    elif img: extra += f'<link rel="preload" as="image" href="{img}" fetchpriority="high">\n'
    if S.get("gsc_verification"): extra += f'<meta name="google-site-verification" content="{S["gsc_verification"]}">\n'
    if S.get("ga4_id"):
        extra += (f'<script async src="https://www.googletagmanager.com/gtag/js?id={S["ga4_id"]}"></script>'
                  f'<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments)}}gtag("js",new Date());gtag("config","{S["ga4_id"]}");'
                  'document.addEventListener("click",function(e){var a=e.target.closest("a");if(!a)return;var h=a.getAttribute("href")||"";'
                  'if(h.indexOf("tel:")===0)gtag("event","llamada",{link_url:h});if(h.indexOf("#form")>-1)gtag("event","pedir_cita",{link_url:h});});'
                  'document.addEventListener("submit",function(e){if(e.target&&e.target.name==="lead")gtag("event","formulario",{idioma:document.documentElement.lang});});</script>\n')
    ld = "".join(f'<script type="application/ld+json">{json.dumps(s, ensure_ascii=False)}</script>' for s in schemas)
    return f"""<!doctype html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{E(title)}</title>
<meta name="description" content="{E(desc)}">
<link rel="canonical" href="{S['domain']}{path}">
<link rel="alternate" hreflang="{lang}" href="{S['domain']}{path}">
<link rel="alternate" hreflang="{other}" href="{S['domain']}{alt_path}">
<link rel="alternate" hreflang="x-default" href="{S['domain']}{es_path}">
<meta property="og:title" content="{E(title)}">
<meta property="og:description" content="{E(desc)}">
<meta property="og:url" content="{S['domain']}{path}">
<meta property="og:image" content="{img or IMG_HERO}">
<meta property="og:locale" content="{'es_US' if lang=='es' else 'en_US'}">
{extra}
<meta property="og:type" content="website">
<meta name="theme-color" content="#0B2545">
<meta name="site-version" content="{SITE_VERSION}">
<link rel="icon" href="/favicon.ico" sizes="48x48">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="icon" href="/favicon-96.png" type="image/png" sizes="96x96">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<link rel="manifest" href="{'/manifest.webmanifest' if lang == 'es' else '/en/manifest.webmanifest'}">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-title" content="{E(APP_NAME)}">
<meta name="apple-mobile-web-app-status-bar-style" content="default">
{FONTS}
<style>{CSS}</style>
{ld}
</head>
<body>"""

def header(lang, alt_path):
    u = UI[lang]
    nav = "".join(f'<a class="nl" href="{base(lang)}{h}">{t}</a>' for t, h in u["nav"])
    return f"""<div class="topbar"><div class="wrap"><span><span class="hide-s">{u['topbar']}</span><span class="show-s">Se habla español</span></span>
<a class="lang" href="{alt_path}" hreflang="{'en' if lang=='es' else 'es'}">{icon('chat', 15)} {u['toggle']}</a></div></div>
<header class="hdr"><div class="wrap">
<a class="brand" href="{base(lang)}">{LOGO}<span><b>{brand_html()}</b><small>{u['tagline']}</small></span></a>
<nav class="menu">{nav}
<a class="callbtn" href="tel:{S['phone_tel']}">{icon('phone', 22)}<span><small>{u['call_today']}</small><strong>{S['phone_display']}</strong></span></a></nav>
</div></header>"""

def form(lang):
    u, n = UI[lang], NICHE[lang]
    opts = "".join(f"<option>{E(p[1])}</option>" for p in n["problems"]) + f"<option>{u['other']}</option>"
    return f"""<div class="card-form" id="form">
<h2>{u['form_title']}</h2><p>{u['form_sub']}</p>
<form name="lead" method="POST" action="{LEGAL[lang]['thanks']}" data-netlify="true" netlify-honeypot="bot-field">
<input type="hidden" name="form-name" value="lead"><input type="hidden" name="idioma" value="{lang}">
<p class="hide"><label>No llenar <input name="bot-field"></label></p>
<label for="n-{lang}">{u['name']}</label><input id="n-{lang}" name="nombre" required autocomplete="name">
<label for="p-{lang}">{u['phone']}</label><input id="p-{lang}" name="telefono" type="tel" required autocomplete="tel" inputmode="tel" placeholder="(305) 000-0000">
<label for="q-{lang}">{u['problem']}</label><select id="q-{lang}" name="problema" required><option value="">{u['choose']}</option>{opts}</select>
<button class="btn b-call" type="submit">{u['send']}</button>
<p class="note">{u['privacy_note']}</p>
</form></div>"""

def hero(lang, h1, sub, crumb="", eyebrow=None, img=None):
    u = UI[lang]
    ticks = "".join(f"<li>{icon('check', 18)}{t}</li>" for t in u["trust"][:3])
    eb = f'<span class="eyebrow">{E(eyebrow)}</span>' if eyebrow else ""
    zl = " · ".join(x[0] for x in AREAS[:4])
    zones = f'<p class="zones">{icon("pin", 16)}<span>{zl} {"y todo" if lang == "es" else "and all of"} {S["city"]}</span></p>'
    return f"""<main><section class="hero">{picture(img or IMG_HERO, img_alt(img or IMG_HERO, lang, ""), 1600, 900, lazy=False, sizes="100vw", cls="hbg", high=True)}<div class="wrap"><div>{crumb}{eb}
<h1>{E(h1)}</h1><p class="sub">{E(sub)}</p>
<div class="btns"><a class="btn b-call" href="tel:{S['phone_tel']}">{icon('phone', 20)} {u['call']} {S['phone_display']}</a></div>
<ul class="ticks">{ticks}</ul>{zones}</div>{form(lang)}</div></section>
<div class="trust"><div class="wrap">{''.join(f'<div>{icon(i, 28)}<p style="margin:0"><b>{t}</b><span>{d}</span></p></div>' for i, t, d in u['trust_icons'])}</div></div>"""

SHORT = {
 "es": {"ac-no-enfria": "Sale aire tibio o no llega a la temperatura.", "ac-gotea-agua": "Agua en el piso o el techo, casi siempre el drenaje.",
        "ac-hace-ruido": "Golpes, zumbidos o chirridos en el equipo.", "ac-no-enciende": "El equipo no arranca o se apaga solo.",
        "mantenimiento-ac": "Limpieza y revisión para que no falle en verano.", "instalacion-ac": "Equipos nuevos y eficientes, con permiso incluido.",
        "recarga-gas-ac": "Detección de fugas y recarga de refrigerante.", "limpieza-ductos": "Aire más limpio y sin olor a humedad.",
        "termostato": "Reparación e instalación, también inteligentes.", "mini-split": "Reparación, limpieza e instalación.",
        "reparacion-ac-emergencia": "Sin AC en pleno calor, agua cayendo u olor a quemado.", "calidad-aire-humedad": "Casa pegajosa, olor a moho, deshumidificadores y luz UV."},
 "en": {"ac-no-enfria": "Warm air, or it never reaches the set temperature.", "ac-gotea-agua": "Water on the floor or ceiling, usually the drain.",
        "ac-hace-ruido": "Banging, buzzing or squealing from the unit.", "ac-no-enciende": "Unit won't start or shuts off by itself.",
        "mantenimiento-ac": "Cleaning and check-up so it won't fail in summer.", "instalacion-ac": "New efficient systems, permit included.",
        "recarga-gas-ac": "Leak detection and refrigerant recharge.", "limpieza-ductos": "Cleaner air with no musty smell.",
        "termostato": "Repair and installation, including smart models.", "mini-split": "Repair, cleaning and installation.",
        "reparacion-ac-emergencia": "No AC in the heat, water dripping or a burning smell.", "calidad-aire-humedad": "Sticky house, musty smell, dehumidifiers and UV lights."},
}

def services_grid(lang, skip=None, title=None, soft=False):
    u = UI[lang]
    cards = ""
    for sv in SERVICES:
        if sv[0] == skip: continue
        d = svc(lang, sv)
        short = SHORT[lang][sv[0]]
        cards += (f'<a class="svc" href="{svc_path(lang, sv)}"><span class="ibox">{icon(SVC_ICON[sv[0]], 26)}</span>'
                  f'<h3>{E(d["name"])}</h3><p>{E(short)}</p><span class="more">{u["more"]} {icon("arrow", 16)}</span></a>')
    return f"""<section class="blk{' soft' if soft else ''}" id="servicios"><div class="wrap">
<div class="head"><p class="kicker">{S['city']}, FL</p><h2 class="t">{title or u['svc_t']}</h2><p class="s">{fmt(u['svc_s'])}</p></div>
<div class="grid g5">{cards}</div></div></section>"""

def why(lang):
    u = UI[lang]
    lis = "".join(f"<li>{icon('check', 20)}<span>{x}</span></li>" for x in u["why_list"])
    return f"""<section class="blk soft"><div class="wrap split">
<div class="photo">{picture(IMG_UNIT, img_alt(IMG_UNIT, lang, ""), 1000, 750, sizes="(max-width: 900px) 100vw, 560px")}</div>
<div><p class="kicker">{S['brand']}</p><h2 class="t">{u['why_t']}</h2><p>{u['why_p']}</p><ul class="checks">{lis}</ul>
<p class="honest">{fmt(u['disclaimer'])}</p>
<div class="btns" style="margin-top:18px"><a class="btn b-call" href="tel:{S['phone_tel']}">{icon('phone', 20)} {S['phone_display']}</a></div></div>
</div></section>"""

def how(lang):
    u = UI[lang]
    st = "".join(f'<div class="step"><div class="n">0{a}</div><h3>{b}</h3><p>{c}</p></div>' for a, b, c in u["how"])
    return f"""<section class="blk"><div class="wrap"><div class="head"><h2 class="t">{u['how_t']}</h2></div>
<div class="grid g3 steps">{st}</div></div></section>"""

LOCAL_BLOCK = {
 "es": ("Servicio de aire acondicionado en {city}",
        ["Si buscas reparación de AC cerca de ti en {city}, te conectamos con técnicos de aire acondicionado licenciados y asegurados que trabajan en tu zona. "
         "Atendemos reparaciones urgentes el mismo día según disponibilidad, mantenimiento, instalación de equipos nuevos y mini splits, en casas, townhouses y condominios.",
         "Precio justo y claro: el técnico te da el presupuesto antes de empezar, sin cargos escondidos. Si buscas una compañía de aire acondicionado en {city} que conteste el teléfono y te mande a alguien de confianza, ese es nuestro trabajo. Damos servicio de HVAC en {city}, West Kendall, The Hammocks, "
         "Kendale Lakes, Pinecrest y el resto del suroeste de Miami-Dade, en español o en inglés."]),
 "en": ("Air conditioning service in {city}",
        ["If you're looking for AC repair near you in {city}, we connect you with licensed and insured air conditioning technicians who work in your area. "
         "We handle urgent same-day repairs based on availability, maintenance, new system installation and mini splits, for houses, townhouses and condos.",
         "Fair, clear pricing: the technician gives you a quote before starting, with no hidden fees. If you're looking for an AC company in {city} that answers the phone and sends someone you can trust, that's what we do. We provide HVAC service in {city}, West Kendall, The Hammocks, "
         "Kendale Lakes, Pinecrest and the rest of southwest Miami-Dade, in English or Spanish."]),
}

PRICE_ROWS = [("Visita de diagnóstico", "Diagnostic visit", "$75 – $150"),
              ("Destapar la línea de drenaje", "Clearing the drain line", "$75 – $250"),
              ("Cambiar el capacitor", "Replacing the capacitor", "$100 – $400"),
              ("Recarga de refrigerante (sin la fuga)", "Refrigerant recharge (leak not included)", "$100 – $600"),
              ("Reparar una fuga de refrigerante", "Repairing a refrigerant leak", "$200 – $1,500"),
              ("Motor del ventilador interior", "Indoor blower motor", "$200 – $900"),
              ("Serpentín del evaporador", "Evaporator coil", "$400 – $2,700"),
              ("Compresor", "Compressor", "$600 – $3,000"),
              ("Equipo central nuevo (3 a 5 toneladas)", "New central system (3 to 5 tons)", "$8,500 – $13,500")]
PRICE_TXT = {
 "es": ("¿Cuánto cuesta reparar el aire acondicionado en {city}?",
        "Precios de referencia para que sepas qué esperar. El precio final lo da el técnico después de revisar el equipo, siempre antes de empezar.",
        "Reparación", "Precio de referencia",
        "Rangos de guías de costos de EE. UU. publicadas en 2026. En Miami varían según la empresa, la hora y la urgencia. La mayoría de las reparaciones quedan entre $250 y $700.",
        "Ver la guía completa de precios"),
 "en": ("How much does AC repair cost in {city}?",
        "Reference prices so you know what to expect. The final price comes from the technician after checking the unit, always before any work starts.",
        "Repair", "Reference price",
        "Ranges from U.S. cost guides published in 2026. In Miami they vary by company, time of day and urgency. Most repairs land between $250 and $700.",
        "See the full price guide"),
}
def prices(lang):
    t, intro, c1, c2, note, more = PRICE_TXT[lang]
    rows = "".join(f"<tr><td>{E(a if lang == 'es' else b)}</td><td>{c}</td></tr>" for a, b, c in PRICE_ROWS)
    art = next((x for x in ARTICLES if x[0] == "cuanto-cuesta-reparar-aire-acondicionado-miami"), None)
    link = f' <a href="{blog_path(lang, art)}">{more} →</a>' if art else ""
    return (f'<section class="blk soft" id="precios"><div class="wrap prose"><h2 class="t">{E(fmt(t))}</h2><p>{E(intro)}</p>'
            f'<div class="ptw"><table class="ptable"><thead><tr><th>{c1}</th><th>{c2}</th></tr></thead><tbody>{rows}</tbody></table></div>'
            f'<p class="pnote">{E(note)}{link}</p></div></section>')

def all_zips():
    seen = []
    for slug in [a[1] for a in AREAS]:
        for z in AREA_LOCAL.get(slug, ([],))[0]:
            if z not in seen: seen.append(z)
    return sorted(seen)

def local_block(lang):
    t, ps = LOCAL_BLOCK[lang]
    return (f'<section class="blk"><div class="wrap prose"><h2 class="t">{fmt(t)}</h2>'
            + "".join(f"<p>{E(fmt(p))}</p>" for p in ps)
            + f"<p><b>{'Códigos postales que cubrimos' if lang == 'es' else 'ZIP codes we cover'}:</b> {', '.join(all_zips())}.</p>"
            + "</div></section>")

def areas(lang, skip=None, title=None):
    u = UI[lang]
    items = "".join(f'<li><a href="{area_path(lang, a[1])}">{icon("pin", 18)}{a[0]}</a></li>' for a in AREAS if a[1] != skip)
    return f"""<section class="blk soft" id="zonas"><div class="wrap">
<div class="head"><h2 class="t">{title or u['areas_t']}</h2><p class="s">{fmt(u['areas_s'])}</p></div>
<div class="zmap"><ul class="areas">{items}</ul>{gmap(lang, S['city'], 12)}</div></div></section>"""

def faq(lang):
    u = UI[lang]
    items = "".join(f"<details><summary>{E(fmt(q))}</summary><p>{E(fmt(a))}</p></details>" for q, a in NICHE[lang]["faq"])
    return f'<section class="blk" id="preguntas"><div class="wrap prose"><h2 class="t">{u["faq_t"]}</h2>{items}</div></section>'

def cta(lang):
    u = UI[lang]
    return f"""<section class="cta"><div class="wrap"><div><h2>{u['cta_t']}</h2><p>{u['cta_s']}</p></div>
<a class="big" href="tel:{S['phone_tel']}">{icon('phone', 32)} {S['phone_display']}</a></div></section>"""

# Iconos de redes: Facebook e Instagram de Simple Icons (CC0); Nextdoor con una casita genérica en su color
SOCIAL_ICONS = {"Facebook": ["0866FF", "M9.101 23.691v-7.98H6.627v-3.667h2.474v-1.58c0-4.085 1.848-5.978 5.858-5.978.401 0 .955.042 1.468.103a8.68 8.68 0 0 1 1.141.195v3.325a8.623 8.623 0 0 0-.653-.036 26.805 26.805 0 0 0-.733-.009c-.707 0-1.259.096-1.675.309a1.686 1.686 0 0 0-.679.622c-.258.42-.374.995-.374 1.752v1.297h3.919l-.386 2.103-.287 1.564h-3.246v8.245C19.396 23.238 24 18.179 24 12.044c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.628 3.874 10.35 9.101 11.647Z"], "Instagram": ["FF0069", "M7.0301.084c-1.2768.0602-2.1487.264-2.911.5634-.7888.3075-1.4575.72-2.1228 1.3877-.6652.6677-1.075 1.3368-1.3802 2.127-.2954.7638-.4956 1.6365-.552 2.914-.0564 1.2775-.0689 1.6882-.0626 4.947.0062 3.2586.0206 3.6671.0825 4.9473.061 1.2765.264 2.1482.5635 2.9107.308.7889.72 1.4573 1.388 2.1228.6679.6655 1.3365 1.0743 2.1285 1.38.7632.295 1.6361.4961 2.9134.552 1.2773.056 1.6884.069 4.9462.0627 3.2578-.0062 3.668-.0207 4.9478-.0814 1.28-.0607 2.147-.2652 2.9098-.5633.7889-.3086 1.4578-.72 2.1228-1.3881.665-.6682 1.0745-1.3378 1.3795-2.1284.2957-.7632.4966-1.636.552-2.9124.056-1.2809.0692-1.6898.063-4.948-.0063-3.2583-.021-3.6668-.0817-4.9465-.0607-1.2797-.264-2.1487-.5633-2.9117-.3084-.7889-.72-1.4568-1.3876-2.1228C21.2982 1.33 20.628.9208 19.8378.6165 19.074.321 18.2017.1197 16.9244.0645 15.6471.0093 15.236-.005 11.977.0014 8.718.0076 8.31.0215 7.0301.0839m.1402 21.6932c-1.17-.0509-1.8053-.2453-2.2287-.408-.5606-.216-.96-.4771-1.3819-.895-.422-.4178-.6811-.8186-.9-1.378-.1644-.4234-.3624-1.058-.4171-2.228-.0595-1.2645-.072-1.6442-.079-4.848-.007-3.2037.0053-3.583.0607-4.848.05-1.169.2456-1.805.408-2.2282.216-.5613.4762-.96.895-1.3816.4188-.4217.8184-.6814 1.3783-.9003.423-.1651 1.0575-.3614 2.227-.4171 1.2655-.06 1.6447-.072 4.848-.079 3.2033-.007 3.5835.005 4.8495.0608 1.169.0508 1.8053.2445 2.228.408.5608.216.96.4754 1.3816.895.4217.4194.6816.8176.9005 1.3787.1653.4217.3617 1.056.4169 2.2263.0602 1.2655.0739 1.645.0796 4.848.0058 3.203-.0055 3.5834-.061 4.848-.051 1.17-.245 1.8055-.408 2.2294-.216.5604-.4763.96-.8954 1.3814-.419.4215-.8181.6811-1.3783.9-.4224.1649-1.0577.3617-2.2262.4174-1.2656.0595-1.6448.072-4.8493.079-3.2045.007-3.5825-.006-4.848-.0608M16.953 5.5864A1.44 1.44 0 1 0 18.39 4.144a1.44 1.44 0 0 0-1.437 1.4424M5.8385 12.012c.0067 3.4032 2.7706 6.1557 6.173 6.1493 3.4026-.0065 6.157-2.7701 6.1506-6.1733-.0065-3.4032-2.771-6.1565-6.174-6.1498-3.403.0067-6.156 2.771-6.1496 6.1738M8 12.0077a4 4 0 1 1 4.008 3.9921A3.9996 3.9996 0 0 1 8 12.0077"], "Nextdoor": ["8ED500", "M12 3 2 12h3v8h5v-6h4v6h5v-8h3z"]}

def footer(lang):
    u = UI[lang]
    al = "".join(f'<li><a href="{area_path(lang, a[1])}">{a[0]}</a></li>' for a in AREAS)
    sl = "".join(f'<li><a href="{svc_path(lang, sv)}">{E(svc(lang, sv)["name"])}</a></li>' for sv in SERVICES)
    social_li = ('<li class="soc">' + "".join(
        f'<a href="{h}" rel="noopener" target="_blank" aria-label="{n}" title="{n}" style="background:#{SOCIAL_ICONS[n][0]}">'
        f'<svg viewBox="0 0 24 24" width="20" height="20" aria-hidden="true"><path fill="#fff" d="{SOCIAL_ICONS[n][1]}"/></svg></a>'
        for n, h in S.get("social", []) if n in SOCIAL_ICONS) + "</li>") if S.get("social") else ""
    return f"""<footer><div class="wrap"><div class="cols">
<div><div class="fbrand">{LOGO}<b>{E(S['brand'])}</b></div><p>{fmt(u['disclaimer'])}</p></div>
<div><h2 class="fh">{u["svc_word"]}</h2><ul>{sl}</ul></div>
<div><h2 class="fh">{u["areas_word"]}</h2><ul>{al}</ul></div>
<div><h2 class="fh">{u["contact_t"]}</h2><ul><li><a href="tel:{S['phone_tel']}">{S['phone_display']}</a></li>
<li><a href="mailto:{S['email']}">{S['email']}</a></li><li><a href="{blog_path(lang)}">{'Consejos de AC' if lang == 'es' else 'AC tips'}</a></li><li>{u['hours']}</li><li>{S['city']}, {S['county']} County, {S['state']}</li>{social_li}</ul></div>
</div>
<div class="legalrow"><a href="{ABOUT[lang]['slug']}">{ABOUT[lang]['title']}</a><a href="{LEGAL[lang]['privacy']}">{u['privacy']}</a><a href="{LEGAL[lang]['terms']}">{u['terms']}</a>
<span>© {datetime.date.today().year} {S['operator']}</span></div>
</div></footer>
<div class="bar"><a class="c" href="tel:{S['phone_tel']}">{icon('phone', 20)} {u['call']}</a><a class="f" href="#form">{icon('check', 20)} {u['book']}</a></div>
{app_block(lang)}
</body></html>"""

# ============================================================
#  APP INSTALABLE (PWA) — versión 11
#  La web se instala en el teléfono con icono propio. Abre a pantalla completa,
#  el botón Llamar sigue funcionando y sin internet muestra el teléfono.
# ============================================================
APP_NAME = S["brand"].replace(" Repairs", "")  # nombre corto bajo el icono: "Kendall AC"
APP_TXT = {
 "es": {"t": "Instala la app de {brand}", "s": "Llama en un toque cuando tu AC falle.", "ok": "Instalar",
        "ios": "En el iPhone: toca Compartir y luego «Agregar a inicio».", "close": "Cerrar",
        "off_t": "Sin conexión", "off_p": "No hay internet ahora mismo, pero puedes llamarnos igual. La llamada funciona sin datos.",
        "sc_call": "Pedir cita", "sc_tips": "Consejos de AC"},
 "en": {"t": "Install the {brand} app", "s": "Call in one tap when your AC fails.", "ok": "Install",
        "ios": "On iPhone: tap Share, then “Add to Home Screen”.", "close": "Close",
        "off_t": "You're offline", "off_p": "There's no internet right now, but you can still call us. The call works without data.",
        "sc_call": "Book a visit", "sc_tips": "AC tips"},
}

def app_block(lang):
    t = APP_TXT[lang]
    return (f'<div class="appbar" id="appbar" role="dialog" aria-label="{E(fmt(t["t"]))}"><img src="/icon-192.png" alt="{E(S['brand'])}" width="40" height="40" loading="lazy">'
            f'<p style="margin:0"><b>{E(fmt(t["t"]))}</b><span id="appsub">{E(t["s"])}</span></p>'
            f'<button class="ok" id="appok" type="button">{t["ok"]}</button><button class="x" id="appx" type="button" aria-label="{t["close"]}">×</button></div>'
            '<script>(function(){'
            'if("serviceWorker" in navigator)window.addEventListener("load",function(){navigator.serviceWorker.register("/sw.js").catch(function(){})});'
            'var ga=function(n,p){if(window.gtag)gtag("event",n,p||{})};'
            'var app=window.matchMedia("(display-mode: standalone)").matches||navigator.standalone;'
            'if(app){ga("app_abierta");return}'
            'var ls={g:function(k){try{return localStorage.getItem(k)}catch(e){return null}},s:function(k,v){try{localStorage.setItem(k,v)}catch(e){}}};'
            'var n=(+ls.g("kac_vistas")||0)+1;ls.s("kac_vistas",n);'
            'var off=+ls.g("kac_app_no")||0;if(Date.now()-off<2592e6||n<2)return;'  # solo a quien vuelve (2ª página o más), y no si lo cerró hace <30 días
            'var bar=document.getElementById("appbar"),ok=document.getElementById("appok"),ev=null;'
            'var show=function(){setTimeout(function(){bar.classList.add("on");ga("app_aviso")},4000)};'
            'document.getElementById("appx").onclick=function(){bar.classList.remove("on");ls.s("kac_app_no",Date.now())};'
            'window.addEventListener("beforeinstallprompt",function(e){e.preventDefault();ev=e;show()});'
            'ok.onclick=function(){if(ev){ev.prompt();ev.userChoice.then(function(r){ga("app_respuesta",{respuesta:r.outcome});bar.classList.remove("on")})}};'
            'window.addEventListener("appinstalled",function(){ga("app_instalada");bar.classList.remove("on")});'
            'var ios=/iphone|ipad|ipod/i.test(navigator.userAgent)&&!/crios|fxios/i.test(navigator.userAgent);'
            f'if(ios){{document.getElementById("appsub").textContent={json.dumps(t["ios"], ensure_ascii=False)};ok.style.display="none";show()}}'
            '})();</script>')

def app_files():
    for lang in ("es", "en"):
        t, b = APP_TXT[lang], base(lang)
        man = {"name": S["brand"], "short_name": APP_NAME, "lang": lang, "dir": "ltr",
               "description": fmt(NICHE[lang]["hero_sub"]),
               "id": b, "start_url": b + "?utm_source=app&utm_medium=pwa", "scope": "/",
               "display": "standalone", "orientation": "portrait", "background_color": "#FFFFFF", "theme_color": "#0B2545",
               "categories": ["business", "lifestyle"],
               "icons": [{"src": "/icon-192.png", "sizes": "192x192", "type": "image/png", "purpose": "any"},
                         {"src": "/icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any"},
                         {"src": "/icon-maskable-192.png", "sizes": "192x192", "type": "image/png", "purpose": "maskable"},
                         {"src": "/icon-maskable-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable"}],
               "shortcuts": [{"name": t["sc_call"], "url": b + "?utm_source=app&utm_medium=atajo#form",
                              "icons": [{"src": "/icon-192.png", "sizes": "192x192"}]},
                             {"name": t["sc_tips"], "url": blog_path(lang) + "?utm_source=app&utm_medium=atajo",
                              "icons": [{"src": "/icon-192.png", "sizes": "192x192"}]}]}
        write(("" if lang == "es" else "en/") + "manifest.webmanifest", json.dumps(man, ensure_ascii=False, indent=1))
    # página sin conexión (con el teléfono: la llamada funciona sin datos)
    for lang in ("es", "en"):
        t, u = APP_TXT[lang], UI[lang]
        p = "/offline.html" if lang == "es" else "/en/offline.html"
        page = (head(lang, f"{t['off_t']} | {S['brand']}", t["off_p"], p, "/en/offline.html" if lang == "es" else "/offline.html", [])
                .replace("<head>", '<head>\n<meta name="robots" content="noindex">') + header(lang, base("en" if lang == "es" else "es"))
                + f'<main><section class="cta" style="padding:50px 0"><div class="wrap"><div><h1 style="font-size:40px;margin:0 0 6px;text-transform:uppercase">{t["off_t"]}</h1><p>{t["off_p"]}</p></div>'
                f'<a class="big" href="tel:{S["phone_tel"]}">{icon("phone", 32)} {S["phone_display"]}</a></div></section></main>' + footer(lang))
        write(p, page)
    # trabajador de la app: páginas siempre frescas de internet; fotos guardadas; sin internet → página con el teléfono
    pre = ["/", "/en/", "/offline.html", "/en/offline.html", "/icon-192.png", "/favicon.svg", IMG_HERO.replace(S["domain"], "")]
    write("sw.js", f"""// Kendall AC Repairs — app instalable. Generado por build.py (versión {SITE_VERSION}).
var C="kac-v{SITE_VERSION}-{TODAY}",PRE={json.dumps(pre)};
self.addEventListener("install",function(e){{e.waitUntil(caches.open(C).then(function(c){{return c.addAll(PRE)}}).then(function(){{return self.skipWaiting()}}))}});
self.addEventListener("activate",function(e){{e.waitUntil(caches.keys().then(function(k){{return Promise.all(k.filter(function(x){{return x!==C}}).map(function(x){{return caches.delete(x)}}))}}).then(function(){{return self.clients.claim()}}))}});
self.addEventListener("fetch",function(e){{
 var r=e.request,u=new URL(r.url);
 if(r.method!=="GET"||u.pathname.indexOf("/admin")===0)return;
 var mine=u.origin===location.origin,font=/fonts\\.(googleapis|gstatic)\\.com$/.test(u.hostname);
 if(!mine&&!font)return;
 if(r.mode==="navigate"){{
  e.respondWith(fetch(r).then(function(res){{var cp=res.clone();caches.open(C).then(function(c){{c.put(r,cp)}});return res}})
   .catch(function(){{return caches.match(r).then(function(m){{return m||caches.match(u.pathname.indexOf("/en/")===0?"/en/offline.html":"/offline.html")}})}}));
  return;
 }}
 if(font||/\\.(png|jpg|jpeg|webp|svg|ico|woff2?)$/.test(u.pathname)){{
  e.respondWith(caches.match(r).then(function(m){{var f=fetch(r).then(function(res){{if(res.ok||res.type==="opaque"){{var cp=res.clone();caches.open(C).then(function(c){{c.put(r,cp)}})}}return res}}).catch(function(){{return m}});return m||f}}));
 }}
}});
""")

def crumbs_schema(lang, items):
    return {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": i + 1, "name": n, "item": S["domain"] + u} for i, (n, u) in enumerate(items)]}

def faq_block(lang, qs, title):
    items = "".join(f"<details><summary>{E(q)}</summary><p>{E(a)}</p></details>" for q, a in qs)
    schema = {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in qs]}
    return f'<section class="blk" id="preguntas"><div class="wrap prose"><h2 class="t">{E(title)}</h2>{items}</div></section>', schema

def art_img(art, w=1800):
    img = art[7] if len(art) > 7 else ""
    if img: return img if img.startswith("http") else S["domain"] + "/" + img.lstrip("/")
    return px(art[3], w)

def md_inline(t):
    t = E(t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<em>\1</em>", t)
    def link(m):
        txt, url = m.group(1), m.group(2)
        if url.startswith("/"): return f'<a href="{url}">{txt}</a>'
        if url.startswith("http"): return f'<a href="{url}" target="_blank" rel="noopener">{txt}</a>'
        return txt
    return re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", link, t)

def md_to_html(text):
    """Convierte el texto del panel (markdown sencillo) a HTML con el estilo de la web."""
    out, para, items = [], [], []
    def flush():
        if para: out.append("<p>" + md_inline(" ".join(para)) + "</p>"); para.clear()
        if items: out.append('<ul class="checks">' + "".join(f"<li>{icon('check', 20)}<span>{md_inline(x)}</span></li>" for x in items) + "</ul>"); items.clear()
    for raw in (text or "").replace("\r", "").split("\n"):
        ln = raw.strip()
        img = re.match(r"^!\[([^\]]*)\]\(([^)\s]+)\)$", ln)
        if not ln: flush(); continue
        if img:
            flush(); alt = img.group(1) or "Imagen"; src = img.group(2)
            out.append(f'<img src="{E(src)}" alt="{E(alt)}" loading="lazy" width="1200" height="800" style="width:100%;height:auto;border-radius:6px;margin:10px 0 18px">')
        elif ln.startswith("### "): flush(); out.append(f'<h3 style="font-size:24px;color:var(--navy);margin:26px 0 8px;text-transform:uppercase">{md_inline(ln[4:])}</h3>')
        elif ln.startswith("## ") or ln.startswith("# "): flush(); out.append(f'<h2 class="t" style="font-size:30px;margin-top:34px">{md_inline(ln.split(" ", 1)[1])}</h2>')
        elif re.match(r"^([-*+]|\d+[.)])\s+", ln):
            if para: out.append("<p>" + md_inline(" ".join(para)) + "</p>"); para.clear()
            items.append(re.sub(r"^([-*+]|\d+[.)])\s+", "", ln))
        else:
            if items: flush()
            para.append(ln)
    flush()
    return "".join(out)

def blog_path(lang, art=None):
    b = base(lang) + "blog/"
    return b if art is None else b + (art[0] if lang == "es" else art[1]) + "/"

def blog_list(lang, skip=None):
    out = ""
    for art in ARTICLES:
        if art[0] == skip: continue
        a = art[5] if lang == "es" else art[6]
        out += (f'<a class="svc" href="{blog_path(lang, art)}"><div class="photo" style="border-radius:4px;overflow:hidden;aspect-ratio:16/9;background:#D9E1EA;margin-bottom:14px">'
                + picture(art_img(art, 700), img_alt(art_img(art, 700), lang, a["title"]), 1200, 675, style="width:100%;height:100%;object-fit:cover", sizes="(max-width: 800px) 100vw, 400px") + '</div>'
                + f'<h3>{E(a["title"])}</h3><p>{E(a["desc"])}</p><span class="more">{"Leer" if lang == "es" else "Read"} {icon("arrow", 16)}</span></a>')
    return out

def blog_index(lang):
    u, other = UI[lang], ("en" if lang == "es" else "es")
    t = ("Consejos de aire acondicionado" if lang == "es" else "Air conditioning tips")
    title = f"{t} en {S['city']}, FL | {S['brand']}" if lang == "es" else f"{t} in {S['city']}, FL | {S['brand']}"
    desc = (f"Guías sencillas sobre el cuidado y la reparación del aire acondicionado en {S['city']} y Miami-Dade: filtros, mantenimiento, cuándo reparar o cambiar."
            if lang == "es" else f"Simple guides on caring for and repairing your air conditioner in {S['city']} and Miami-Dade: filters, maintenance, when to repair or replace.")
    p, alt = blog_path(lang), blog_path(other)
    intro = ("Respuestas claras a las dudas más comunes sobre el aire acondicionado en el sur de la Florida, escritas para dueños de casa, sin tecnicismos. "
             "Si tu equipo ya está fallando, no esperes: llámanos y te conectamos con un técnico licenciado de tu zona."
             if lang == "es" else
             "Clear answers to the most common air conditioning questions in South Florida, written for homeowners, without jargon. "
             "If your unit is already failing, don't wait: call us and we'll connect you with a licensed technician in your area. New guides are added every month.")
    checklist = (["Revisa el filtro cada mes y cámbialo cada 1 a 3 meses.", "Limpia la línea de drenaje dos veces al año para evitar goteras.",
                  "Mantén dos pies libres alrededor de la unidad exterior.", "Haz un mantenimiento antes de mayo, cuando empieza el calor fuerte.",
                  "Si el AC enfría poco, apágalo y llama antes de que se dañe el compresor.", "Guarda los papeles de la garantía y la fecha de instalación."]
                 if lang == "es" else
                 ["Check the filter monthly and replace it every 1 to 3 months.", "Clear the drain line twice a year to prevent leaks.",
                  "Keep two feet clear around the outdoor unit.", "Schedule a tune-up before May, when the real heat starts.",
                  "If the AC cools poorly, turn it off and call before the compressor gets damaged.", "Keep your warranty papers and installation date."])
    ck_t = "Lista rápida para cuidar tu AC en Miami" if lang == "es" else "Quick checklist for your AC in Miami"
    ck = f'<section class="blk soft"><div class="wrap prose"><h2 class="t">{ck_t}</h2><ul class="checks">' + "".join(f"<li>{icon('check', 20)}<span>{E(x)}</span></li>" for x in checklist) + "</ul></div></section>"
    bc = crumbs_schema(lang, [(u["home"], base(lang)), (t, p)])
    page = (head(lang, title, desc, p, alt, [bc]) + header(lang, alt)
            + f'<main><section class="blk"><div class="wrap"><div class="crumb" style="color:var(--mut)"><a href="{base(lang)}" style="color:var(--navy2)">{u["home"]}</a> › {t}</div>'
            + f'<div class="head"><h1 class="t" style="font-size:44px">{t}</h1><p class="s">{E(intro)}</p></div><div class="grid g3">{blog_list(lang)}</div></div></section>'
            + ck + services_grid(lang) + cta(lang) + "</main>" + footer(lang))
    write(p, page); PAGES.append(p)

def article_page(lang, art):
    u, other = UI[lang], ("en" if lang == "es" else "es")
    a = art[5] if lang == "es" else art[6]
    p, alt = blog_path(lang, art), blog_path(other, art)
    img = art_img(art)
    t_blog = "Consejos" if lang == "es" else "Tips"
    body = (f'<p style="font-size:19px">{md_inline(a["intro"])}</p>' if a["intro"] else "") + md_to_html(a["body"])
    by = {sv[0]: sv for sv in SERVICES}
    rel = "".join(f'<a class="svc" href="{svc_path(lang, by[t])}"><span class="ibox">{icon(SVC_ICON[t], 26)}</span><h3>{E(svc(lang, by[t])["name"])}</h3>'
                  f'<p>{E(SHORT[lang][t])}</p><span class="more">{u["more"]} {icon("arrow", 16)}</span></a>' for t in art[4])
    upd = ("Publicado: " if lang == "es" else "Published: ") + art[2]
    schema = {"@context": "https://schema.org", "@type": "Article", "headline": a["title"], "description": a["desc"], "image": img,
              "datePublished": art[2], "dateModified": art[2], "inLanguage": lang, "mainEntityOfPage": S["domain"] + p,
              "author": author_schema(), "publisher": {"@type": "Organization", "name": S["brand"], "url": S["domain"]}}
    bc = crumbs_schema(lang, [(u["home"], base(lang)), (t_blog, blog_path(lang)), (a["title"], p)])
    page = (head(lang, f"{a['title']} | {S['brand']}", a["desc"], p, alt, [schema, bc], img=img) + header(lang, alt)
            + f'<main><section class="blk"><div class="wrap prose"><div class="crumb" style="color:var(--mut)"><a href="{base(lang)}" style="color:var(--navy2)">{u["home"]}</a> › <a href="{blog_path(lang)}" style="color:var(--navy2)">{t_blog}</a></div>'
            + f'<h1 class="t" style="font-size:42px">{E(a["title"])}</h1><p style="color:var(--mut);font-size:14px">{upd} · {"Por" if lang == "es" else "By"} <a href="{ABOUT[lang]["slug"]}" style="color:var(--navy2)">{E(AUTHOR["name"])}</a></p>'
            + f'<div class="photo" style="border-radius:6px;overflow:hidden;aspect-ratio:16/9;background:#D9E1EA;margin:18px 0 24px">{picture(img, img_alt(img, lang, a["title"]), 1200, 675, lazy=False, style="width:100%;height:100%;object-fit:cover")}</div>'
            + body + author_box(lang)
            + f'<div style="background:var(--navy);color:#fff;border-radius:6px;padding:22px;margin-top:30px"><b style="font-size:20px">{u["cta_t"]}</b><p style="margin:6px 0 14px;color:#C9D4E3">{u["cta_s"]}</p>'
            + f'<a class="btn b-call" href="tel:{S["phone_tel"]}">{icon("phone", 20)} {u["call"]} {S["phone_display"]}</a></div></div></section>'
            + f'<section class="blk soft"><div class="wrap"><div class="head"><h2 class="t">{"Servicios relacionados" if lang == "es" else "Related services"}</h2></div><div class="grid g3">{rel}</div></div></section>'
            + (f'<section class="blk"><div class="wrap"><div class="head"><h2 class="t">{"Más consejos" if lang == "es" else "More tips"}</h2></div><div class="grid g3">{blog_list(lang, skip=art[0])}</div></div></section>' if len(ARTICLES) > 1 else "")
            + cta(lang) + "</main>" + footer(lang))
    write(p, page); PAGES.append(p)

def author_schema():
    a = {"@type": AUTHOR["type"], "name": AUTHOR["name"], "url": S["domain"] + ABOUT["es"]["slug"]}
    if AUTHOR.get("photo"): a["image"] = S["domain"] + AUTHOR["photo"]
    if AUTHOR.get("links"): a["sameAs"] = AUTHOR["links"]
    if AUTHOR["type"] == "Person" and AUTHOR.get("license"): a["hasCredential"] = {"@type": "EducationalOccupationalCredential", "name": "Florida HVAC license " + AUTHOR["license"]}
    return a

def author_box(lang):
    au, ab = AUTHOR[lang], ABOUT[lang]
    photo = (f'<img src="{AUTHOR["photo"]}" alt="{E(AUTHOR["name"])}" width="64" height="64" loading="lazy" style="border-radius:50%;object-fit:cover;flex:none">'
             if AUTHOR.get("photo") else f'<span class="ibox" style="flex:none">{icon("shield", 26)}</span>')
    lic = f' · {"Licencia" if lang == "es" else "License"} {E(AUTHOR["license"])}' if AUTHOR.get("license") else ""
    return (f'<div class="author" style="display:flex;gap:14px;align-items:flex-start;border:1px solid var(--line);border-radius:6px;padding:16px;margin-top:28px">{photo}'
            f'<div><b>{E(AUTHOR["name"])}</b><span style="display:block;color:var(--mut);font-size:14px">{E(au["role"])}{lic}</span>'
            f'<p style="margin:8px 0 6px;font-size:15px">{E(au["bio"])}</p><a href="{ab["slug"]}" style="color:var(--navy2);font-weight:600">{E(ab["title"])} {icon("arrow", 14)}</a></div></div>')

def about_page(lang):
    other = "en" if lang == "es" else "es"
    ab, u = ABOUT[lang], UI[lang]
    p, alt = ab["slug"], ABOUT[other]["slug"]
    kw = dict(brand=S["brand"], city=S["city"], county=S["county"] + " County", operator=S["operator"], email=S["email"], phone=S["phone_display"])
    zone = ", ".join(x[0] for x in AREAS)
    zips = ", ".join(sorted({x[2] for x in AREAS if x[2]}))
    zh, zt = (("Zona que atendemos", f"Atendemos {S['city']} y sus barrios: {zone}. Códigos postales: {zips}. Si vives cerca pero no ves tu comunidad, llámanos igual: casi siempre podemos coordinar un técnico.")
              if lang == "es" else ("Area we serve", f"We serve {S['city']} and its neighborhoods: {zone}. ZIP codes: {zips}. If you live nearby but don't see your community, call anyway: we can almost always coordinate a technician."))
    nh, nt = (("Lo que no hacemos", "No cobramos por la llamada ni por la coordinación, no vendemos tus datos y no enviamos técnicos sin licencia. Si no podemos ayudarte en tu zona o con tu equipo, te lo decimos en la misma llamada.")
              if lang == "es" else ("What we don't do", "We don't charge for the call or the coordination, we don't sell your data and we never send unlicensed technicians. If we can't help in your area or with your unit, we tell you on the same call."))
    secs = list(ab["sections"]) + [(zh, zt), (nh, nt)]
    body = "".join(f"<h2>{E(fmt(h, **kw))}</h2><p>{E(fmt(x, **kw))}</p>" for h, x in secs)
    desc = fmt(ab["intro"], **kw)
    org = {"@context": "https://schema.org", "@type": "AboutPage", "name": ab["title"], "url": S["domain"] + p, "inLanguage": lang,
           "about": {"@type": "HVACBusiness", "name": S["brand"], "url": S["domain"] + base(lang), "telephone": S["phone_tel"], "email": S["email"],
                     "parentOrganization": {"@type": "Organization", "name": S["operator"]},
                     "areaServed": {"@type": "City", "name": f"{S['city']}, {S['state']}"}},
           "author": author_schema()}
    bc = crumbs_schema(lang, [(u["home"], base(lang)), (ab["title"], p)])
    page = (head(lang, f"{ab['title']} | {S['brand']}", desc[:155], p, alt, [org, bc]) + header(lang, alt)
            + f'<main><section class="blk"><div class="wrap prose"><div class="crumb" style="color:var(--mut)"><a href="{base(lang)}" style="color:var(--navy2)">{u["home"]}</a> › {E(ab["title"])}</div>'
            + f'<h1 class="t" style="font-size:42px">{E(ab["h1"])}</h1><p style="font-size:19px">{E(desc)}</p>{body}'
            + f'<h2>{E(ab["author_t"])}</h2>{author_box(lang)}'
            + f'<div style="background:var(--navy);color:#fff;border-radius:6px;padding:22px;margin-top:30px"><b style="font-size:20px">{E(ab["cta"])}</b><p style="margin:12px 0 0">'
            + f'<a class="btn b-call" href="tel:{S["phone_tel"]}">{icon("phone", 20)} {u["call"]} {S["phone_display"]}</a></p></div></div></section>'
            + cta(lang) + "</main>" + footer(lang))
    write(p, page); PAGES.append(p)

def write(path, content):
    full = os.path.join(OUT, path.strip("/"), "index.html") if path.endswith("/") else os.path.join(OUT, path.strip("/"))
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(content)

PAGES = []

def home(lang):
    n, other = NICHE[lang], ("en" if lang == "es" else "es")
    title = (f"{n['service']} en {S['city']}, FL | Técnico Hoy | {S['brand']}" if lang == "es"
             else f"{n['service']} {S['city']}, FL | Same-Day Technician | {S['brand']}")
    desc = (f"¿Tu AC no enfría? Te conectamos hoy con un técnico licenciado en {S['city']}. Precio claro antes de empezar. Se habla español. Llama {S['phone_display']}."
            if lang == "es" else
            f"AC not cooling? We connect you today with a licensed technician in {S['city']}. Clear price up front. Se habla español. Call {S['phone_display']}.")
    h1 = (f"Reparación de aire acondicionado en {S['city']}" if lang == "es" else f"AC repair in {S['city']}, FL")
    eb = n["hero_q"]
    p = base(lang)
    page = (head(lang, title, desc, p, base(other), [schema_website(lang), schema_business(lang), schema_faq(lang)], img=IMG_HERO) + header(lang, base(other))
            + hero(lang, h1, fmt(n["hero_sub"]), eyebrow=eb) + services_grid(lang) + why(lang) + how(lang) + prices(lang) + local_block(lang) + areas(lang) + faq(lang) + cta(lang)
            + "</main>" + footer(lang))
    write(p, page); PAGES.append(p)

def area_page(lang, a):
    n, u, other = NICHE[lang], UI[lang], ("en" if lang == "es" else "es")
    name, slug, zipc, txt_es, txt_en = a
    zl, roads, mark, permit = AREA_LOCAL[slug]
    zipc = zipc or zl[0]
    txt = txt_es if lang == "es" else txt_en
    top, near, housing = AREA_EXTRA[slug]
    house = housing[0] if lang == "es" else housing[1]
    zip_s = f" {zipc}" if zipc else ""
    h1 = u['area_h1'].format(service=n['service'], area=name)
    title = f"{h1}, FL{zip_s} | {S['brand']}"
    by = {sv[0]: sv for sv in SERVICES}
    def low(x): return re.sub(r"\bac\b", "AC", x.lower())
    topn = [low(svc(lang, by[t])["name"]) for t in top]
    desc = (f"{n['service']} en {name}{zip_s}: {topn[0]}, {topn[1]} y {topn[2]}. Técnicos licenciados, se habla español. Llama {S['phone_display']}."
            if lang == "es" else
            f"{n['service']} in {name}{zip_s}: {topn[0]}, {topn[1]} and {topn[2]}. Licensed technicians, se habla español. Call {S['phone_display']}.")
    if len(desc) > 160: desc = desc[:157].rsplit(" ", 1)[0] + "…"
    p, alt = area_path(lang, slug), area_path(other, slug)
    img = px(AREA_POOL[[x[1] for x in AREAS].index(slug) % len(AREA_POOL)])
    crumb = f'<div class="crumb"><a href="{base(lang)}">{u["home"]}</a> › {name}</div>'
    biz = schema_business(lang); biz["url"] = S["domain"] + p
    biz["areaServed"] = [{"@type": "Place", "name": f"{name}, {S['state']}",
                          "address": {"@type": "PostalAddress", "addressLocality": name, "addressRegion": S["state"], "postalCode": z, "addressCountry": "US"}} for z in zl]
    sub = fmt(n["hero_sub"]).replace(S["city"], name, 1)
    names = {x[1]: x[0] for x in AREAS}
    if lang == "es":
        p2 = (f"En {name} atendemos sobre todo {house}. Los problemas que más vemos en la zona son {topn[0]}, {topn[1]} y {topn[2]}. "
              f"El técnico te da el precio antes de empezar, y si el arreglo no vale la pena te lo dice con claridad.")
        top_t, near_t = f"Lo que más nos piden en {name}", "Comunidades cercanas"
        near_p = f"Desde {name} también atendemos " + ", ".join(names[x] for x in near[:-1]) + f" y {names[near[-1]]}."
        qs = [(f"¿Tienen técnicos de aire acondicionado en {name}?", f"Sí. Te conectamos con contratistas licenciados que trabajan en {name} y alrededores, normalmente el mismo día según disponibilidad."),
              (f"¿Cuánto cuesta reparar un AC en {name}?", "Depende de la causa. El técnico revisa el equipo y te da el precio antes de hacer cualquier trabajo; tú decides si lo apruebas."),
              (f"¿Atienden condominios y townhouses en {name}?", f"Sí: casas, townhouses, condominios y mini splits. En {name} trabajamos sobre todo con {house}.")]
        faq_t = f"Preguntas sobre AC en {name}"
    else:
        p2 = (f"In {name} we mostly serve {house}. The most common issues we see in the area are {topn[0]}, {topn[1]} and {topn[2]}. "
              f"The technician gives you the price before starting, and if a repair isn't worth it, they'll tell you plainly.")
        top_t, near_t = f"Most requested in {name}", "Nearby communities"
        near_p = f"From {name} we also serve " + ", ".join(names[x] for x in near[:-1]) + f" and {names[near[-1]]}."
        qs = [(f"Do you have AC technicians in {name}?", f"Yes. We connect you with licensed contractors who work in {name} and nearby, usually same day depending on availability."),
              (f"How much does AC repair cost in {name}?", "It depends on the cause. The technician inspects the unit and gives you the price before any work; you decide whether to approve it."),
              (f"Do you serve condos and townhouses in {name}?", f"Yes: houses, townhouses, condos and mini splits. In {name} we mostly work with {house}.")]
        faq_t = f"AC questions in {name}"
    # bloque de datos locales verificados
    def join(xs, y): return xs[0] if len(xs) == 1 else ", ".join(xs[:-1]) + f" {y} " + xs[-1]
    zips_s, roads_s = ", ".join(zl), join(roads, "y" if lang == "es" else "and")
    mark_l = mark if lang == "es" else mark.replace(" y ", " and ")
    if lang == "es":
        perm = ("los tramita el contratista ante el condado de Miami-Dade, porque es zona no incorporada" if permit == "county"
                else f"los tramita el contratista ante el Departamento de Construcción de {permit}, que tiene su propia oficina")
        local_p = (("Atendemos casas en el código postal " if len(zl) == 1 else "Atendemos casas en los códigos postales ") + f"{zips_s}, alrededor de {roads_s}" + (f", cerca de {mark_l}" if mark else "") + ". "
                   f"Si hay que cambiar el equipo completo, los permisos {perm}.")
        rows = [("Código postal" if len(zl) == 1 else "Códigos postales", zips_s), ("Calles principales", roads_s)] + ([("Cerca de", mark_l)] if mark else []) + \
               [("Permiso para cambiar el AC", "Condado de Miami-Dade" if permit == "county" else f"Municipio de {permit}")]
        box_t = f"Datos de la zona: {name}"
    else:
        perm = ("are pulled by the contractor with Miami-Dade County, since it's an unincorporated area" if permit == "county"
                else f"are pulled by the contractor with the {permit} Building Department, which runs its own office")
        local_p = (("We serve homes in ZIP code " if len(zl) == 1 else "We serve homes in ZIP codes ") + f"{zips_s}, around {roads_s}" + (f", near {mark_l}" if mark else "") + ". "
                   f"If the whole system needs replacing, permits {perm}.")
        rows = [("ZIP code" if len(zl) == 1 else "ZIP codes", zips_s), ("Main roads", roads_s)] + ([("Near", mark_l)] if mark else []) + \
               [("AC replacement permit", "Miami-Dade County" if permit == "county" else f"{permit} (municipal)")]
        box_t = f"Area facts: {name}"
    local_box = (f'<div class="facts"><b>{E(box_t)}</b><dl>' + "".join(f"<dt>{E(k)}</dt><dd>{E(v)}</dd>" for k, v in rows) + "</dl></div>")
    cards = "".join(f'<a class="svc" href="{svc_path(lang, by[t])}"><span class="ibox">{icon(SVC_ICON[t], 26)}</span><h3>{E(svc(lang, by[t])["name"])}</h3>'
                    f'<p>{E(SHORT[lang][t])}</p><span class="more">{u["more"]} {icon("arrow", 16)}</span></a>' for t in top)
    near_links = "".join(f'<li><a href="{area_path(lang, x)}">{icon("pin", 18)}{names[x]}</a></li>' for x in near)
    intro = f"""<section class="blk"><div class="wrap prose"><p class="kicker">{name}, FL{zip_s}</p>
<h2 class="t">{E(h1)}</h2><p>{E(txt)}</p><p>{E(p2)}</p><p>{E(local_p)}</p>{local_box}
<div style="border-left:4px solid var(--red);background:var(--soft);padding:16px 18px;border-radius:4px;margin:6px 0 18px"><b style="color:var(--navy)">{'Consejo para ' + name if lang == 'es' else 'Tip for ' + name}</b><p style="margin:6px 0 0">{E(AREA_TIP[slug][0 if lang == 'es' else 1])}</p></div>
<div class="btns" style="margin-top:8px"><a class="btn b-call" href="tel:{S['phone_tel']}">{icon('phone', 20)} {u['call']} {S['phone_display']}</a></div>
</div></section>
<section class="blk soft"><div class="wrap"><div class="head"><h2 class="t">{E(top_t)}</h2></div><div class="grid g3">{cards}</div></div></section>"""
    faq_html, faq_schema = faq_block(lang, qs, faq_t)
    nearby = f"""<section class="blk soft"><div class="wrap"><div class="head"><h2 class="t">{near_t}</h2><p class="s">{E(near_p)}</p></div><div class="zmap"><ul class="areas">{near_links}</ul>{gmap(lang, name, 13)}</div></div></section>"""
    bc = crumbs_schema(lang, [(u["home"], base(lang)), (name, p)])
    page = (head(lang, title, desc, p, alt, [biz, faq_schema, bc], img=img) + header(lang, alt)
            + hero(lang, h1, sub, crumb, img=img) + intro + how(lang) + faq_html + nearby
            + services_grid(lang) + cta(lang) + "</main>" + footer(lang))
    write(p, page); PAGES.append(p)

def service_page(lang, sv):
    u, other = UI[lang], ("en" if lang == "es" else "es")
    d = svc(lang, sv)
    h1 = fmt(d["h1"])
    title = f"{h1} | {S['brand']}"
    desc = (f"{d['name']} en {S['city']}, FL. Te conectamos con técnicos licenciados. Precio claro antes de empezar. Se habla español. Llama {S['phone_display']}."
            if lang == "es" else
            f"{d['name']} in {S['city']}, FL. We connect you with licensed technicians. Clear price up front. Se habla español. Call {S['phone_display']}.")
    p, alt = svc_path(lang, sv), svc_path(other, sv)
    crumb = f'<div class="crumb"><a href="{base(lang)}">{u["home"]}</a> › {E(d["name"])}</div>'
    schema = {"@context": "https://schema.org", "@type": "Service", "name": d["name"], "serviceType": d["name"],
              "url": S["domain"] + p, "description": d["p1"],
              "areaServed": [{"@type": "Place", "name": f"{a[0]}, {S['state']}"} for a in AREAS],
              "provider": {"@type": "Organization", "name": S["brand"], "telephone": S["phone_tel"], "url": S["domain"] + base(lang)}}
    lis = "".join(f"<li>{icon('check', 20)}<span>{E(x)}</span></li>" for x in d["signs"])
    X = SVC_EXTRA[sv[0]][lang]
    chk = "".join(f"<li>{icon('check', 20)}<span>{E(x)}</span></li>" for x in X["check"])
    T = ({"check": "Qué revisa el técnico", "price": "¿De qué depende el precio?", "tip": "Consejo práctico", "faq": "Preguntas frecuentes"} if lang == "es"
         else {"check": "What the technician checks", "price": "What does the price depend on?", "tip": "Practical tip", "faq": "Frequently asked questions"})
    faq_html, faq_schema = faq_block(lang, X["faq"], f"{T['faq']}: {d['name']}")
    more = f"""<section class="blk soft"><div class="wrap split" style="align-items:start">
<div><h2 class="t">{T['check']}</h2><ul class="checks">{chk}</ul></div>
<div><h2 class="t">{T['price']}</h2><p>{E(X['price'])}</p>
<div style="border-left:4px solid var(--red);background:#fff;padding:16px 18px;border-radius:4px;margin-top:18px"><b style="color:var(--navy)">{T['tip']}</b><p style="margin:6px 0 0">{E(X['tip'])}</p></div></div>
</div></section>"""
    body = f"""<section class="blk"><div class="wrap split">
<div><p class="kicker">{S['city']}, FL</p><h2 class="t">{E(d['name'])}</h2><p>{E(d['p1'])}</p><p>{E(d['p2'])}</p>
<div class="btns" style="margin-top:18px"><a class="btn b-call" href="tel:{S['phone_tel']}">{icon('phone', 20)} {u['call']} {S['phone_display']}</a></div></div>
<div><div class="photo" style="border-radius:6px;overflow:hidden;aspect-ratio:16/10;background:#D9E1EA;margin-bottom:18px">{picture(px(SVC_IMG[sv[0]]), img_alt(px(SVC_IMG[sv[0]]), lang, d['name']), 1200, 675, style="width:100%;height:100%;object-fit:cover", sizes="(max-width: 900px) 100vw, 400px")}</div>
<div style="background:var(--soft);border-radius:6px;padding:26px"><h3 style="font-size:24px;color:var(--navy);margin:0;text-transform:uppercase">{u['signs_t']}</h3><ul class="checks">{lis}</ul></div></div>
</div></section>"""
    bc = crumbs_schema(lang, [(u["home"], base(lang)), (d["name"], p)])
    page = (head(lang, title, desc, p, alt, [schema, faq_schema, bc], img=px(SVC_IMG[sv[0]])) + header(lang, alt)
            + hero(lang, h1, fmt(NICHE[lang]["hero_sub"]), crumb, img=px(SVC_IMG[sv[0]])) + body + more + faq_html + how(lang)
            + services_grid(lang, skip=sv[0], title=u["svc_more"], soft=True) + areas(lang) + cta(lang) + "</main>" + footer(lang))
    write(p, page); PAGES.append(p)

LEGAL_TXT = {
"es": {
 "privacy": ("Política de Privacidad", [
  ("Quiénes somos", "{brand} es un servicio de referidos operado por {op}. Conectamos a personas que necesitan servicio con contratistas independientes con licencia en Florida."),
  ("Qué datos recogemos", "Nombre, teléfono, el problema que nos describes y, si lo das, tu dirección o código postal. También datos básicos de navegación (páginas visitadas, tipo de dispositivo)."),
  ("Grabación de llamadas", "Las llamadas a nuestro número pueden ser grabadas para control de calidad y para confirmar que tu solicitud se atendió. Se te avisa al inicio de la llamada."),
  ("Para qué los usamos", "Para coordinar tu servicio y contactarte sobre tu solicitud. No vendemos tus datos a listas de marketing."),
  ("Con quién los compartimos", "Con el contratista independiente que atenderá tu servicio, y con proveedores técnicos que hacen funcionar esta web (alojamiento y telefonía)."),
  ("Cuánto tiempo los guardamos", "El tiempo necesario para atender tu solicitud y cumplir obligaciones legales o fiscales."),
  ("Tus derechos", "Puedes pedirnos ver, corregir o borrar tus datos escribiendo a {email}."),
  ("Cambios", "Podemos actualizar esta política. La fecha de la última actualización aparece abajo.")]),
 "terms": ("Términos de Servicio", [
  ("Qué hacemos", "{brand} ({op}) es un servicio de referidos. No somos un contratista de aire acondicionado y no realizamos reparaciones ni instalaciones."),
  ("Quién hace el trabajo", "Los trabajos los realiza un contratista independiente con licencia en Florida. El precio, la garantía y las condiciones del trabajo las acuerdas directamente con él."),
  ("Sin costo para ti", "Usar este servicio para pedir un técnico no tiene costo. Solo pagas al contratista por el trabajo que apruebes."),
  ("Responsabilidad", "{op} no es responsable por el trabajo realizado por los contratistas, aunque solo trabajamos con contratistas que declaran tener licencia y seguro vigentes."),
  ("Ley aplicable", "Estos términos se rigen por las leyes del Estado de Florida, condado de {county}."),
  ("Contacto", "{email}")]),
 "thanks": ("¡Recibido!", "Gracias. Te contactamos muy pronto. Si es urgente, llámanos ahora:"),
},
"en": {
 "privacy": ("Privacy Policy", [
  ("Who we are", "{brand} is a referral service operated by {op}. We connect people who need service with independent Florida-licensed contractors."),
  ("What we collect", "Name, phone, the problem you describe and, if provided, your address or ZIP code. Also basic browsing data (pages visited, device type)."),
  ("Call recording", "Calls to our number may be recorded for quality control and to confirm your request was handled. You are notified at the start of the call."),
  ("How we use it", "To coordinate your service and contact you about your request. We do not sell your data to marketing lists."),
  ("Who we share it with", "The independent contractor who will handle your service, and technical providers that run this website (hosting and phone)."),
  ("How long we keep it", "As long as needed to handle your request and meet legal or tax obligations."),
  ("Your rights", "You can ask to see, correct or delete your data by emailing {email}."),
  ("Changes", "We may update this policy. The last update date appears below.")]),
 "terms": ("Terms of Service", [
  ("What we do", "{brand} ({op}) is a referral service. We are not an air conditioning contractor and do not perform repairs or installations."),
  ("Who does the work", "Work is performed by an independent Florida-licensed contractor. Price, warranty and job terms are agreed directly with them."),
  ("No cost to you", "Using this service to request a technician is free. You only pay the contractor for work you approve."),
  ("Liability", "{op} is not responsible for work performed by contractors, though we only work with contractors who state they hold a current license and insurance."),
  ("Governing law", "These terms are governed by the laws of the State of Florida, {county} County."),
  ("Contact", "{email}")]),
 "thanks": ("Got it!", "Thank you. We'll contact you very soon. If it's urgent, call us now:"),
}}

def legal_pages(lang):
    other = "en" if lang == "es" else "es"
    L = LEGAL_TXT[lang]
    for key in ("privacy", "terms"):
        t, secs = L[key]
        body = "".join(f"<h2>{E(h)}</h2><p>{E(fmt(x, email=S['email'], county=S['county']))}</p>" for h, x in secs)
        p, alt = LEGAL[lang][key], LEGAL[other][key]
        upd = ("Última actualización: " if lang == "es" else "Last updated: ") + TODAY
        bc = crumbs_schema(lang, [(UI[lang]["home"], base(lang)), (t, LEGAL[lang][key])])
        page = (head(lang, f"{t} | {S['brand']}", (f"{t} de {S['brand']}, servicio de referidos de aire acondicionado en {S['city']}, FL, operado por {S['operator']}." if lang == "es" else f"{t} of {S['brand']}, an AC referral service in {S['city']}, FL, operated by {S['operator']}."), p, alt, [bc]) + header(lang, alt)
                + f'<main><section class="blk"><div class="wrap legal"><h1>{t}</h1>{body}<p><em>{upd}</em></p></div></section></main>' + footer(lang))
        write(p, page); PAGES.append(p)
    t, msg = L["thanks"]
    p, alt = LEGAL[lang]["thanks"], LEGAL[other]["thanks"]
    page = (head(lang, f"{t} | {S['brand']}", t, p, alt, []).replace("<head>", '<head>\n<meta name="robots" content="noindex">') + header(lang, alt)
            + f'<main><section class="cta" style="padding:50px 0"><div class="wrap"><div><h1 style="font-size:40px;margin:0 0 6px;text-transform:uppercase">{t}</h1><p>{msg}</p></div>'
            f'<a class="big" href="tel:{S["phone_tel"]}">{S["phone_display"]}</a></div></section></main>' + footer(lang))
    write(p, page)

def extras():
    def alt_links(p):
        a = ALTS.get(p, {})
        return "".join(f'<xhtml:link rel="alternate" hreflang="{l}" href="{S["domain"]}{a[l]}"/>' for l in ("es", "en") if l in a) + \
               (f'<xhtml:link rel="alternate" hreflang="x-default" href="{S["domain"]}{a["es"]}"/>' if "es" in a else "")
    urls = "".join(f"<url><loc>{S['domain']}{p}</loc><lastmod>{TODAY}</lastmod>{alt_links(p)}"
                   + (f"<image:image><image:loc>{PAGE_IMG[p]}</image:loc></image:image>" if p in PAGE_IMG else "") + "</url>\n" for p in PAGES)
    write("sitemap.xml", f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml" xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">\n{urls}</urlset>\n')
    # Netlify lee _headers en despliegues por arrastre (netlify.toml no se usa en ese modo)
    write("_headers", """/*
  X-Content-Type-Options: nosniff
  X-Frame-Options: SAMEORIGIN
  Referrer-Policy: strict-origin-when-cross-origin
  Permissions-Policy: camera=(), microphone=(), geolocation=()
  Strict-Transport-Security: max-age=31536000

/sitemap.xml
  Cache-Control: public, max-age=3600

/sw.js
  Cache-Control: no-cache
  Service-Worker-Allowed: /

/manifest.webmanifest
  Content-Type: application/manifest+json

/en/manifest.webmanifest
  Content-Type: application/manifest+json
""")
    app_files()
    write("robots.txt", f"User-agent: *\nAllow: /\nDisallow: /admin/\nSitemap: {S['domain']}/sitemap.xml\n")
    # Redirecciones 301: versiones anteriores tenían páginas en inglés en la raíz (/ac-repair-tamiami);
    # Google aún las muestra. Se envían a su dirección actual /en/... (solo si la raíz no tiene esa página).
    en_dir = os.path.join(OUT, "en")
    reglas = []
    for slug in sorted(os.listdir(en_dir)) if os.path.isdir(en_dir) else []:
        if slug in ("blog", "index.html") or not os.path.isdir(os.path.join(en_dir, slug)): continue
        if os.path.exists(os.path.join(OUT, slug)): continue
        reglas += [f"/{slug}  /en/{slug}/  301", f"/{slug}/  /en/{slug}/  301"]
    write("_redirects", "\n".join(reglas) + "\n")
    # ficha de salud: la revisión automática semanal la compara con la web publicada
    write("salud.json", json.dumps({"version": SITE_VERSION, "generada": TODAY, "telefono": S["phone_display"],
                                    "telefono_tel": S["phone_tel"], "paginas": len(PAGES),
                                    "ga4": S.get("ga4_id", ""), "revisar": [S["domain"] + p for p in PAGES[:3]] +
                                    [S["domain"] + "/sitemap.xml"]}, ensure_ascii=False, indent=1))
    nf = (head("es", f"Página no encontrada | {S['brand']}", "404", "/404.html", "/en/", []).replace("<head>", '<head>\n<meta name="robots" content="noindex">')
          + header("es", "/en/") + f'<main><section class="cta" style="padding:50px 0"><div class="wrap"><h1 style="font-size:36px;margin:0;text-transform:uppercase">Página no encontrada / Page not found</h1>'
          f'<a class="big" href="tel:{S["phone_tel"]}">{S["phone_display"]}</a><a class="btn b-navy" href="/">Inicio / Home</a></div></section></main>' + footer("es"))
    write("404.html", nf)

if __name__ == "__main__":
    shutil.rmtree(OUT, ignore_errors=True)
    for lang in ("es", "en"):
        home(lang)
        for a in AREAS:
            area_page(lang, a)
        for sv in SERVICES:
            service_page(lang, sv)
        blog_index(lang)
        for art in ARTICLES:
            article_page(lang, art)
        legal_pages(lang)
        about_page(lang)
    extras()
    st = os.path.join(ROOT, "static")
    if os.path.isdir(st): shutil.copytree(st, OUT, dirs_exist_ok=True)
    print(f"Listo: {len(PAGES)} páginas indexables en {OUT}")
