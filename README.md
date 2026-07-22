# Comparador WOM vs Competencia (Chile)

Página de una sola pantalla (`index.html`) que compara la oferta comercial móvil de **WOM**, **Movistar**, **Entel** y **Claro**: precio, GB, minutos, SMS, roaming y redes sociales gratis, con filtros interactivos y paneles por operador.

Las estadísticas (promedios, mediana, CLP/GB, rankings, correlación datos↔precio) se calculan **100% con Python puro** (`scripts/analysis.py`, sin IA) y se sirven como JSON estático que consume el HTML por `fetch`.

## Estructura

```
index.html            # página única, filtros + paneles + tablas
data/planes.json       # dataset de planes (fuente de verdad, editable a mano)
data/stats.json         # generado por scripts/analysis.py — NO editar a mano
scripts/analysis.py     # calcula las estadísticas desde planes.json
.github/workflows/ci.yml  # valida que stats.json esté al día en cada PR
```

## Actualizar datos

1. Edita `data/planes.json` con los planes/precios nuevos.
2. Corre:
   ```bash
   python3 scripts/analysis.py
   ```
3. Commitea `data/planes.json` y el `data/stats.json` regenerado.
4. Abre un PR — el CI falla si `stats.json` quedó desactualizado respecto a `planes.json`.

## Correr localmente

```bash
python3 -m http.server 8000
# abrir http://localhost:8000
```

## Deploy

Pensado para Vercel (estático, sin build step) o GitHub Pages — solo sirve los archivos tal cual.

## Fuentes

Datos recopilados en julio 2026 desde los sitios oficiales de cada operador (wom.cl, movistar.cl, entel.cl, clarochile.cl) y agregadores especializados (fonochile.com, cuantomecuesta.com, celulares.com). Ver campo `fuente` en cada plan de `data/planes.json`.
