"""
Servicio de Materialidad Asistida

Sugiere valores de materialidad basado en NIAs y reglas de negocio.
El auditor siempre decide el valor final.

NIA 320: Materialidad en la planificación y ejecución de auditoría
"""

import builtins
import yaml
from pathlib import Path
from typing import Optional, Dict, Any
from domain.services.leer_perfil import leer_perfil
from analysis.lector_tb import leer_tb, obtener_resumen_tb


# Rutas
DATA_ROOT = Path(__file__).parent.parent.parent / "data"
REGLAS_PATH = DATA_ROOT / "catalogos" / "reglas_materialidad.yaml"


def print(*args, **kwargs):  # type: ignore[override]
    try:
        builtins.print(*args, **kwargs)
    except UnicodeEncodeError:
        safe_args = [str(arg).encode("ascii", "ignore").decode("ascii") for arg in args]
        builtins.print(*safe_args, **kwargs)


def obtener_reglas() -> Dict:
    """
    Carga las reglas de materialidad desde YAML.
    
    Returns:
        dict: Reglas de materialidad completas
    """
    try:
        if not REGLAS_PATH.exists():
            print(f"⚠️  No se encontró {REGLAS_PATH}")
            return _reglas_por_defecto()
        
        with open(REGLAS_PATH, 'r', encoding='utf-8') as f:
            reglas = yaml.safe_load(f)
        
        return reglas if reglas else _reglas_por_defecto()
    except Exception as e:
        print(f"⚠️  Error cargando reglas: {e}")
        return _reglas_por_defecto()


def _reglas_por_defecto() -> Dict:
    """Retorna reglas por defecto si no se encuentran las del YAML."""
    return {
        'regla_defecto': {
            'base': 'activos',
            'porcentaje_min': 0.03,
            'porcentaje_max': 0.05,
            'descripcion': 'Regla por defecto'
        }
    }


def obtener_regla_materialidad(cliente: str) -> Optional[Dict]:
    """
    Obtiene la regla de materialidad aplicable para un cliente.
    
    Busca primero por tipo_entidad, luego por sector.
    
    Args:
        cliente: Nombre del cliente
        
    Returns:
        dict: Regla con campos base, porcentaje_min, porcentaje_max
        None: Si no se puede determinar
    """
    try:
        perfil = leer_perfil(cliente)
        
        if not perfil:
            print(f"⚠️  No se encontró perfil para {cliente}")
            reglas = obtener_reglas()
            return reglas.get('regla_defecto')
        
        reglas = obtener_reglas()
        reglas_entidad = reglas.get('reglas_por_entidad', {})
        reglas_sector = reglas.get('reglas_por_sector', {})
        regla_defecto = reglas.get('regla_defecto', {})
        
        # 1. Buscar por tipo_entidad (normalizado)
        tipo_entidad = perfil.get('cliente', {}).get('tipo_entidad', '').upper().replace(' ', '_')
        
        if tipo_entidad in reglas_entidad:
            regla = reglas_entidad[tipo_entidad].copy()
            regla['origen'] = f'tipo_entidad: {tipo_entidad}'
            print(f"✅ Regla encontrada por tipo_entidad: {tipo_entidad}")
            return regla
        
        # 2. Buscar por sector (normalizado)
        sector = perfil.get('cliente', {}).get('sector', '').lower().replace(' ', '_')
        
        if sector in reglas_sector:
            regla = reglas_sector[sector].copy()
            regla['origen'] = f'sector: {sector}'
            print(f"✅ Regla encontrada por sector: {sector}")
            return regla
        
        # 3. Usar regla por defecto
        regla = regla_defecto.copy()
        regla['origen'] = 'Regla por defecto'
        print(f"ℹ️  Usando regla por defecto")
        return regla
        
    except Exception as e:
        print(f"❌ Error obteniendo regla: {e}")
        reglas = obtener_reglas()
        return reglas.get('regla_defecto')


def obtener_base_materialidad(cliente: str, base_requerida: str) -> Optional[float]:
    """
    Obtiene el valor de la base para calcular materialidad.
    
    Args:
        cliente: Nombre del cliente
        base_requerida: 'activos', 'patrimonio', 'ingresos'
        
    Returns:
        float: Valor de la base o None
        
    Ejemplo:
        >>> base = obtener_base_materialidad("cliente_demo", "activos")
        >>> print(base)  # 8325000.0
    """
    try:
        resumen_tb = obtener_resumen_tb(cliente)
        
        if not resumen_tb:
            print(f"⚠️  No se encontró TB para {cliente}")
            return None
        
        # Mapear bases del TB
        mapa_bases = {
            'activos': resumen_tb.get('ACTIVO', 0),
            'pasivos': resumen_tb.get('PASIVO', 0),
            'patrimonio': resumen_tb.get('PATRIMONIO', 0),
            'ingresos': resumen_tb.get('INGRESOS', 0)
        }
        
        base_normalizada = base_requerida.lower()
        
        if base_normalizada not in mapa_bases:
            print(f"⚠️  Base desconocida: {base_requerida}")
            return None
        
        valor = mapa_bases[base_normalizada]
        
        if valor <= 0:
            print(f"⚠️  La base '{base_requerida}' tiene valor 0 o negativo")
            return None
        
        return float(valor)
        
    except Exception as e:
        print(f"❌ Error obteniendo base: {e}")
        return None


def calcular_materialidad(cliente: str, base_valor: Optional[float] = None) -> Optional[Dict]:
    """
    Calcula materialidad sugerida para un cliente.
    
    Incluye: min, max, desempeño y error trivial.
    
    Args:
        cliente: Nombre del cliente
        base_valor: Valor de la base (si no lo proporciona, se obtiene del TB)
        
    Returns:
        dict: Cálculos de materialidad o None si falla
        
    Ejemplo:
        >>> resultado = calcular_materialidad("cliente_demo")
        >>> print(f"Sugerida: ${resultado['materialidad_sugerida']:.0f}")
    """
    try:
        # Obtener regla
        regla = obtener_regla_materialidad(cliente)
        
        if not regla:
            print(f"❌ No se puede obtener regla de materialidad")
            return None
        
        base_requerida = regla.get('base', 'activos')
        pct_min = regla.get('porcentaje_min', 0.03)
        pct_max = regla.get('porcentaje_max', 0.05)
        
        # Obtener valor de la base si no se proporciona
        if base_valor is None:
            base_valor = obtener_base_materialidad(cliente, base_requerida)
        
        if base_valor is None:
            print(f"❌ No se puede determinar base de materialidad")
            return None
        
        # Calcular materialidades
        materialidad_min = base_valor * pct_min
        materialidad_max = base_valor * pct_max
        
        # Materialidad sugerida = promedio de min y max
        materialidad_sugerida = (materialidad_min + materialidad_max) / 2
        
        # Materialidad de desempeño (NIA 320) = 75% de materialidad elegida
        # Si no existe materialidad elegida, usamos la sugerida
        materialidad_desempeno = materialidad_sugerida * 0.75
        
        # Error trivial (NIA 320) = 5% de materialidad elegida
        # Aprox. 5% de la materialidad sugerida
        error_trivial = materialidad_sugerida * 0.05
        
        resultado = {
            'cliente': cliente,
            'base_utilizada': base_requerida,
            'valor_base': round(base_valor, 2),
            'porcentaje_minimo': round(pct_min * 100, 2),
            'porcentaje_maximo': round(pct_max * 100, 2),
            'materialidad_minima': round(materialidad_min, 2),
            'materialidad_maxima': round(materialidad_max, 2),
            'materialidad_sugerida': round(materialidad_sugerida, 2),
            'materialidad_desempeno': round(materialidad_desempeno, 2),
            'error_trivial': round(error_trivial, 2),
            'origen_regla': regla.get('origen', 'Unknown'),
            'descripcion_regla': regla.get('descripcion', 'N/A')
        }
        
        print(f"✅ Materialidad calculada para {cliente}")
        return resultado
        
    except Exception as e:
        print(f"❌ Error calculando materialidad: {e}")
        return None


def sugerir_materialidad(cliente: str) -> Optional[Dict]:
    """
    Obtiene sugerencia completa de materialidad (recomendación para el auditor).
    
    Esta es la función principal que el auditor usa.
    
    Args:
        cliente: Nombre del cliente
        
    Returns:
        dict: Sugerencia con análisis y recomendación
        
    Ejemplo:
        >>> suggestion = sugerir_materialidad("cliente_demo")
        >>> print(suggestion['recomendacion'])
    """
    try:
        calculo = calcular_materialidad(cliente)
        
        if not calculo:
            return None
        
        perfil = leer_perfil(cliente)
        
        # Generar recomendación
        recomendacion = (
            f"Para {perfil.get('cliente', {}).get('nombre_legal', 'Cliente')}, "
            f"se sugiere usar materialidad de ${calculo['materialidad_sugerida']:,.0f} "
            f"({calculo['porcentaje_maximo']}% de {calculo['base_utilizada']}). "
            f"Rango aceptable: ${calculo['materialidad_minima']:,.0f} - ${calculo['materialidad_maxima']:,.0f}"
        )
        
        sugerencia = {
            'cliente': cliente,
            'nombre_cliente': perfil.get('cliente', {}).get('nombre_legal', 'N/A'),
            'sector': perfil.get('cliente', {}).get('sector', 'N/A'),
            'calculo': calculo,
            'recomendacion': recomendacion,
            'proximos_pasos': [
                f"1. Revisar recomendación de materialidad: ${calculo['materialidad_sugerida']:,.0f}",
                f"2. Confirmar materialidad final (rango: ${calculo['materialidad_minima']:,.0f} - ${calculo['materialidad_maxima']:,.0f})",
                f"3. Guardar materialidad elegida en base de datos",
                f"4. Calcular materialidad de desempeño: ${calculo['materialidad_desempeno']:,.0f}",
                f"5. Establecer error trivial: ${calculo['error_trivial']:,.0f}"
            ]
        }
        
        return sugerencia
        
    except Exception as e:
        print(f"❌ Error en sugerir_materialidad: {e}")
        return None


def guardar_sugerencia_materialidad(cliente: str, materialidad_elegida: Optional[float] = None) -> bool:
    """
    Guarda la materialidad elegida por el auditor.
    
    Args:
        cliente: Nombre del cliente
        materialidad_elegida: Materialidad confirmada por auditor (opcional)
        
    Returns:
        bool: Éxito de la guardada
    """
    try:
        sugerencia = sugerir_materialidad(cliente)
        
        if not sugerencia:
            print("❌ No se puede guardar: error al obtener sugerencia")
            return False
        
        calculo = sugerencia['calculo']
        
        # Si no proporciona materialidad elegida, usar la sugerida
        if materialidad_elegida is None:
            materialidad_elegida = calculo['materialidad_sugerida']
        
        # Validar que esté en rango
        if not (calculo['materialidad_minima'] <= materialidad_elegida <= calculo['materialidad_maxima']):
            print(f"⚠️  Advertencia: materialidad ${materialidad_elegida:,.0f} fuera del rango recomendado")
        
        # Preparar datos a guardar
        datos = {
            'cliente': cliente,
            'fecha': '2026-03-16',  # Fecha actual
            'materialidad_sugerida': calculo['materialidad_sugerida'],
            'materialidad_elegida': materialidad_elegida,
            'materialidad_desempeno': materialidad_elegida * 0.75,
            'error_trivial': materialidad_elegida * 0.05,
            'base_utilizada': calculo['base_utilizada'],
            'valor_base': calculo['valor_base'],
            'porcentaje_aplicado': round((materialidad_elegida / calculo['valor_base']) * 100, 2),
            'origen_regla': calculo['origen_regla'],
            'notas': 'Materialidad establecida por auditor'
        }
        
        # Guardar en repositorio
        from infra.repositories.cliente_repository import guardar_materialidad
        
        exito = guardar_materialidad(cliente, datos)
        
        if exito:
            print(f"✅ Materialidad guardada: ${materialidad_elegida:,.0f}")
        
        return exito
        
    except Exception as e:
        print(f"❌ Error guardando materialidad: {e}")
        return False


def obtener_materialidad_guardada(cliente: str) -> Optional[Dict]:
    """
    Obtiene la materialidad previamente guardada para un cliente.
    
    Args:
        cliente: Nombre del cliente
        
    Returns:
        dict: Datos de materialidad guardada o None
    """
    try:
        
        # Intentar cargar materialidad desde repositorio
        # Nota: usamos cargar_perfil como demo, en producción usaríamos una función específica
        
        client_path = DATA_ROOT / "clientes" / cliente / "materialidad.yaml"
        
        if not client_path.exists():
            return None
        
        with open(client_path, 'r', encoding='utf-8') as f:
            datos = yaml.safe_load(f)
        
        return datos if datos else None
        
    except Exception as e:
        print(f"⚠️  Error cargando materialidad guardada: {e}")
        return None


def resumen_materialidad(cliente: str) -> Optional[Dict]:
    """
    Obtiene un resumen ejecutivo de materialidad.
    
    Útil para reportes y dashboards.
    
    Args:
        cliente: Nombre del cliente
        
    Returns:
        dict: Resumen con valores clave
    """
    try:
        sugerencia = sugerir_materialidad(cliente)
        guardada = obtener_materialidad_guardada(cliente)
        
        if not sugerencia:
            return None
        
        calculo = sugerencia['calculo']
        
        resumen = {
            'cliente': cliente,
            'nombre_cliente': sugerencia['nombre_cliente'],
            'materialidad_sugerida': calculo['materialidad_sugerida'],
            'materialidad_elegida': guardada['materialidad_elegida'] if guardada else None,
            'materialidad_desempeno': calculo['materialidad_desempeno'],
            'error_trivial': calculo['error_trivial'],
            'base': f"{calculo['porcentaje_maximo']}% de {calculo['base_utilizada']}",
            'estado': 'ESTABLECIDA' if guardada else 'PENDIENTE'
        }
        
        return resumen
        
    except Exception as e:
        print(f"❌ Error en resumen_materialidad: {e}")
        return None
