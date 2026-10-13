# kendallacrepairs.com

Web de Kendall AC Repairs (DHY Solutions LLC). Es una web estática generada con Python y publicada en Netlify.

## Cómo funciona
- `config.py`: marca, teléfono, barrios, servicios y preguntas frecuentes.
- `contenido.py`: textos de cada servicio y barrio, y los datos locales verificados.
- `blog/`: un archivo por artículo. Se editan desde **kendallacrepairs.com/admin/**.
- `build.py`: genera todas las páginas en `sitio/`.
- `auditoria.py`: revisa la web. Si hay errores, Netlify no publica el cambio.
- `static/`: archivos que se copian tal cual (el panel `/admin/` y las imágenes subidas en `/uploads/`).

## Publicar
Cada cambio que llega a la rama `main` (desde el panel o desde Claude) hace que Netlify ejecute
`python3 build.py && python3 auditoria.py` y publique la carpeta `sitio/`.

## Probar en tu computadora
    python3 build.py && python3 auditoria.py
