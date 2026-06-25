"""
Configuracion dinamica por tipo de industria/entidad.
Incluye una base general tipo CaseWare y bloques especificos por negocio.
"""

from __future__ import annotations

from copy import deepcopy


GENERAL_QUESTIONS = [
    {
        "id": "estructura_entidad",
        "texto": "La estructura de la entidad es una compania.",
        "tipo": "select",
        "opciones": [{"valor": "SI", "label": "Si"}, {"valor": "NO", "label": "No"}],
        "default": "SI",
        "critica": True,
        "ayuda": "Valida si el perfil base corresponde a una persona juridica operativa.",
    },
    {
        "id": "perfil_adecuado",
        "texto": "Se esta utilizando el perfil adecuado para este compromiso.",
        "tipo": "select",
        "opciones": [{"valor": "SI", "label": "Si"}, {"valor": "NO", "label": "No"}],
        "default": "SI",
        "critica": True,
        "ayuda": "Si es NO, el perfil debe corregirse antes de continuar.",
    },
    {
        "id": "cumple_nia_315",
        "texto": "El compromiso sigue la NIA 315 (Revisada 2019).",
        "tipo": "select",
        "opciones": [{"valor": "SI", "label": "Si"}, {"valor": "NO", "label": "No"}],
        "default": "SI",
        "critica": True,
        "ayuda": "Base para la evaluacion de riesgos de incorreccion material.",
    },
    {
        "id": "cumple_nia_220",
        "texto": "El compromiso sigue la NIA 220 (Revisada) y la NICC 2.",
        "tipo": "select",
        "opciones": [{"valor": "SI", "label": "Si"}, {"valor": "NO", "label": "No"}],
        "default": "SI",
        "critica": True,
        "ayuda": "Permite calibrar el control de calidad del encargo.",
    },
    {
        "id": "es_proposito_especial",
        "texto": "El compromiso es una auditoria de proposito especial.",
        "tipo": "select",
        "opciones": [{"valor": "SI", "label": "Si"}, {"valor": "NO", "label": "No"}],
        "default": "NO",
        "critica": True,
        "ayuda": "Impacta la lectura del marco contable y los procedimientos.",
    },
    {
        "id": "continuacion_compromiso",
        "texto": "Esta es una continuidad de un compromiso de auditoria.",
        "tipo": "select",
        "opciones": [{"valor": "SI", "label": "Si"}, {"valor": "NO", "label": "No"}],
        "default": "SI",
        "critica": True,
        "ayuda": "Sirve para reutilizar antecedentes y comparativos.",
    },
    {
        "id": "requiere_experto",
        "texto": "Sera requerido un auditor experto.",
        "tipo": "select",
        "opciones": [{"valor": "SI", "label": "Si"}, {"valor": "NO", "label": "No"}],
        "default": "NO",
        "critica": False,
        "ayuda": "Define si el encargo necesita apoyo tecnico especializado.",
    },
    {
        "id": "incluir_vistas_riesgo",
        "texto": "Incluir vistas detalladas del informe de riesgo.",
        "tipo": "select",
        "opciones": [{"valor": "SI", "label": "Si"}, {"valor": "NO", "label": "No"}],
        "default": "SI",
        "critica": False,
        "ayuda": "Activa vistas ampliadas para supervision y revisiones.",
    },
    {
        "id": "empresa_en_marcha",
        "texto": "Se ha anticipado que sera identificada la condicion de empresa en marcha.",
        "tipo": "select",
        "opciones": [{"valor": "SI", "label": "Si"}, {"valor": "NO", "label": "No"}],
        "default": "NO",
        "critica": True,
        "ayuda": "Permite elevar foco en liquidez, continuidad y eventos subsecuentes.",
    },
    {
        "id": "tiene_provisiones_estimaciones",
        "texto": "Los estados financieros incluyen estimaciones, devengos, pagos anticipados y provisiones.",
        "tipo": "select",
        "opciones": [{"valor": "SI", "label": "Si"}, {"valor": "NO", "label": "No"}],
        "default": "SI",
        "critica": True,
        "ayuda": "Si es SI, se deben reforzar pruebas de estimacion y corte.",
    },
    {
        "id": "ti_provee_servicios",
        "texto": "El entorno de TI incluye una organizacion que provee servicios tecnologicos.",
        "tipo": "select",
        "opciones": [{"valor": "SI", "label": "Si"}, {"valor": "NO", "label": "No"}],
        "default": "SI",
        "critica": False,
        "ayuda": "Impacta el alcance de controles generales y accesos.",
    },
    {
        "id": "usa_comercio_electronico",
        "texto": "La entidad tiene comercio electronico o ventas por canales digitales.",
        "tipo": "select",
        "opciones": [{"valor": "SI", "label": "Si"}, {"valor": "NO", "label": "No"}],
        "default": "NO",
        "critica": False,
        "ayuda": "Afecta corte, ingresos, devoluciones y analiticos de ventas.",
    },
    {
        "id": "ciclo_ingresos_cxc",
        "texto": "La entidad posee el ciclo de ingresos, cuentas por cobrar y entradas.",
        "tipo": "select",
        "opciones": [{"valor": "SI", "label": "Si"}, {"valor": "NO", "label": "No"}],
        "default": "SI",
        "critica": True,
        "ayuda": "Ciclo basico para casi todo encargo operativo.",
    },
    {
        "id": "ciclo_compras_cxp",
        "texto": "La entidad posee el ciclo de compras, cuentas por pagar y pagos.",
        "tipo": "select",
        "opciones": [{"valor": "SI", "label": "Si"}, {"valor": "NO", "label": "No"}],
        "default": "SI",
        "critica": True,
        "ayuda": "Necesario para validar pasivos, corte y devengos.",
    },
    {
        "id": "ciclo_nomina",
        "texto": "La entidad posee el ciclo de nomina.",
        "tipo": "select",
        "opciones": [{"valor": "SI", "label": "Si"}, {"valor": "NO", "label": "No"}],
        "default": "SI",
        "critica": False,
        "ayuda": "Ayuda a definir procedimientos de sueldos y beneficios.",
    },
    {
        "id": "ciclo_informes_financieros",
        "texto": "La entidad posee el ciclo de informes financieros.",
        "tipo": "select",
        "opciones": [{"valor": "SI", "label": "Si"}, {"valor": "NO", "label": "No"}],
        "default": "SI",
        "critica": True,
        "ayuda": "Define el nivel de formalizacion del cierre y reporting.",
    },
    {
        "id": "ciclo_inventario",
        "texto": "La entidad posee el ciclo de inventario.",
        "tipo": "select",
        "opciones": [{"valor": "SI", "label": "Si"}, {"valor": "NO", "label": "No"}],
        "default": "NO",
        "critica": True,
        "ayuda": "Clave para retail, manufactura y entidades con stock.",
    },
    {
        "id": "ciclo_inversiones",
        "texto": "La entidad posee el ciclo de inversiones.",
        "tipo": "select",
        "opciones": [{"valor": "SI", "label": "Si"}, {"valor": "NO", "label": "No"}],
        "default": "NO",
        "critica": True,
        "ayuda": "Relevante para holdings, fondos, fideicomisos y financieras.",
    },
]


def _merge_questions(*groups: list[dict]) -> list[dict]:
    merged: list[dict] = []
    seen: set[str] = set()
    for group in groups:
        for item in group:
            qid = item.get("id")
            if not isinstance(qid, str) or qid in seen:
                continue
            seen.add(qid)
            merged.append(deepcopy(item))
    return merged


CONFIGURACION_INDUSTRIAS = {
    "BANCO": {
        "nombre": "Entidad Financiera / Banco",
        "preguntas": [
            {
                "id": "rango_vencimiento",
                "texto": "¿Rango de vencimiento para cartera vencida?",
                "tipo": "select",
                "opciones": [
                    {"valor": "15", "label": "15 dias"},
                    {"valor": "30", "label": "30 dias (default)"},
                    {"valor": "45", "label": "45 dias"},
                    {"valor": "90", "label": "90 dias"},
                ],
                "default": "30",
                "critica": True,
                "ayuda": "Define cuando una cartera se considera vencida.",
            },
            {
                "id": "clasificacion_cartera",
                "texto": "¿Que clasificacion de cartera usa?",
                "tipo": "select",
                "opciones": [
                    {"valor": "ABCDE", "label": "A/B/C/D/E"},
                    {"valor": "VIGENTE_VENCIDA", "label": "Vigente/Vencida"},
                    {"valor": "OTRO", "label": "Otro"},
                ],
                "default": "ABCDE",
                "critica": True,
                "ayuda": "Clasificacion interna de riesgo crediticio.",
            },
            {
                "id": "provisiones_pct",
                "texto": "% de provision esperado por clasificacion",
                "tipo": "text",
                "placeholder": "0.5,1,2,5,10",
                "default": "0.5,1,2,5,10",
                "critica": True,
                "ayuda": "Separado por comas.",
            },
            {
                "id": "tiene_obligaciones_publico",
                "texto": "¿Tiene obligaciones con el publico (depositos)?",
                "tipo": "select",
                "opciones": [{"valor": "SI", "label": "Si"}, {"valor": "NO", "label": "No"}],
                "default": "SI",
                "critica": False,
                "ayuda": "Determina analisis de liquidez y reservas.",
            },
        ],
    },
    "COOPERATIVAS": {
        "nombre": "Cooperativas / Ahorro y Credito",
        "preguntas": [
            {
                "id": "tipo_cooperativa",
                "texto": "¿Que tipo de cooperativa es?",
                "tipo": "select",
                "opciones": [
                    {"valor": "AHORRO_CREDITO", "label": "Ahorro y credito"},
                    {"valor": "PRODUCCION", "label": "Produccion / Servicios"},
                    {"valor": "CONSUMO", "label": "Consumo"},
                    {"valor": "OTRO", "label": "Otro"},
                ],
                "default": "AHORRO_CREDITO",
                "critica": True,
                "ayuda": "Contextualiza cartera, aportes y excedentes.",
            },
            {
                "id": "rango_vencimiento_cartera",
                "texto": "¿A cuantos dias se considera vencida la cartera de socios?",
                "tipo": "select",
                "opciones": [
                    {"valor": "30", "label": "30 dias"},
                    {"valor": "60", "label": "60 dias"},
                    {"valor": "90", "label": "90 dias"},
                    {"valor": "120", "label": "120 dias"},
                ],
                "default": "60",
                "critica": True,
                "ayuda": "Calibra mora y provision de cartera social.",
            },
            {
                "id": "tiene_aportes_obligatorios",
                "texto": "¿Existen aportes obligatorios de socios?",
                "tipo": "select",
                "opciones": [{"valor": "SI", "label": "Si"}, {"valor": "NO", "label": "No"}],
                "default": "SI",
                "critica": False,
                "ayuda": "Importante para capital social y patrimonializacion.",
            },
            {
                "id": "tiene_beneficios_sociales",
                "texto": "¿Otorga beneficios sociales, bonos o retornos a socios?",
                "tipo": "select",
                "opciones": [{"valor": "SI", "label": "Si"}, {"valor": "NO", "label": "No"}],
                "default": "NO",
                "critica": False,
                "ayuda": "Puede afectar provisiones y distribucion de excedentes.",
            },
        ],
    },
    "RETAIL": {
        "nombre": "Retail / Comercio / Distribuidora",
        "preguntas": [
            {
                "id": "rango_vencimiento_cxc",
                "texto": "¿A cuantos dias se considera CxC vencida?",
                "tipo": "select",
                "opciones": [
                    {"valor": "30", "label": "30 dias"},
                    {"valor": "45", "label": "45 dias"},
                    {"valor": "60", "label": "60 dias"},
                    {"valor": "90", "label": "90 dias"},
                ],
                "default": "60",
                "critica": True,
                "ayuda": "Retail suele tener ciclos mas largos que servicios.",
            },
            {
                "id": "inventario_pct_activos",
                "texto": "¿Que % de inventario esperas vs total activos?",
                "tipo": "select",
                "opciones": [
                    {"valor": "30", "label": "30-40%"},
                    {"valor": "50", "label": "40-60%"},
                    {"valor": "70", "label": "60-80%"},
                    {"valor": "custom", "label": "Personalizado"},
                ],
                "default": "50",
                "critica": True,
                "ayuda": "Parametro clave para detectar desbalances.",
            },
            {
                "id": "rotacion_inventario_dias",
                "texto": "¿Cuantos dias deberia rotar el inventario?",
                "tipo": "text",
                "placeholder": "45",
                "default": "60",
                "critica": True,
                "ayuda": "Ej: moda 30-45d, electronica 45-90d.",
            },
            {
                "id": "tiene_consignaciones",
                "texto": "¿Tiene inventario en consignacion de proveedores?",
                "tipo": "select",
                "opciones": [{"valor": "SI", "label": "Si"}, {"valor": "NO", "label": "No"}],
                "default": "NO",
                "critica": False,
                "ayuda": "Requiere validacion especial de corte.",
            },
        ],
    },
    "SERVICIOS": {
        "nombre": "Servicios / Consultoria / Legal",
        "preguntas": [
            {
                "id": "rango_vencimiento_cxc",
                "texto": "¿A cuantos dias se considera CxC vencida?",
                "tipo": "select",
                "opciones": [
                    {"valor": "30", "label": "30 dias"},
                    {"valor": "45", "label": "45 dias"},
                    {"valor": "60", "label": "60 dias"},
                    {"valor": "90", "label": "90 dias"},
                ],
                "default": "60",
                "critica": True,
                "ayuda": "Servicios suelen tener terminos de 30-60 dias.",
            },
            {
                "id": "margen_esperado",
                "texto": "¿Margen de ganancia esperado por proyecto?",
                "tipo": "text",
                "placeholder": "25",
                "default": "25",
                "critica": True,
                "ayuda": "Margen bruto esperado. Bajo de esto = alerta.",
            },
            {
                "id": "usa_proyectos",
                "texto": "¿Contabiliza por proyectos?",
                "tipo": "select",
                "opciones": [
                    {"valor": "SI", "label": "Si (por proyecto)"},
                    {"valor": "NO", "label": "No (por cuenta general)"},
                ],
                "default": "SI",
                "critica": True,
                "ayuda": "Determina si validar margenes por proyecto.",
            },
            {
                "id": "tiene_anticipos_clientes",
                "texto": "¿Recibe anticipos de clientes?",
                "tipo": "select",
                "opciones": [{"valor": "SI", "label": "Si"}, {"valor": "NO", "label": "No"}],
                "default": "SI",
                "critica": False,
                "ayuda": "Requiere validacion de reconocimiento de ingresos.",
            },
        ],
    },
    "MANUFACTURA": {
        "nombre": "Manufactura / Produccion",
        "preguntas": [
            {
                "id": "rotacion_inventario_dias",
                "texto": "¿Cuantos dias deberia rotar el inventario?",
                "tipo": "text",
                "placeholder": "90",
                "default": "90",
                "critica": True,
                "ayuda": "Manufactura suele tener ciclos mas largos.",
            },
            {
                "id": "tiene_wip",
                "texto": "¿Tiene inventario WIP (Work in Process)?",
                "tipo": "select",
                "opciones": [{"valor": "SI", "label": "Si"}, {"valor": "NO", "label": "No"}],
                "default": "SI",
                "critica": True,
                "ayuda": "Requiere validacion de porcentaje WIP normal.",
            },
            {
                "id": "pct_wip_normal",
                "texto": "¿% de WIP que se considera normal?",
                "tipo": "text",
                "placeholder": "15",
                "default": "15",
                "critica": True,
                "ayuda": "Por encima = posible retraso de produccion.",
            },
            {
                "id": "usa_costos_estandar",
                "texto": "¿Usa costos estandar vs costo real?",
                "tipo": "select",
                "opciones": [
                    {"valor": "ESTANDAR", "label": "Costo estandar"},
                    {"valor": "REAL", "label": "Costo real"},
                    {"valor": "PROMEDIO", "label": "Costo promedio"},
                ],
                "default": "REAL",
                "critica": True,
                "ayuda": "Metodo de valuacion de inventario.",
            },
        ],
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
                "ayuda": "Por encima = riesgo de concentracion.",
            },
            {
                "id": "usa_equity_method",
                "texto": "¿Usa metodo de equity para inversiones?",
                "tipo": "select",
                "opciones": [
                    {"valor": "SI", "label": "Si (costo o equity)"},
                    {"valor": "NO", "label": "No (solo costo)"},
                ],
                "default": "SI",
                "critica": True,
                "ayuda": "NIIF requiere validar metodo de consolidacion.",
            },
            {
                "id": "tiene_cambios_control",
                "texto": "¿Hubo adquisiciones/ventas en el periodo?",
                "tipo": "select",
                "opciones": [{"valor": "SI", "label": "Si"}, {"valor": "NO", "label": "No"}],
                "default": "NO",
                "critica": True,
                "ayuda": "Cambios de control requieren impairment analysis.",
            },
            {
                "id": "tiene_garantias_pasivos",
                "texto": "¿Holding garantiza pasivos de controladas?",
                "tipo": "select",
                "opciones": [
                    {"valor": "SI", "label": "Si"},
                    {"valor": "NO", "label": "No"},
                    {"valor": "PARCIALMENTE", "label": "Parcialmente"},
                ],
                "default": "SI",
                "critica": False,
                "ayuda": "Requiere analisis de pasivos contingentes.",
            },
        ],
    },
    "FIDEICOMISOS": {
        "nombre": "Fideicomisos / Patrimonios Autonomos",
        "preguntas": [
            {
                "id": "tipo_fideicomiso",
                "texto": "¿Que tipo de fideicomiso es?",
                "tipo": "select",
                "opciones": [
                    {"valor": "MERCANTIL", "label": "Mercantil"},
                    {"valor": "INMOBILIARIO", "label": "Inmobiliario"},
                    {"valor": "GARANTIA", "label": "Garantia"},
                    {"valor": "ADMINISTRACION", "label": "Administracion"},
                    {"valor": "OTRO", "label": "Otro"},
                ],
                "default": "ADMINISTRACION",
                "critica": True,
                "ayuda": "Ayuda a entender la naturaleza economica del patrimonio.",
            },
            {
                "id": "administra_recursos_terceros",
                "texto": "¿Administra recursos de terceros o beneficiarios?",
                "tipo": "select",
                "opciones": [{"valor": "SI", "label": "Si"}, {"valor": "NO", "label": "No"}],
                "default": "SI",
                "critica": True,
                "ayuda": "Determina trazabilidad y segregacion de fondos.",
            },
            {
                "id": "tiene_bienes_fideicomitidos",
                "texto": "¿Existen bienes fideicomitidos o activos administrados?",
                "tipo": "select",
                "opciones": [{"valor": "SI", "label": "Si"}, {"valor": "NO", "label": "No"}],
                "default": "SI",
                "critica": True,
                "ayuda": "Requiere controles especiales sobre activos administrados.",
            },
            {
                "id": "ingresos_por_comision",
                "texto": "¿Reconoce ingresos por comisiones, administracion o estructuracion?",
                "tipo": "select",
                "opciones": [{"valor": "SI", "label": "Si"}, {"valor": "NO", "label": "No"}],
                "default": "SI",
                "critica": False,
                "ayuda": "Importante para corte y reconocimiento por servicios prestados.",
            },
        ],
    },
    "SALUD": {
        "nombre": "Salud / Clinica / Hospital / Farmaceutica",
        "preguntas": [
            {
                "id": "rango_vencimiento_cxc",
                "texto": "¿A cuantos dias se considera CxC vencida?",
                "tipo": "select",
                "opciones": [
                    {"valor": "30", "label": "30 dias"},
                    {"valor": "45", "label": "45 dias"},
                    {"valor": "60", "label": "60 dias (pacientes)"},
                    {"valor": "90", "label": "90 dias (seguros)"},
                ],
                "default": "60",
                "critica": True,
                "ayuda": "Pacientes 30d, seguros pueden ser 60-90d.",
            },
            {
                "id": "tipo_entidad_salud",
                "texto": "¿Tipo de entidad de salud?",
                "tipo": "select",
                "opciones": [
                    {"valor": "CLINICA", "label": "Clinica"},
                    {"valor": "HOSPITAL", "label": "Hospital"},
                    {"valor": "FARMACEUTICA", "label": "Farmaceutica"},
                    {"valor": "OTRO", "label": "Otro"},
                ],
                "default": "CLINICA",
                "critica": True,
                "ayuda": "Cada tipo tiene riesgos diferentes.",
            },
            {
                "id": "pct_seguros_vs_pacientes",
                "texto": "% de ingresos de seguros vs pacientes directos",
                "tipo": "text",
                "placeholder": "70",
                "default": "70",
                "critica": True,
                "ayuda": "Alto % seguros = CxC mas largo.",
            },
            {
                "id": "usa_arco_norm",
                "texto": "¿Esta regulado por ARCO o SBS?",
                "tipo": "select",
                "opciones": [{"valor": "SI", "label": "Si"}, {"valor": "NO", "label": "No"}],
                "default": "NO",
                "critica": False,
                "ayuda": "Regulacion adicional requiere validaciones extra.",
            },
        ],
    },
    "EDUCACION": {
        "nombre": "Educacion / Universidad / Colegio",
        "preguntas": [
            {
                "id": "rango_vencimiento_pensiones",
                "texto": "¿A cuantos meses se considera pension vencida?",
                "tipo": "select",
                "opciones": [
                    {"valor": "1", "label": "1 mes"},
                    {"valor": "2", "label": "2 meses"},
                    {"valor": "3", "label": "3 meses"},
                    {"valor": "6", "label": "6 meses"},
                ],
                "default": "3",
                "critica": True,
                "ayuda": "Educacion: pensiones 30-90d comun.",
            },
            {
                "id": "tipo_institucion",
                "texto": "¿Tipo de institucion?",
                "tipo": "select",
                "opciones": [
                    {"valor": "COLEGIO", "label": "Colegio"},
                    {"valor": "UNIVERSIDAD_PRIVADA", "label": "Universidad privada"},
                    {"valor": "INSTITUTO", "label": "Instituto tecnico"},
                    {"valor": "OTRO", "label": "Otro"},
                ],
                "default": "COLEGIO",
                "critica": True,
                "ayuda": "Cada tipo tiene estructura financiera diferente.",
            },
            {
                "id": "pct_becas",
                "texto": "% de estudiantes con beca/ayuda financiera",
                "tipo": "text",
                "placeholder": "20",
                "default": "20",
                "critica": True,
                "ayuda": "Alto = menor cobranza, mayor provision.",
            },
            {
                "id": "tiene_endowment",
                "texto": "¿Tiene endowment o fondo patrimonial?",
                "tipo": "select",
                "opciones": [{"valor": "SI", "label": "Si"}, {"valor": "NO", "label": "No"}],
                "default": "NO",
                "critica": False,
                "ayuda": "Requiere valuacion especial.",
            },
        ],
    },
}


def obtener_preguntas(tipo_entidad: str) -> dict | None:
    """
    Obtiene preguntas para un tipo de entidad.

    Para cualquier tipo especifico, mezcla preguntas generales + preguntas del tipo.
    Si tipo_entidad es GENERAL, devuelve solo la base general.
    """
    tipo_upper = (tipo_entidad or "").upper().strip()
    if tipo_upper == "GENERAL":
        return {
            "nombre": "Configuracion general del encargo",
            "preguntas": deepcopy(GENERAL_QUESTIONS),
        }

    configuracion = CONFIGURACION_INDUSTRIAS.get(tipo_upper)
    if not configuracion:
        return None

    return {
        "nombre": f"Configuracion general + {configuracion['nombre']}",
        "preguntas": _merge_questions(GENERAL_QUESTIONS, configuracion.get("preguntas", [])),
    }


def obtener_tipos_entidad() -> list:
    """Obtiene lista de todos los tipos de entidad soportados."""
    return [{"tipo": k, "nombre": v["nombre"]} for k, v in CONFIGURACION_INDUSTRIAS.items()]
