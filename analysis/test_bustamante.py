#!/usr/bin/env python3
"""
Deep testing analysis for Bustamante Fabara IP
Compare deterministic rules + Claude + DeepSeek vs actual audit findings
"""

import pandas as pd
import json
from pathlib import Path

# ============================================================================
# LOAD DATA
# ============================================================================

tb = pd.read_excel("data/clientes/bustamante_fabara_ip/tb.xlsx")

print("\n" + "="*80)
print("ANALISIS DETERMINISTICO - BUSTAMANTE FABARA IP")
print("="*80)

# Parse accounts
accounts = {}
for idx, row in tb.iterrows():
    code = str(row["Numero de Cuenta"]).strip()
    name = str(row["Nombre Cuenta"]).strip()
    corr = str(row["Correspondencia"]).strip()
    ls = str(row["L/S"]).strip()
    s2025 = float(pd.to_numeric(row["Saldo 2025"], errors='coerce') or 0)
    s2024 = float(pd.to_numeric(row["Saldo 2024"], errors='coerce') or 0)

    accounts[code] = {
        "nombre": name,
        "correspondencia": corr,
        "ls": ls,
        "saldo_2025": s2025,
        "saldo_2024": s2024,
        "cambio": s2025 - s2024
    }

# ============================================================================
# RULE 1: Provision de cuentas incobrables
# ============================================================================
print("\n[RULE 1] PROVISION DE CUENTAS INCOBRABLES")
print("-" * 80)

cxc = {c: d for c, d in accounts.items() if "130" in str(d["ls"]) and c.startswith("101") and d["saldo_2025"] > 0}
provision = {c: d for c, d in accounts.items() if "provision" in d["nombre"].lower() and "cobrar" in d["nombre"].lower()}

total_cxc = sum(d["saldo_2025"] for d in cxc.values())
total_prov = sum(abs(d["saldo_2025"]) for d in provision.values() if d["saldo_2025"] < 0)
ratio = (total_prov / total_cxc * 100) if total_cxc > 0 else 0

print(f"Total CxC: ${total_cxc:,.2f}")
print(f"Total Provision: ${total_prov:,.2f}")
print(f"Ratio: {ratio:.2f}%")

# ============================================================================
# RULE 2: Pasivos con relacionadas
# ============================================================================
print("\n[RULE 2] TRANSACCIONES CON RELACIONADAS")
print("-" * 80)

related = {c: d for c, d in accounts.items() if "relacionada" in d["nombre"].lower()}
for code, data in related.items():
    cambio_pct = (data["cambio"] / abs(data["saldo_2024"]) * 100) if data["saldo_2024"] != 0 else 0
    if abs(data["cambio"]) > 1000:
        print(f"{code} {data['nombre'][:50]}")
        print(f"  2024: ${data['saldo_2024']:>12,.2f}  2025: ${data['saldo_2025']:>12,.2f}  Cambio: {cambio_pct:+.1f}%")

# ============================================================================
# RULE 3: Pasivos laborales
# ============================================================================
print("\n[RULE 3] PASIVOS LABORALES - Jubilacion y Desahucio")
print("-" * 80)

labor = {c: d for c, d in accounts.items() if any(x in d["nombre"].lower() for x in ["jubilacion", "desahucio", "empleado"])}
for code, data in labor.items():
    if code.startswith("20") and abs(data["cambio"]) > 100:
        cambio_pct = (data["cambio"] / abs(data["saldo_2024"]) * 100) if data["saldo_2024"] != 0 else 0
        print(f"{code} {data['nombre'][:50]}")
        print(f"  2024: ${data['saldo_2024']:>12,.2f}  2025: ${data['saldo_2025']:>12,.2f}  Cambio: {cambio_pct:+.1f}%")

# ============================================================================
# RULE 4: Ingresos vs Gastos
# ============================================================================
print("\n[RULE 4] ANALISIS DE RESULTADOS")
print("-" * 80)

ingresos = {c: d for c, d in accounts.items() if c.startswith("40")}
costos = {c: d for c, d in accounts.items() if c.startswith("51")}
gastos = {c: d for c, d in accounts.items() if c.startswith("5") and not c.startswith("51")}

total_ing = abs(sum(d["saldo_2025"] for d in ingresos.values()))
total_cost = sum(d["saldo_2025"] for d in costos.values())
total_gasto = sum(d["saldo_2025"] for d in gastos.values())

print(f"Ingresos: ${total_ing:,.2f}")
print(f"Costos directos: ${total_cost:,.2f}")
print(f"Otros gastos: ${total_gasto:,.2f}")
if total_ing > 0:
    print(f"Margen bruto: {(total_ing - total_cost) / total_ing * 100:.1f}%")

# ============================================================================
# RULE 5: Activos intangibles
# ============================================================================
print("\n[RULE 5] ACTIVOS INTANGIBLES Y AMORTIZACION")
print("-" * 80)

intangibles = {c: d for c, d in accounts.items() if c.startswith("103")}
for code, data in intangibles.items():
    if "amorti" not in data["nombre"].lower():
        print(f"{code} {data['nombre'][:50]} ${data['saldo_2025']:>12,.2f}")

print("\n" + "="*80)
print("HALLAZGOS DETERMINÍSTICOS COMPLETADOS")
print("="*80)
