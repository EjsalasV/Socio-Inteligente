# Intelligent Audit Analyzer - Guía de Uso

**Status:** ✅ IMPLEMENTADO  
**Fecha:** 4 de junio 2026  
**Función:** Detección automática de anomalías en datos financieros usando IA

---

## 📋 ¿QUÉ ES?

El **Intelligent Audit Analyzer** es un módulo que:

1. **Recibe datos financieros** (balance de prueba, estado de resultados)
2. **Analiza automáticamente con Claude IA**
3. **Detecta anomalías y hallazgos** potenciales de auditoría
4. **Genera recomendaciones** basadas en normas NIIF/NIC

---

## 🚀 CÓMO USAR

### Acceso

```
http://localhost:3000/audit-analyzer/{clienteId}

Ejemplo:
http://localhost:3000/audit-analyzer/bustamante_fabara_ip_cl
```

### Paso 1: Ingresar Datos Financieros

**Sector:** Ej. "Comercio", "Manufactura"  
**Tamaño:** Pequeña, Mediana, Grande  
**Marco referencial:** NIIF Completas o NIIF PYMES

### Paso 2: Balance de Prueba (JSON)

Ingresa en formato JSON:

```json
{
  "140 - Activos Intangibles": 150000,
  "170 - Propiedad Planta Equipo": 500000,
  "130 - Cuentas por Cobrar": 250000,
  "210 - Cuentas por Pagar": 100000,
  "400 - Ingresos por Ventas": 1000000,
  "410 - Gastos de Operación": 600000
}
```

**Formato:**
- Clave: "NNN - Nombre de Cuenta"
- Valor: Monto numérico

### Paso 3: Estado de Resultados (Opcional)

```json
{
  "Ingresos por ventas": 1000000,
  "Costo de ventas": 400000,
  "Gastos de operación": 200000,
  "Ingresos netos": 400000
}
```

### Paso 4: Analizar

Click en **"▶️ Analizar Datos"**

El sistema:
1. Enviará datos a Claude IA
2. Analizará inconsistencias
3. Generará hallazgos automáticos
4. Mostrará resultados en ~30 segundos

---

## 📊 QUÉ DETECTA

El analizador busca automáticamente:

### Anomalías Financieras
- ✅ Activos sin depreciación/amortización
- ✅ Cuentas por cobrar antiguas (posibles incobrables)
- ✅ Ratios anormales para el sector
- ✅ Ingresos/gastos categorizados incorrectamente
- ✅ Provisiones faltantes

### Inconsistencias de Normas
- ✅ Incumplimientos de NIIF/NIC
- ✅ Errores de clasificación contable
- ✅ Falta de revelaciones requeridas
- ✅ Inconsistencias de períodos anteriores

### Riesgos de Fraude
- ✅ Patrones sospechosos
- ✅ Transacciones inusuales
- ✅ Irregularidades en documentación

---

## 📌 RESULTADO: HALLAZGOS

Cada hallazgo incluye:

### 1. Descripción
Qué es lo que se detectó exactamente

### 2. Nivel de Riesgo
- **CRÍTICO:** Requiere atención inmediata
- **IMPORTANTE:** Debe revisarse en auditoría
- **MENOR:** Observación sin riesgo material

### 3. Norma Aplicable
Ej: NIC 38, NIIF 9, etc.

### 4. Riesgo de Auditoría
Por qué es relevante para la auditoría

### 5. Procedimientos de Auditoría
Pasos específicos para auditar:
1. Paso 1
2. Paso 2
3. Etc.

### 6. Evidencia a Buscar
Documentos/datos a revisar:
- Certificados
- Facturas
- Estados de cuenta
- Etc.

### 7. Estimación de Horas
Cuánto tiempo toma auditar este hallazgo

---

## 📈 EJEMPLO PRÁCTICO

### Datos Ingresados

**Cliente:** Bustamante Fábara IP  
**Sector:** Comercio  
**Tamaño:** Mediana

**Balance:**
```json
{
  "140 - Activos Intangibles": 150000,
  "400 - Ingresos": 1000000,
  "410 - Gastos": 600000
}
```

### Hallazgos Detectados

**CRÍTICO - NIC 38**
- **Descripción:** Marca de calidad sin amortización
- **Riesgo:** Incumplimiento de NIC 38
- **Auditoría:** 
  1. Verificar vida útil asignada
  2. Calcular amortización correcta
  3. Registrar ajuste propuesto
- **Evidencia:** Documentos de registro, pólizas contables

---

## 🔍 CASO DE USO REAL

### Situación
Auditas a Bustamante Fábara IP. Ves una "Marca de Calidad" de $150K sin movimiento en gastos.

### Sin SocioAI
- ❌ Tienes que identificar manualmente
- ❌ Consultar normas
- ❌ Pensar qué revisar
- ⏱️ 1-2 horas

### Con SocioAI
- ✅ Subes datos
- ✅ Sistema detecta automáticamente
- ✅ Tienes lista de hallazgos + procedimientos
- ⏱️ 10 minutos

---

## 💬 OPCIÓN 3: AI AUDITOR ASSISTANT (Próximo)

Complemento al Analizador:

```
AUDITOR: "¿Cómo auditar una marca sin amortización?"

SISTEMA:
"Debes verificar NIC 38:
1. ¿Tiene vida útil definida?
2. ¿Por qué no se amortiza?
3. ¿Es revaluación?
4. Revisa esto... [evidencia]"
```

Integrado en el **Socio-Chat** ya existente.

---

## 🎯 CASOS DE HALLAZGOS AUTOMÁTICOS

### H001: Activo Intangible sin Amortización
```
Nivel: CRÍTICO
Norma: NIC 38
Procedimientos:
1. Verificar documentación de compra
2. Determinar vida útil (NIIF vs local)
3. Calcular amortización desde fecha compra
4. Registrar ajuste
```

### H002: Cartera Vencida
```
Nivel: IMPORTANTE
Norma: NIIF 9
Procedimientos:
1. Obtener antigüedad de deuda
2. Evaluar recaudabilidad
3. Calcular provisión
4. Validar con cliente
```

### H003: Ratio de Endeudamiento Anormal
```
Nivel: IMPORTANTE
Norma: NIIF 1 (Presentación)
Procedimientos:
1. Calcular ratio para sector
2. Comparar con estándares
3. Investigar cambios vs período anterior
4. Validar causas
```

---

## 🔄 FLUJO COMPLETO

```
AUDITOR entra a http://localhost:3000/audit-analyzer/bustamante
    ↓
Carga balance + estado de resultados (JSON)
    ↓
Click "Analizar"
    ↓
SocioAI enva a Claude IA
    ↓
Claude analiza datos
    ↓
Retorna hallazgos detectados
    ↓
AUDITOR ve lista de hallazgos
    ↓
Click en "Marca sin amortización"
    ↓
Ve detalles + procedimientos
    ↓
Click "Guardar como Hallazgo"
    ↓
Se guarda en módulo de hallazgos
    ↓
Continúa auditoría con datos reales
```

---

## ⚙️ CÓMO FUNCIONA INTERNAMENTE

1. **Frontend recibe datos JSON**
2. **POST /api/audit-analysis/{cliente_id}/analyze**
3. **Backend procesa y envía a Claude IA**
4. **Claude analiza y detecta anomalías**
5. **Backend retorna hallazgos en JSON**
6. **Frontend muestra resultados**

---

## 🚨 LIMITACIONES ACTUALES

- ✅ Detecta con IA
- ⏳ Almacenamiento de hallazgos (próximo)
- ⏳ Integración completa con módulo de hallazgos (próximo)
- ⏳ Exportación a PDF (próximo)

---

## 📚 PRÓXIMAS MEJORAS

### Opción 2: Smart Risk Engine
- Integrar análisis automático en dashboard
- Mostrar alertas en tiempo real

### Opción 3: AI Auditor Chat
- Chat especializado para cada hallazgo
- Recomendaciones paso a paso

---

## ✅ CHECKLIST

- [x] Servicio de análisis (intelligent_analyzer_service.py)
- [x] Endpoint backend (/api/audit-analysis)
- [x] Frontend página (/audit-analyzer)
- [x] Integración con Claude IA
- [x] Detección de anomalías
- [ ] Almacenamiento de hallazgos
- [ ] Chat especializado (Opción 3)
- [ ] Integración Risk Engine (Opción 2)

---

**¿Listo para probar?**

Ve a: http://localhost:3000/audit-analyzer/bustamante_fabara_ip_cl
