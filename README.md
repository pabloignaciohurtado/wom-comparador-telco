# wom-comparador-telco
Comparador estadístico (Python, sin IA) de la oferta comercial móvil de WOM vs Movistar, Entel y Claro en Chile. Página HTML de una sola pantalla con filtros.

## Estructura
- `data/planes.json`: planes postpago vigentes (fuente y fecha por plan). `verificado: false` marca datos que no se pudieron confirmar en la fuente oficial.
- `data/planes_multilinea.json`: precio de línea adicional por operador.
- `data/stats.json`: generado por `scripts/analysis.py`; no se edita a mano.
- `index.html`: página publicada en GitHub Pages.

## Actualizar precios
1. Editar `data/planes.json` y `data/planes_multilinea.json` (incluye `fecha_actualizacion` y `fuente`).
2. `python3 scripts/validate_data.py`
3. `python3 scripts/analysis.py`
4. Commit en una rama y PR hacia `main`; el CI verifica datos, `stats.json` y la página.
