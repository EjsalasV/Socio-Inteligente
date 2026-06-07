"""
Configuración dinámica por tipo de industria/entidad
Define preguntas y parámetros que configuran el sistema de auditoría
"""

CONFIGURACION_INDUSTRIAS = {
    "BANCO": {
        "nombre": "Entidad Financiera / Banco",
        "preguntas": [
            {
                "id": "rango_vencimiento",
                "texto": "¿Rango de vencimiento para cartera vencida?",
                "tipo": "select",
                "opciones": [
                    {"valor": "15", "label": "15 días"},
                    {"valor": "30", "label": "30 días (default)"},
                    {"valor": "45", "label": "45 días"},
                    {"valor": "90", "label": "90 días"},
                ],
                "default": "30",
                "critica": True,
                "afecta_hallazgos": ["A.3", "A.6"],
                "ayuda": "Define cuándo una cartera se considera vencida para detectar hallazgos"
            },
            {
                "id": "clasificacion_cartera",
                "texto": "¿Qué clasificación de cartera usa?",
                "tipo": "select",
                "opciones": [
                    {"valor": "ABCDE", "label": "A/B/C/D/E (Standard SBS)"},
                    {"valor": "VIGENTE_VENCIDA", "label": "Vigente/Vencida"},
                    {"valor": "OTRO", "label": "Otro"},
                ],
                "default": "ABCDE",
                "critica": True,
                "afecta_hallazgos": ["A.3", "A.6"],
                "ayuda": "Clasificación que el banco usa internamente"
            },
            {
                "id": "provisiones_pct",
                "texto": "% de provisión esperado por clasificación",
                "tipo": "text",
                "placeholder": "0.5,1,2,5,10",
                "default": "0.5,1,2,5,10",
                "critica": True,
                "afecta_hallazgos": ["PROVISION"],
                "ayuda": "Separado por comas. Ej: 0.5% para A, 1% para B, etc"
            },
            {
                "id": "esta_auditado_sbs",
                "texto": "¿Está auditado por SBS (Superintendencia)?",
                "tipo": "select",
                "opciones": [
                    {"valor": "SI", "label": "Sí"},
                    {"valor": "NO", "label": "No"},
                ],
                "default": "SI",
                "critica": False,
                "afecta_hallazgos": [],
                "ayuda": "Si es SBS, se aplican validaciones regulatorias adicionales"
            },
            {
                "id": "tiene_obligaciones_publico",
                "texto": "¿Tiene obligaciones con el público (depósitos)?",
                "tipo": "select",
                "opciones": [
                    {"valor": "SI", "label": "Sí"},
                    {"valor": "NO", "label": "No"},
                ],
                "default": "SI",
                "critica": False,
                "afecta_hallazgos": [],
                "ayuda": "Determina análisis de liquidez y reservas"
            },
        ]
    },

    "RETAIL": {
        "nombre": "Retail / Comercio / Distribuidora",
        "preguntas": [
            {
                "id": "rango_vencimiento_cxc",
                "texto": "¿A cuántos días se considera CxC vencida?",
                "tipo": "select",
                "opciones": [
                    {"valor": "30", "label": "30 días (tiendas modernas)"},
                    {"valor": "45", "label": "45 días"},
                    {"valor": "60", "label": "60 días (retail tradicional)"},
                    {"valor": "90", "label": "90 días"},
                ],
                "default": "60",
                "critica": True,
                "afecta_hallazgos": ["A.3", "A.4"],
                "ayuda": "Retail tiene ciclos más largos que servicios"
            },
            {
                "id": "inventario_pct_activos",
                "texto": "¿Qué % de inventario esperas vs total activos?",
                "tipo": "select",
                "opciones": [
                    {"valor": "30", "label": "30-40% (bajo)"},
                    {"valor": "50", "label": "40-60% (normal)"},
                    {"valor": "70", "label": "60-80% (alto)"},
                    {"valor": "custom", "label": "Personalizado"},
                ],
                "default": "50",
                "critica": True,
                "afecta_hallazgos": ["A.5"],
                "ayuda": "Parámetro clave para detectar desbalances"
            },
            {
                "id": "rotacion_inventario_dias",
                "texto": "¿Cuántos días debería rotar el inventario?",
                "tipo": "text",
                "placeholder": "45",
                "default": "60",
                "critica": True,
                "afecta_hallazgos": ["A.5"],
                "ayuda": "Ej: retail moda 30-45d, electronics 45-90d, etc"
            },
            {
                "id": "tiene_consignaciones",
                "texto": "¿Tiene inventario en consignación de proveedores?",
                "tipo": "select",
                "opciones": [
                    {"valor": "SI", "label": "Sí"},
                    {"valor": "NO", "label": "No"},
                ],
                "default": "NO",
                "critica": False,
                "afecta_hallazgos": ["CUTOFF"],
                "ayuda": "Requiere validación especial de cutoff"
            },
            {
                "id": "pct_devoluciones_normal",
                "texto": "% de devoluciones clientes considerado normal",
                "tipo": "text",
                "placeholder": "2",
                "default": "2",
                "critica": False,
                "afecta_hallazgos": [],
                "ayuda": "Por encima de esto = alerta"
            },
        ]
    },

    "SERVICIOS": {
        "nombre": "Servicios / Consultoría / Legal",
        "preguntas": [
            {
                "id": "rango_vencimiento_cxc",
                "texto": "¿A cuántos días se considera CxC vencida?",
                "tipo": "select",
                "opciones": [
                    {"valor": "30", "label": "30 días (agresivo)"},
                    {"valor": "45", "label": "45 días"},
                    {"valor": "60", "label": "60 días (normal)"},
                    {"valor": "90", "label": "90 días"},
                ],
                "default": "60",
                "critica": True,
                "afecta_hallazgos": ["A.3", "A.4"],
                "ayuda": "Servicios usualmente tienen 30-60 días de términos"
            },
            {
                "id": "margen_esperado",
                "texto": "¿Margen de ganancia esperado por proyecto?",
                "tipo": "text",
                "placeholder": "25",
                "default": "25",
                "critica": True,
                "afecta_hallazgos": ["A.5"],
                "ayuda": "% margen bruto esperado. Bajo de esto = alerta"
            },
            {
                "id": "usa_proyectos",
                "texto": "¿Contabiliza por proyectos?",
                "tipo": "select",
                "opciones": [
                    {"valor": "SI", "label": "Sí (por proyecto)"},
                    {"valor": "NO", "label": "No (por cuenta general)"},
                ],
                "default": "SI",
                "critica": True,
                "afecta_hallazgos": [],
                "ayuda": "Determina si validar márgenes por proyecto"
            },
            {
                "id": "tiene_servicios_garantia",
                "texto": "¿Tiene servicios con período de garantía?",
                "tipo": "select",
                "opciones": [
                    {"valor": "SI", "label": "Sí"},
                    {"valor": "NO", "label": "No"},
                ],
                "default": "NO",
                "critica": False,
                "afecta_hallazgos": ["PROVISION"],
                "ayuda": "Requiere provisiones por garantías"
            },
            {
                "id": "tiene_anticipos_clientes",
                "texto": "¿Recibe anticipos de clientes?",
                "tipo": "select",
                "opciones": [
                    {"valor": "SI", "label": "Sí"},
                    {"valor": "NO", "label": "No"},
                ],
                "default": "SI",
                "critica": False,
                "afecta_hallazgos": ["INGRESOS"],
                "ayuda": "Requiere validación de reconocimiento de ingresos"
            },
        ]
    },

    "MANUFACTURA": {
        "nombre": "Manufactura / Producción",
        "preguntas": [
            {
                "id": "rango_vencimiento_cxc",
                "texto": "¿A cuántos días se considera CxC vencida?",
                "tipo": "select",
                "opciones": [
                    {"valor": "30", "label": "30 días"},
                    {"valor": "45", "label": "45 días"},
                    {"valor": "60", "label": "60 días (normal)"},
                    {"valor": "90", "label": "90 días"},
                ],
                "default": "60",
                "critica": True,
                "afecta_hallazgos": ["A.3", "A.4"],
                "ayuda": "Manufactura típicamente tiene ciclos 60-90d"
            },
            {
                "id": "rotacion_inventario_dias",
                "texto": "¿Cuántos días debería rotar el inventario?",
                "tipo": "text",
                "placeholder": "90",
                "default": "90",
                "critica": True,
                "afecta_hallazgos": ["A.5"],
                "ayuda": "Manufactura: 60-120d común"
            },
            {
                "id": "tiene_wip",
                "texto": "¿Tiene inventario WIP (Work in Process)?",
                "tipo": "select",
                "opciones": [
                    {"valor": "SI", "label": "Sí"},
                    {"valor": "NO", "label": "No"},
                ],
                "default": "SI",
                "critica": True,
                "afecta_hallazgos": ["A.5"],
                "ayuda": "Requiere validación de % WIP normal"
            },
            {
                "id": "pct_wip_normal",
                "texto": "¿% de WIP que se considera normal?",
                "tipo": "text",
                "placeholder": "15",
                "default": "15",
                "critica": True,
                "afecta_hallazgos": ["A.5"],
                "ayuda": "Por encima = posible retraso de producción"
            },
            {
                "id": "usa_costos_estandar",
                "texto": "¿Usa costos estándar vs costo real?",
                "tipo": "select",
                "opciones": [
                    {"valor": "ESTANDAR", "label": "Costo estándar"},
                    {"valor": "REAL", "label": "Costo real"},
                    {"valor": "PROMEDIO", "label": "Costo promedio"},
                ],
                "default": "REAL",
                "critica": True,
                "afecta_hallazgos": ["A.5"],
                "ayuda": "Método de valoración de inventario"
            },
            {
                "id": "tiene_bienes_construccion",
                "texto": "¿Tiene bienes en construcción (capex)?",
                "tipo": "select",
                "opciones": [
                    {"valor": "SI", "label": "Sí"},
                    {"valor": "NO", "label": "No"},
                ],
                "default": "SI",
                "critica": False,
                "afecta_hallazgos": ["A.5"],
                "ayuda": "Requiere validación de tiempo en construcción"
            },
        ]
    },

    "HOLDING": {
        "nombre": "Holding / Grupo Empresarial",
        "preguntas": [
            {
                "id": "pct_transacciones_relacionadas",
                "texto": "% de transacciones que son con relacionadas",
                "tipo": "text",
                "placeholder": "10",
                "default": "10",
                "critica": True,
                "afecta_hallazgos": ["B.2"],
                "ayuda": "Por encima = riesgo de concentración"
            },
            {
                "id": "usa_equity_method",
                "texto": "¿Usa método de equity para inversiones?",
                "tipo": "select",
                "opciones": [
                    {"valor": "SI", "label": "Sí (costo o equity)"},
                    {"valor": "NO", "label": "No (solo costo)"},
                ],
                "default": "SI",
                "critica": True,
                "afecta_hallazgos": ["A.5"],
                "ayuda": "NIIF requiere validar método de consolidación"
            },
            {
                "id": "tiene_cambios_control",
                "texto": "¿Hubo adquisiciones/ventas en el período?",
                "tipo": "select",
                "opciones": [
                    {"valor": "SI", "label": "Sí"},
                    {"valor": "NO", "label": "No"},
                ],
                "default": "NO",
                "critica": True,
                "afecta_hallazgos": ["A.5"],
                "ayuda": "Cambios de control requieren impairment analysis"
            },
            {
                "id": "centraliza_deuda",
                "texto": "¿Centraliza deuda de grupo o descentralizada?",
                "tipo": "select",
                "opciones": [
                    {"valor": "CENTRALIZADA", "label": "Centralizada (holding financia)"},
                    {"valor": "DESCENTRALIZADA", "label": "Descentralizada (cada empresa)"},
                ],
                "default": "CENTRALIZADA",
                "critica": False,
                "afecta_hallazgos": [],
                "ayuda": "Afecta análisis de transacciones relacionadas"
            },
            {
                "id": "tiene_garantias_pasivos",
                "texto": "¿Holding garantiza pasivos de controladas?",
                "tipo": "select",
                "opciones": [
                    {"valor": "SI", "label": "Sí"},
                    {"valor": "NO", "label": "No"},
                    {"valor": "PARCIALMENTE", "label": "Parcialmente"},
                ],
                "default": "SI",
                "critica": False,
                "afecta_hallazgos": ["CONTINGENCIAS"],
                "ayuda": "Requiere análisis de pasivos contingentes"
            },
        ]
    },

    "SALUD": {
        "nombre": "Salud / Clínica / Hospital / Farmacéutica",
        "preguntas": [
            {
                "id": "rango_vencimiento_cxc",
                "texto": "¿A cuántos días se considera CxC vencida?",
                "tipo": "select",
                "opciones": [
                    {"valor": "30", "label": "30 días"},
                    {"valor": "45", "label": "45 días"},
                    {"valor": "60", "label": "60 días (pacientes)"},
                    {"valor": "90", "label": "90 días (seguros)"},
                ],
                "default": "60",
                "critica": True,
                "afecta_hallazgos": ["A.3", "A.4"],
                "ayuda": "Salud: pacientes 30d, seguros pueden ser 60-90d"
            },
            {
                "id": "tipo_entidad_salud",
                "texto": "¿Tipo de entidad de salud?",
                "tipo": "select",
                "opciones": [
                    {"valor": "CLINICA", "label": "Clínica pequeña"},
                    {"valor": "HOSPITAL", "label": "Hospital"},
                    {"valor": "FARMACEUTICA", "label": "Farmacéutica"},
                    {"valor": "OTRO", "label": "Otro"},
                ],
                "default": "CLINICA",
                "critica": True,
                "afecta_hallazgos": [],
                "ayuda": "Cada tipo tiene riesgos diferentes"
            },
            {
                "id": "pct_seguros_vs_pacientes",
                "texto": "% de ingresos de seguros vs pacientes directos",
                "tipo": "text",
                "placeholder": "70",
                "default": "70",
                "critica": True,
                "afecta_hallazgos": ["A.4"],
                "ayuda": "Alto % seguros = CxC más largo"
            },
            {
                "id": "tiene_medicinas_vencidas",
                "texto": "¿Hay rotación lenta de medicinas?",
                "tipo": "select",
                "opciones": [
                    {"valor": "SI", "label": "Sí (riesgo de vencimiento)"},
                    {"valor": "NO", "label": "No (rotación rápida)"},
                ],
                "default": "SI",
                "critica": False,
                "afecta_hallazgos": ["A.5"],
                "ayuda": "Requiere validación de obsolescencia"
            },
            {
                "id": "usa_arco_norm",
                "texto": "¿Está regulado por ARCO o SBS?",
                "tipo": "select",
                "opciones": [
                    {"valor": "SI", "label": "Sí"},
                    {"valor": "NO", "label": "No"},
                ],
                "default": "NO",
                "critica": False,
                "afecta_hallazgos": [],
                "ayuda": "Regulación adicional requiere validaciones extra"
            },
        ]
    },

    "EDUCACION": {
        "nombre": "Educación / Universidad / Colegio",
        "preguntas": [
            {
                "id": "rango_vencimiento_pensiones",
                "texto": "¿A cuántos meses se considera pensión vencida?",
                "tipo": "select",
                "opciones": [
                    {"valor": "1", "label": "1 mes (muy estricto)"},
                    {"valor": "2", "label": "2 meses (estándar)"},
                    {"valor": "3", "label": "3 meses (flexible)"},
                    {"valor": "6", "label": "6 meses"},
                ],
                "default": "3",
                "critica": True,
                "afecta_hallazgos": ["A.3", "A.4"],
                "ayuda": "Educación: pensiones 30-90d común"
            },
            {
                "id": "tipo_institucion",
                "texto": "¿Tipo de institución?",
                "tipo": "select",
                "opciones": [
                    {"valor": "COLEGIO", "label": "Colegio (K-12)"},
                    {"valor": "UNIVERSIDAD_PRIVADA", "label": "Universidad privada"},
                    {"valor": "INSTITUTO", "label": "Instituto técnico"},
                    {"valor": "OTRO", "label": "Otro"},
                ],
                "default": "COLEGIO",
                "critica": True,
                "afecta_hallazgos": [],
                "ayuda": "Cada tipo tiene estructura financiera diferente"
            },
            {
                "id": "pct_becas",
                "texto": "% de estudiantes con beca/ayuda financiera",
                "tipo": "text",
                "placeholder": "20",
                "default": "20",
                "critica": True,
                "afecta_hallazgos": ["A.4"],
                "ayuda": "Alto = menor cobranza, mayor provisión"
            },
            {
                "id": "tiene_endowment",
                "texto": "¿Tiene endowment o fondo patrimonial?",
                "tipo": "select",
                "opciones": [
                    {"valor": "SI", "label": "Sí"},
                    {"valor": "NO", "label": "No"},
                ],
                "default": "NO",
                "critica": False,
                "afecta_hallazgos": ["A.5"],
                "ayuda": "Requiere valuación especial"
            },
            {
                "id": "tiene_investigacion",
                "texto": "¿Tiene ingresos por investigación?",
                "tipo": "select",
                "opciones": [
                    {"valor": "SI", "label": "Sí"},
                    {"valor": "NO", "label": "No"},
                ],
                "default": "NO",
                "critica": False,
                "afecta_hallazgos": ["INGRESOS"],
                "ayuda": "Requiere validación de ingresos diferidos"
            },
        ]
    },
}


def obtener_preguntas(tipo_entidad: str) -> dict | None:
    """
    Obtiene preguntas para un tipo de entidad

    Args:
        tipo_entidad: BANCO, RETAIL, SERVICIOS, MANUFACTURA, HOLDING, SALUD, EDUCACION

    Returns:
        Dict con preguntas o None si tipo no existe
    """
    return CONFIGURACION_INDUSTRIAS.get(tipo_entidad)


def obtener_tipos_entidad() -> list:
    """
    Obtiene lista de todos los tipos de entidad soportados
    """
    return [
        {"tipo": k, "nombre": v["nombre"]}
        for k, v in CONFIGURACION_INDUSTRIAS.items()
    ]
