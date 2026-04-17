#!/usr/bin/env python3
# Script para extraer y clasificar papeles de trabajo
# Papeles modelo estan en Pruebas modelo

import os
import json
import re
from pathlib import Path
from collections import defaultdict

# Aseveraciones NIA por tipo de paper (basado en nombres y propósitos)
ASEVERACION_MAP = {
    # EXISTENCIA: Verificar que assets/pasivos existen
    "Confirmación": "EXISTENCIA",
    "Confirmación de saldos": "EXISTENCIA",
    "Arqueo": "EXISTENCIA",
    "Reposición": "EXISTENCIA",
    "Verificación": "EXISTENCIA",

    # COMPLETITUD/INTEGRIDAD: Verificar que todo está registrado
    "Conciliación": "INTEGRIDAD",
    "Movimiento": "INTEGRIDAD",
    "Análisis de partidas": "INTEGRIDAD",
    "Resumen": "INTEGRIDAD",
    "Corte": "INTEGRIDAD",
    "Pasos alternos": "INTEGRIDAD",
    "Cobros posteriores": "INTEGRIDAD",
    "Pagos posteriores": "INTEGRIDAD",

    # VALORACIÓN: Verificar correctitud de valuación
    "Recálculo": "VALORACIÓN",
    "Valor Neto": "VALORACIÓN",
    "Costo amortizado": "VALORACIÓN",
    "Deterioro": "VALORACIÓN",
    "Amortización": "VALORACIÓN",
    "Impuestos": "VALORACIÓN",

    # DERECHOS Y OBLIGACIONES: Verificar que los derechos/obligaciones son válidos
    "Escrituras": "DERECHOS",
    "Clasificación": "DERECHOS",

    # PRESENTACIÓN: Cómo está presentado
    "Declaración": "PRESENTACION",
    "ATS": "PRESENTACION",
    "APS": "PRESENTACION",
    "Anexo": "PRESENTACION",

    # OTROS
    "Levantamiento": "PROCEDIMIENTO",
    "Revisión": "PROCEDIMIENTO",
    "Muestra": "PROCEDIMIENTO",
    "Análisis": "PROCEDIMIENTO",
    "Plantilla": "PROCEDIMIENTO",
    "Firmas": "PROCEDIMIENTO",
    "Fantasma": "VALIDACION",
}

IMPORTANCIA_MAP = {
    # CRÍTICO: Sin esto no puedo firmar
    "Confirmación de saldos": "CRITICO",
    "Conciliación cuentas": "CRITICO",
    "Movimiento": "CRITICO",
    "Declaración": "CRITICO",
    "Conciliacion base": "CRITICO",

    # ALTO: Muy importante, generalmente obligatorio
    "Arqueo": "ALTO",
    "Conciliación": "ALTO",
    "Resumen": "ALTO",
    "Análisis de": "ALTO",
    "Recálculo": "ALTO",
    "Deterioro": "ALTO",
    "Pasos alternos": "ALTO",
    "Antiguedad": "ALTO",

    # MEDIO: Importante si aplica
    "Costo amortizado": "MEDIO",
    "Clasificación": "MEDIO",
    "Inversiones": "MEDIO",
    "Derivados": "MEDIO",

    # BAJO: Procedimientos menores
    "Firmas": "BAJO",
    "Plantilla": "BAJO",
}

# Descripción POR QUÉ se realiza (para Junior)
DESCRIPCION_MAP = {
    "140.03": "Por qué se realiza conciliación de efectivo bancario en rol Junior",
    "140.04": "Por qué se analizan partidas conciliatorias en rol Junior",
    "140.05": "Por qué se revisan firmas autorizadas en rol Junior",
    "140.06": "Por qué se realiza corte documentario de egresos en rol Junior",
    "140.07": "Por qué se realiza corte documentario de ingresos en rol Junior",
    "140.08": "Por qué se analizan inversiones en rol Junior",
    "140.09": "Por qué se realiza arqueo de caja en rol Junior",
    "140.10": "Por qué se realiza reposición de caja en rol Junior",

    "130.03": "Por qué se realiza conciliación de cuentas por cobrar en rol Junior",
    "130.04": "Por qué se analiza antigüedad de cartera en rol Junior",
    "130.05": "Por qué se analiza concentración de cartera en rol Junior",
    "130.06": "Por qué se analiza costo amortizado en rol Junior",
    "130.07": "Por qué se realizan confirmaciones de saldos en rol Junior",
    "130.08": "Por qué se evalúan cobros posteriores en rol Junior",
    "130.09": "Por qué se evalúa deterioro de cartera en rol Junior",

    "110.03": "Por qué se revisa movimiento de inventarios en rol Junior",
    "110.04": "Por qué se concilia detalle de inventarios en rol Junior",
    "110.05": "Por qué se muestrea compras locales en rol Junior",
    "110.06": "Por qué se revisan importaciones en rol Junior",
    "110.07": "Por qué se analiza inventario de lento movimiento en rol Junior",
    "110.08": "Por qué se evalúa valor neto realizable en rol Junior",

    "425.03": "Por qué se realiza conciliación de cuentas por pagar en rol Junior",
    "425.04": "Por qué se analiza antigüedad de proveedores en rol Junior",
    "425.05": "Por qué se realizan confirmaciones de saldos a proveedores en rol Junior",
    "425.06": "Por qué se evalúan pagos posteriores en rol Junior",
    "425.07": "Por qué se analiza costo amortizado en rol Junior",

    "324.02": "Por qué se revisa declaración de retención IR en rol Junior",
    "324.03": "Por qué se revisa declaración de retención IVA en rol Junior",
    "324.04": "Por qué se revisa declaración de IVA en rol Junior",
    "324.05": "Por qué se analiza ATS en rol Junior",
    "324.06": "Por qué se revisan otros impuestos en rol Junior",
    "324.07": "Por qué se revisa anexo de dividendos en rol Junior",
    "324.08": "Por qué se revisa APS en rol Junior",
}

def extract_ls_and_name(filename):
    """Extrae LS.Número y nombre del archivo"""
    # Patrón: "140.03 Resumen conciliación bancaria.xlsx"
    match = re.match(r'(\d+\.\d+)\s+(.+)\.\w+$', filename)
    if match:
        codigo = match.group(1)
        nombre = match.group(2)
        ls = codigo.split('.')[0]
        numero = codigo.split('.')[1]
        return ls, numero, codigo, nombre
    return None, None, None, None

def classify_aseveracion(nombre_archivo):
    """Clasifica aseveración basado en el nombre"""
    for keyword, aseveracion in ASEVERACION_MAP.items():
        if keyword.lower() in nombre_archivo.lower():
            return aseveracion
    return "PROCEDIMIENTO"

def classify_importancia(nombre_archivo):
    """Clasifica importancia basado en el nombre"""
    for keyword, importancia in IMPORTANCIA_MAP.items():
        if keyword.lower() in nombre_archivo.lower():
            return importancia
    return "MEDIO"

def get_descripcion(codigo):
    """Obtiene descripción POR QUÉ"""
    if codigo in DESCRIPCION_MAP:
        return DESCRIPCION_MAP[codigo]
    return f"Por qué se realiza este procedimiento en rol Junior"

def main():
    papeles_dir = Path(r"C:\Users\echoe\Desktop\Nuevo Socio AI\Pruebas modelo")

    papeles = []
    ls_groups = defaultdict(list)

    # Buscar todos los .xlsx
    for filepath in papeles_dir.rglob("*.xlsx"):
        filename = filepath.name

        ls, numero, codigo, nombre = extract_ls_and_name(filename)
        if ls is None:
            print(f"⚠️  No se pudo extraer LS de: {filename}")
            continue

        aseveracion = classify_aseveracion(nombre)
        importancia = classify_importancia(nombre)
        descripcion = get_descripcion(codigo)

        papel = {
            "codigo": codigo,
            "numero": numero,
            "ls": int(ls),
            "nombre": nombre,
            "aseveracion": aseveracion,
            "importancia": importancia,
            "obligatorio": "SÍ" if importancia in ["CRITICO", "ALTO"] else "CONDICIONAL" if importancia == "MEDIO" else "NO",
            "descripcion": descripcion,
            "archivo_original": str(filepath),
        }

        papeles.append(papel)
        ls_groups[int(ls)].append(papel)

    # Ordenar por importancia
    importancia_orden = {"CRITICO": 0, "ALTO": 1, "MEDIO": 2, "BAJO": 3}
    for ls in ls_groups:
        ls_groups[ls].sort(key=lambda x: (importancia_orden.get(x["importancia"], 4), x["codigo"]))

    # Mostrar resumen
    print(f"\n{'='*80}")
    print(f"EXTRACCIÓN DE PAPELES DE TRABAJO")
    print(f"{'='*80}")
    print(f"Total papeles encontrados: {len(papeles)}")
    print(f"Líneas de Cuenta (LS) encontradas: {sorted(ls_groups.keys())}")
    print()

    # Mostrar por LS
    for ls in sorted(ls_groups.keys()):
        papers = ls_groups[ls]
        print(f"\nLS {ls} ({len(papers)} papeles):")
        for p in papers:
            print(f"  {p['codigo']} | {p['aseveracion']:15} | {p['importancia']:10} | {p['nombre'][:50]}")

    # Guardar JSON
    output_json = {
        "total": len(papeles),
        "lineas_de_cuenta": sorted(ls_groups.keys()),
        "papeles": papeles,
        "papeles_por_ls": {
            str(ls): ls_groups[ls] for ls in sorted(ls_groups.keys())
        }
    }

    output_path = Path("data/papeles_clasificados.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_json, f, ensure_ascii=False, indent=2)

    print(f"\nJSON guardado en: {output_path}")
    print(f"{'='*80}\n")

if __name__ == "__main__":
    main()
