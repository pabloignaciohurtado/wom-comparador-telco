#!/usr/bin/env python3
"""
Valida la consistencia de data/planes.json y data/planes_multilinea.json.

Reglas (falla con exit 1 si alguna no se cumple):
- Campos obligatorios presentes y con el tipo correcto.
- IDs únicos.
- Operador declarado en metadata.operadores.
- precio_regular > 0; precio_promo (si existe) > 0 y <= precio_regular.
- meses_promo informado si y solo si hay precio_promo.
- Plan con datos ilimitados no informa datos_gb; plan con GB informado es > 0.
- Cada operador de metadata tiene al menos un plan.
- fecha_actualizacion en formato YYYY-MM-DD.

Uso:
    python3 scripts/validate_data.py
"""
import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLANES = ROOT / "data" / "planes.json"
MULTILINEA = ROOT / "data" / "planes_multilinea.json"

REQUERIDOS = {
    "id": str,
    "operador": str,
    "nombre": str,
    "segmento": str,
    "precio_regular": int,
    "datos_ilimitados": bool,
    "redes_sociales_gratis": bool,
    "roaming_incluido": bool,
    "streaming_incluido": bool,
    "fuente": str,
}

errores = []


def err(msg):
    errores.append(msg)


def validar_fecha(valor, donde):
    try:
        date.fromisoformat(valor)
    except (TypeError, ValueError):
        err(f"{donde}: fecha_actualizacion inválida ({valor!r}), se espera YYYY-MM-DD")


def validar_planes():
    raw = json.loads(PLANES.read_text(encoding="utf-8"))
    meta = raw.get("metadata", {})
    validar_fecha(meta.get("fecha_actualizacion"), "planes.json")
    operadores = set(meta.get("operadores", []))
    if not operadores:
        err("planes.json: metadata.operadores vacío")

    planes = raw.get("planes", [])
    if not planes:
        err("planes.json: no hay planes")

    ids = set()
    for i, p in enumerate(planes):
        tag = p.get("id", f"#{i}")
        for campo, tipo in REQUERIDOS.items():
            if campo not in p:
                err(f"{tag}: falta campo '{campo}'")
            elif not isinstance(p[campo], tipo) or (tipo is int and isinstance(p[campo], bool)):
                err(f"{tag}: '{campo}' debe ser {tipo.__name__}, es {type(p[campo]).__name__}")
        if tag in ids:
            err(f"{tag}: id duplicado")
        ids.add(tag)
        if p.get("operador") not in operadores:
            err(f"{tag}: operador '{p.get('operador')}' no está en metadata.operadores")

        reg = p.get("precio_regular")
        promo = p.get("precio_promo")
        if isinstance(reg, int) and reg <= 0:
            err(f"{tag}: precio_regular debe ser > 0")
        if promo is not None:
            if not isinstance(promo, int) or promo <= 0:
                err(f"{tag}: precio_promo debe ser entero > 0 o null")
            elif isinstance(reg, int) and promo > reg:
                err(f"{tag}: precio_promo ({promo}) mayor que precio_regular ({reg})")
            if not p.get("meses_promo"):
                err(f"{tag}: tiene precio_promo pero no meses_promo")
        elif p.get("meses_promo"):
            err(f"{tag}: informa meses_promo sin precio_promo")

        gb = p.get("datos_gb")
        if p.get("datos_ilimitados") and gb is not None:
            err(f"{tag}: datos ilimitados no debe informar datos_gb")
        if gb is not None and (not isinstance(gb, (int, float)) or gb <= 0):
            err(f"{tag}: datos_gb debe ser > 0 o null")

    for op in operadores:
        if not any(p.get("operador") == op for p in planes):
            err(f"planes.json: operador '{op}' sin planes")
    return operadores, len(planes)


def validar_multilinea(operadores):
    if not MULTILINEA.exists():
        return 0
    raw = json.loads(MULTILINEA.read_text(encoding="utf-8"))
    validar_fecha(raw.get("metadata", {}).get("fecha_actualizacion"), "planes_multilinea.json")
    ofertas = raw.get("ofertas", [])
    for o in ofertas:
        op = o.get("operador")
        if op not in operadores:
            err(f"multilínea: operador '{op}' no está en planes.json")
        if o.get("confirmado"):
            reg = o.get("precio_linea_adicional_regular")
            promo = o.get("precio_linea_adicional_promo")
            if not isinstance(reg, int) or reg <= 0:
                err(f"multilínea {op}: confirmado sin precio_linea_adicional_regular válido")
            if promo is not None and isinstance(reg, int) and promo > reg:
                err(f"multilínea {op}: precio promo mayor que regular")
    return len(ofertas)


def main():
    operadores, n = validar_planes()
    m = validar_multilinea(operadores)
    if errores:
        print(f"::error::{len(errores)} problema(s) en los datos:")
        for e in errores:
            print(f"  - {e}")
        sys.exit(1)
    print(f"OK -> {n} planes de {len(operadores)} operadores y {m} ofertas multilínea validados.")


if __name__ == "__main__":
    main()
