#!/usr/bin/env python3
"""
Analisis estadistico de la oferta comercial movil de WOM vs competencia (Chile).

Objetivo: calcular metricas puramente estadisticas (sin uso de modelos de IA)
a partir de data/planes.json, y dejar el resultado en data/stats.json para
que la pagina HTML lo consuma directamente (fetch), sin recalcular nada del
lado del cliente.

Uso:
    python3 scripts/analysis.py
"""
import json
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INPUT_PATH = ROOT / "data" / "planes.json"
OUTPUT_PATH = ROOT / "data" / "stats.json"


def precio_efectivo(plan):
    """Precio que paga el cliente hoy: promo si existe, si no el regular."""
    return plan["precio_promo"] if plan.get("precio_promo") else plan["precio_regular"]


def precio_por_gb(plan):
    """CLP por GB, solo para planes con tope de datos definido (no ilimitados)."""
    if plan.get("datos_ilimitados") or not plan.get("datos_gb"):
        return None
    return round(precio_efectivo(plan) / plan["datos_gb"], 2)


def resumen_operador(nombre, planes_operador):
    precios = [precio_efectivo(p) for p in planes_operador]
    precios_regulares = [p["precio_regular"] for p in planes_operador]
    ppg = [precio_por_gb(p) for p in planes_operador if precio_por_gb(p) is not None]
    con_roaming = sum(1 for p in planes_operador if p.get("roaming_incluido"))
    con_redes_gratis = sum(1 for p in planes_operador if p.get("redes_sociales_gratis"))
    ilimitados = sum(1 for p in planes_operador if p.get("datos_ilimitados"))

    plan_mas_barato = min(planes_operador, key=precio_efectivo)
    plan_mas_caro = max(planes_operador, key=precio_efectivo)

    return {
        "operador": nombre,
        "cantidad_planes": len(planes_operador),
        "precio_promedio": round(statistics.mean(precios), 0),
        "precio_mediana": round(statistics.median(precios), 0),
        "precio_regular_promedio": round(statistics.mean(precios_regulares), 0),
        "precio_min": min(precios),
        "precio_max": max(precios),
        "desviacion_estandar_precio": round(statistics.pstdev(precios), 1) if len(precios) > 1 else 0.0,
        "precio_por_gb_promedio": round(statistics.mean(ppg), 1) if ppg else None,
        "precio_por_gb_mediana": round(statistics.median(ppg), 1) if ppg else None,
        "pct_planes_con_roaming": round(100 * con_roaming / len(planes_operador), 1),
        "pct_planes_redes_sociales_gratis": round(100 * con_redes_gratis / len(planes_operador), 1),
        "cantidad_planes_datos_ilimitados": ilimitados,
        "plan_mas_barato": {
            "id": plan_mas_barato["id"],
            "nombre": plan_mas_barato["nombre"],
            "precio": precio_efectivo(plan_mas_barato),
        },
        "plan_mas_caro": {
            "id": plan_mas_caro["id"],
            "nombre": plan_mas_caro["nombre"],
            "precio": precio_efectivo(plan_mas_caro),
        },
    }


def correlacion_precio_datos(planes):
    """Correlacion de Pearson entre GB contratados y precio, solo planes con GB finito."""
    pares = [(p["datos_gb"], precio_efectivo(p)) for p in planes if p.get("datos_gb")]
    if len(pares) < 3:
        return None
    xs = [x for x, _ in pares]
    ys = [y for _, y in pares]
    try:
        return round(statistics.correlation(xs, ys), 3)
    except Exception:
        return None


def main():
    raw = json.loads(INPUT_PATH.read_text(encoding="utf-8"))
    planes = raw["planes"]

    for p in planes:
        p["precio_efectivo"] = precio_efectivo(p)
        p["precio_por_gb"] = precio_por_gb(p)

    operadores = sorted({p["operador"] for p in planes})
    por_operador = {
        op: resumen_operador(op, [p for p in planes if p["operador"] == op])
        for op in operadores
    }

    todos_precios = [precio_efectivo(p) for p in planes]
    todos_ppg = [precio_por_gb(p) for p in planes if precio_por_gb(p) is not None]

    ranking_precio_por_gb = sorted(
        (p for p in planes if p.get("precio_por_gb") is not None),
        key=lambda p: p["precio_por_gb"],
    )
    ranking_mas_barato_absoluto = sorted(planes, key=precio_efectivo)

    stats = {
        "generado_desde": str(INPUT_PATH.name),
        "fecha_actualizacion": raw["metadata"]["fecha_actualizacion"],
        "resumen_general": {
            "total_planes": len(planes),
            "total_operadores": len(operadores),
            "precio_promedio_mercado": round(statistics.mean(todos_precios), 0),
            "precio_mediana_mercado": round(statistics.median(todos_precios), 0),
            "precio_por_gb_promedio_mercado": round(statistics.mean(todos_ppg), 1) if todos_ppg else None,
            "correlacion_datos_vs_precio": correlacion_precio_datos(planes),
        },
        "por_operador": por_operador,
        "ranking_precio_por_gb_top10": [
            {
                "id": p["id"],
                "operador": p["operador"],
                "nombre": p["nombre"],
                "precio_por_gb": p["precio_por_gb"],
                "precio_efectivo": p["precio_efectivo"],
                "datos_gb": p["datos_gb"],
            }
            for p in ranking_precio_por_gb[:10]
        ],
        "ranking_mas_barato_absoluto_top5": [
            {
                "id": p["id"],
                "operador": p["operador"],
                "nombre": p["nombre"],
                "precio_efectivo": p["precio_efectivo"],
            }
            for p in ranking_mas_barato_absoluto[:5]
        ],
    }

    OUTPUT_PATH.write_text(json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"OK -> {OUTPUT_PATH} generado con {len(planes)} planes de {len(operadores)} operadores.")
    print(f"Precio/GB promedio del mercado: {stats['resumen_general']['precio_por_gb_promedio_mercado']} CLP/GB")
    for op, r in por_operador.items():
        print(f"  {op}: promedio {r['precio_promedio']} CLP, {r['cantidad_planes']} planes, "
              f"{r['precio_por_gb_promedio']} CLP/GB")


if __name__ == "__main__":
    main()
