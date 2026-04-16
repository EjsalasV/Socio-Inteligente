"""
Export service for generating PDF reports by role.
Supports role-based report generation with different levels of detail.
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Literal

from backend.repositories.file_repository import repo

LOGGER = logging.getLogger("socio_ai.export")


def generate_pdf(
    cliente_id: str,
    report_type: Literal["resumen_ejecutivo", "informe_completo", "hallazgos"],
    role: Literal["junior", "semi", "senior", "socio"],
    fecha_periodo: str | None = None,
) -> bytes:
    """
    Generate PDF report based on role and report type.

    Args:
        cliente_id: Client ID
        report_type: Type of report to generate
        role: User role (determines detail level)
        fecha_periodo: Period to report on (e.g., "2025-01")

    Returns:
        PDF bytes

    Raises:
        ValueError: If client data is missing or invalid
        ImportError: If required libraries are not available
    """
    # Get client data
    perfil = repo.read_perfil(cliente_id)
    if not perfil:
        raise ValueError(f"Cliente {cliente_id} no encontrado")

    # Get hallazgos
    hallazgos_doc = repo.read_hallazgos(cliente_id)
    hallazgos = _parse_hallazgos(hallazgos_doc) if hallazgos_doc else []

    # Get areas
    areas = repo.list_areas(cliente_id)
    areas_data = []
    if areas:
        for area_code in areas[:5]:  # Top 5 areas
            try:
                area_yaml = repo.read_area_yaml(cliente_id, area_code)
                if area_yaml:
                    areas_data.append({
                        "codigo": area_code,
                        "nombre": area_yaml.get("nombre", area_code),
                        "descripcion": area_yaml.get("descripcion", ""),
                    })
            except Exception as e:
                LOGGER.warning("Error reading area %s: %s", area_code, e)

    # Get dashboard data for indices
    try:
        from backend.services.view_cache_service import get_cached_view
        dashboard_data = get_cached_view(cliente_id, "dashboard")
    except Exception as e:
        LOGGER.warning("Could not get cached dashboard data: %s", e)
        dashboard_data = {}

    # Generate context based on role
    context = _build_report_context(
        cliente_id=cliente_id,
        perfil=perfil,
        hallazgos=hallazgos,
        areas=areas_data,
        dashboard_data=dashboard_data,
        role=role,
        report_type=report_type,
        fecha_periodo=fecha_periodo,
    )

    # Generate HTML
    html_content = _generate_html(context, role, report_type)

    # Convert to PDF
    try:
        from weasyprint import HTML, CSS
        return HTML(string=html_content).write_pdf()
    except ImportError:
        LOGGER.error("weasyprint not installed. Install with: pip install weasyprint")
        raise ImportError("weasyprint is required for PDF generation")


def _parse_hallazgos(hallazgos_doc: str) -> list[dict[str, Any]]:
    """Parse markdown hallazgos document into structured list."""
    hallazgos = []
    lines = hallazgos_doc.split("\n")
    current = None

    for line in lines:
        if line.startswith("## Hallazgo"):
            if current:
                hallazgos.append(current)
            parts = line.replace("## Hallazgo", "").strip().split(" - ", 1)
            current = {
                "area_codigo": parts[0].strip() if parts else "",
                "area_nombre": parts[1].strip() if len(parts) > 1 else "",
                "descripcion": "",
            }
        elif current:
            current["descripcion"] += line + " "

    if current:
        hallazgos.append(current)

    return hallazgos


def _build_report_context(
    cliente_id: str,
    perfil: dict,
    hallazgos: list,
    areas: list,
    dashboard_data: dict,
    role: str,
    report_type: str,
    fecha_periodo: str | None,
) -> dict[str, Any]:
    """Build template context based on role and report type."""
    now = datetime.now()
    periodo = fecha_periodo or now.strftime("%Y-%m")

    # Extract balance KPIs
    balance = dashboard_data.get("balance", {})
    activo = balance.get("activo", 0.0)
    pasivo = balance.get("pasivo", 0.0)
    patrimonio = balance.get("patrimonio", 0.0)
    ingresos = balance.get("ingresos", 0.0)

    # Calculate indices based on role
    indices = _calculate_indices(activo, pasivo, patrimonio, ingresos, role)

    # Filter hallazgos by role
    hallazgos_filtered = _filter_hallazgos_by_role(hallazgos, role)

    context = {
        "cliente_id": cliente_id,
        "nombre_cliente": perfil.get("nombre", ""),
        "sector": perfil.get("sector", ""),
        "periodo": periodo,
        "fecha_generacion": now.strftime("%d/%m/%Y"),
        "hora_generacion": now.strftime("%H:%M"),
        "role": role,
        "report_type": report_type,

        # Financial data
        "activo": f"{activo:,.0f}",
        "pasivo": f"{pasivo:,.0f}",
        "patrimonio": f"{patrimonio:,.0f}",
        "ingresos": f"{ingresos:,.0f}",

        # Indices
        "indices": indices,
        "total_indices": len(indices),

        # Findings
        "hallazgos": hallazgos_filtered,
        "total_hallazgos": len(hallazgos_filtered),
        "hallazgos_criticos": len([h for h in hallazgos_filtered if "crítico" in h.get("descripcion", "").lower()]),

        # Areas
        "areas": areas[:3],  # Top 3 areas
        "total_areas": len(areas),

        # Metadata
        "materialidad_global": dashboard_data.get("materialidad_global", 0.0),
        "riesgo_global": dashboard_data.get("riesgo_global", "Medio"),
        "progreso_pct": dashboard_data.get("progreso", {}).get("pct_completado", 0),
    }

    return context


def _calculate_indices(
    activo: float,
    pasivo: float,
    patrimonio: float,
    ingresos: float,
    role: str,
) -> list[dict[str, Any]]:
    """Calculate financial indices based on role."""
    indices = []

    # All roles get basic indices
    if activo > 0:
        indice_endeudamiento = (pasivo / activo) * 100
        indices.append({
            "nombre": "Índice de Endeudamiento",
            "valor": f"{indice_endeudamiento:.2f}%",
            "interpretacion": "% activos financiados por pasivos"
        })

    if patrimonio > 0:
        roa = (ingresos / patrimonio) * 100 if patrimonio > 0 else 0
        indices.append({
            "nombre": "Rentabilidad del Patrimonio",
            "valor": f"{roa:.2f}%",
            "interpretacion": "Retorno sobre el patrimonio"
        })

    # Semi+ get more indices
    if role in {"semi", "senior", "socio"}:
        if pasivo + patrimonio > 0:
            estructura_capital = (patrimonio / (pasivo + patrimonio)) * 100
            indices.append({
                "nombre": "Estructura de Capital",
                "valor": f"{estructura_capital:.2f}%",
                "interpretacion": "% patrimonio en estructura total"
            })

        if activo > 0:
            indice_liquidez = (activo / pasivo) if pasivo > 0 else 0
            indices.append({
                "nombre": "Índice de Liquidez",
                "valor": f"{indice_liquidez:.2f}",
                "interpretacion": "Capacidad de pagar deudas"
            })

    # Senior+ get advanced indices
    if role in {"senior", "socio"}:
        if patrimonio > 0:
            roi = (ingresos / patrimonio) * 100 if patrimonio > 0 else 0
            indices.append({
                "nombre": "ROI (Return on Investment)",
                "valor": f"{roi:.2f}%",
                "interpretacion": "Retorno sobre inversión total"
            })

        indices.append({
            "nombre": "Margen de Ganancia",
            "valor": f"{((ingresos - (ingresos * 0.4)) / ingresos * 100):.2f}%" if ingresos > 0 else "N/A",
            "interpretacion": "Ganancia neta sobre ingresos"
        })

    return indices


def _filter_hallazgos_by_role(hallazgos: list, role: str) -> list[dict[str, Any]]:
    """Filter hallazgos based on role severity filtering."""
    if role == "junior":
        # Junior only sees critical
        return [h for h in hallazgos if "crítico" in h.get("descripcion", "").lower()]
    elif role == "semi":
        # Semi sees critical + high
        return [h for h in hallazgos if any(x in h.get("descripcion", "").lower() for x in ["crítico", "alto"])]
    else:
        # Senior and socio see all
        return hallazgos


def _generate_html(
    context: dict[str, Any],
    role: str,
    report_type: str,
) -> str:
    """Generate HTML content for PDF based on template and role."""
    template_key = f"{report_type}_{role}"

    if report_type == "resumen_ejecutivo":
        return _template_ejecutivo(context, role)
    elif report_type == "informe_completo":
        return _template_completo(context, role)
    elif report_type == "hallazgos":
        return _template_hallazgos(context, role)
    else:
        return _template_ejecutivo(context, role)  # Default


def _template_ejecutivo(context: dict[str, Any], role: str) -> str:
    """Template for executive summary."""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; color: #333; }}
            .header {{ border-bottom: 3px solid #1e40af; padding-bottom: 20px; margin-bottom: 30px; }}
            .cliente {{ font-size: 24px; font-weight: bold; }}
            .periodo {{ font-size: 14px; color: #666; margin-top: 5px; }}
            .section {{ margin-bottom: 40px; page-break-inside: avoid; }}
            .section-title {{ font-size: 18px; font-weight: bold; color: #1e40af; border-bottom: 2px solid #e5e7eb; padding-bottom: 10px; margin-bottom: 15px; }}
            .indices {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin: 15px 0; }}
            .indice-box {{ background: #f3f4f6; padding: 15px; border-radius: 8px; }}
            .indice-valor {{ font-size: 20px; font-weight: bold; color: #1e40af; }}
            .indice-nombre {{ font-size: 12px; color: #666; margin-top: 5px; }}
            .hallazgos {{ margin: 15px 0; }}
            .hallazgo {{ background: #fee2e2; padding: 12px; margin: 10px 0; border-left: 4px solid #dc2626; }}
            .footer {{ text-align: center; color: #999; font-size: 10px; margin-top: 40px; border-top: 1px solid #e5e7eb; padding-top: 10px; }}
            table {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
            th, td {{ padding: 10px; text-align: left; border-bottom: 1px solid #e5e7eb; }}
            th {{ background: #f3f4f6; font-weight: bold; }}
        </style>
    </head>
    <body>
        <div class="header">
            <div class="cliente">{context['nombre_cliente']}</div>
            <div class="periodo">Período: {context['periodo']} | Rol: {context['role'].upper()}</div>
            <div class="periodo">Generado: {context['fecha_generacion']} a las {context['hora_generacion']}</div>
        </div>

        <div class="section">
            <div class="section-title">Resumen Ejecutivo</div>
            <p>
                {context['nombre_cliente']} es una entidad del sector {context['sector']} evaluada durante el período {context['periodo']}.
                El riesgo global identificado es <strong>{context['riesgo_global']}</strong> con un progreso de ejecución del
                <strong>{context['progreso_pct']}%</strong>.
            </p>
        </div>

        <div class="section">
            <div class="section-title">Situación Financiera</div>
            <table>
                <tr>
                    <th>Concepto</th>
                    <th>Valor</th>
                </tr>
                <tr>
                    <td>Activos Totales</td>
                    <td>{context['activo']}</td>
                </tr>
                <tr>
                    <td>Pasivos Totales</td>
                    <td>{context['pasivo']}</td>
                </tr>
                <tr>
                    <td>Patrimonio</td>
                    <td>{context['patrimonio']}</td>
                </tr>
                <tr>
                    <td>Ingresos del Período</td>
                    <td>{context['ingresos']}</td>
                </tr>
            </table>
        </div>

        <div class="section">
            <div class="section-title">Índices Financieros</div>
            <div class="indices">
                {"".join([f'''
                <div class="indice-box">
                    <div class="indice-valor">{idx['valor']}</div>
                    <div class="indice-nombre">{idx['nombre']}</div>
                </div>
                ''' for idx in context['indices'][:6]])}
            </div>
        </div>

        {"" if not context['hallazgos'] else f'''
        <div class="section">
            <div class="section-title">Hallazgos Significativos ({len(context['hallazgos'])})</div>
            <div class="hallazgos">
                {"".join([f'''
                <div class="hallazgo">
                    <strong>{h['area_codigo']} - {h['area_nombre']}</strong><br>
                    {h['descripcion'][:100]}...
                </div>
                ''' for h in context['hallazgos'][:3]])}
            </div>
        </div>
        '''}

        <div class="footer">
            <p>Este reporte fue generado automáticamente por Socio AI - Auditoría Inteligente</p>
            <p>Confidencial - Solo para uso de {context['nombre_cliente']}</p>
        </div>
    </body>
    </html>
    """


def _template_completo(context: dict[str, Any], role: str) -> str:
    """Template for complete audit report."""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; color: #333; }}
            .header {{ border-bottom: 3px solid #1e40af; padding-bottom: 20px; margin-bottom: 30px; }}
            .cliente {{ font-size: 28px; font-weight: bold; }}
            .section {{ margin-bottom: 40px; page-break-inside: avoid; }}
            .section-title {{ font-size: 20px; font-weight: bold; color: #1e40af; border-bottom: 2px solid #e5e7eb; padding-bottom: 10px; margin-bottom: 15px; }}
            .subsection-title {{ font-size: 14px; font-weight: bold; color: #374151; margin-top: 20px; margin-bottom: 10px; }}
            .hallazgo {{ background: #fee2e2; padding: 15px; margin: 10px 0; border-left: 4px solid #dc2626; page-break-inside: avoid; }}
            .area-box {{ background: #f0f9ff; padding: 15px; margin: 10px 0; border-left: 4px solid #0284c7; }}
            table {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
            th, td {{ padding: 10px; text-align: left; border-bottom: 1px solid #e5e7eb; }}
            th {{ background: #f3f4f6; font-weight: bold; }}
            .footer {{ text-align: center; color: #999; font-size: 10px; margin-top: 50px; border-top: 1px solid #e5e7eb; padding-top: 10px; }}
        </style>
    </head>
    <body>
        <div class="header">
            <div class="cliente">{context['nombre_cliente']}</div>
            <div style="color: #666; margin-top: 10px;">
                Período: {context['periodo']} | Sector: {context['sector']} | Rol: {context['role'].upper()}
            </div>
        </div>

        <div class="section">
            <div class="section-title">1. Contexto de la Auditoría</div>
            <p>
                Esta auditoría fue realizada a {context['nombre_cliente']}, entidad ubicada en el sector {context['sector']},
                durante el período {context['periodo']}.
            </p>
            <p>
                <strong>Materialidad Global:</strong> ${context['materialidad_global']:,.2f}<br>
                <strong>Riesgo Global:</strong> {context['riesgo_global']}<br>
                <strong>Progreso de Ejecución:</strong> {context['progreso_pct']}%
            </p>
        </div>

        <div class="section">
            <div class="section-title">2. Análisis Financiero</div>
            <table>
                <tr>
                    <th>Concepto</th>
                    <th>Monto</th>
                    <th>% del Total</th>
                </tr>
                <tr>
                    <td>Activos Totales</td>
                    <td>{context['activo']}</td>
                    <td>100%</td>
                </tr>
                <tr>
                    <td>Pasivos Totales</td>
                    <td>{context['pasivo']}</td>
                    <td>-</td>
                </tr>
                <tr>
                    <td>Patrimonio</td>
                    <td>{context['patrimonio']}</td>
                    <td>-</td>
                </tr>
            </table>
        </div>

        <div class="section">
            <div class="section-title">3. Índices de Gestión</div>
            <table>
                <tr>
                    <th>Índice</th>
                    <th>Valor</th>
                    <th>Interpretación</th>
                </tr>
                {"".join([f'''
                <tr>
                    <td>{idx['nombre']}</td>
                    <td>{idx['valor']}</td>
                    <td>{idx['interpretacion']}</td>
                </tr>
                ''' for idx in context['indices']])}
            </table>
        </div>

        <div class="section">
            <div class="section-title">4. Hallazgos de Auditoría</div>
            <p>Se identificaron <strong>{len(context['hallazgos'])}</strong> hallazgos durante la ejecución de la auditoría.</p>
            <div>
                {"".join([f'''
                <div class="hallazgo">
                    <strong>Área: {h['area_codigo']} - {h['area_nombre']}</strong><br>
                    <p>{h['descripcion']}</p>
                </div>
                ''' for h in context['hallazgos']])}
            </div>
        </div>

        <div class="section">
            <div class="section-title">5. Áreas Evaluadas</div>
            {"".join([f'''
            <div class="area-box">
                <strong>{a['codigo']} - {a['nombre']}</strong><br>
                {a['descripcion'][:150]}...
            </div>
            ''' for a in context['areas']])}
        </div>

        <div class="footer">
            <p>Reporte generado por Socio AI - Auditoría Inteligente</p>
            <p>Confidencial - Documento privilegiado</p>
            <p>Fecha de generación: {context['fecha_generacion']}</p>
        </div>
    </body>
    </html>
    """


def _template_hallazgos(context: dict[str, Any], role: str) -> str:
    """Template for findings-only report."""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; color: #333; }}
            .header {{ border-bottom: 3px solid #dc2626; padding-bottom: 20px; margin-bottom: 30px; }}
            .cliente {{ font-size: 24px; font-weight: bold; }}
            .section-title {{ font-size: 16px; font-weight: bold; color: #dc2626; margin-top: 20px; margin-bottom: 10px; }}
            .hallazgo {{ background: #fee2e2; padding: 15px; margin: 15px 0; border-left: 4px solid #dc2626; page-break-inside: avoid; }}
            .footer {{ text-align: center; color: #999; font-size: 10px; margin-top: 50px; border-top: 1px solid #e5e7eb; padding-top: 10px; }}
            .stats {{ display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 20px; margin: 20px 0; }}
            .stat-box {{ background: #fecaca; padding: 15px; border-radius: 8px; text-align: center; }}
            .stat-value {{ font-size: 28px; font-weight: bold; color: #7f1d1d; }}
            .stat-label {{ font-size: 12px; color: #991b1b; margin-top: 5px; }}
        </style>
    </head>
    <body>
        <div class="header">
            <div class="cliente">{context['nombre_cliente']}</div>
            <div style="color: #dc2626; margin-top: 10px; font-size: 14px;">
                REPORTE DE HALLAZGOS - {context['periodo'].upper()}
            </div>
        </div>

        <div class="stats">
            <div class="stat-box">
                <div class="stat-value">{len(context['hallazgos'])}</div>
                <div class="stat-label">Hallazgos Totales</div>
            </div>
            <div class="stat-box">
                <div class="stat-value">{context['hallazgos_criticos']}</div>
                <div class="stat-label">Críticos</div>
            </div>
            <div class="stat-box">
                <div class="stat-value">{len(context['areas'])}</div>
                <div class="stat-label">Áreas Afectadas</div>
            </div>
        </div>

        <div class="section-title">Listado de Hallazgos</div>
        {"".join([f'''
        <div class="hallazgo">
            <strong>{i+1}. {h['area_codigo']} - {h['area_nombre']}</strong><br>
            <p>{h['descripcion']}</p>
        </div>
        ''' for i, h in enumerate(context['hallazgos'])])}

        <div class="footer">
            <p>Reporte de Hallazgos - Socio AI Auditoría Inteligente</p>
            <p>Generado: {context['fecha_generacion']}</p>
        </div>
    </body>
    </html>
    """
