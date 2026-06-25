# 📊 SocioAI Analytics
## Business Plan - Versión Final

**Fecha:** Junio 2026  
**Estado:** MVP Validation Ready  
**Confidencial**

---

## 📋 RESUMEN EJECUTIVO

**SocioAI Analytics** es una plataforma web para firmas medianas de auditoría. Ayuda a realizar el análisis preliminar de balanzas contables mediante reglas determinísticas e IA, recupera el histó­rico autorizado del cliente y propone procedimientos revisables. El auditor conserva siempre la decisión profesional final.

Durante los primeros cuatro meses validaremos el producto con tres a cinco firmas piloto en Ecuador. Mediremos reducción de tiempo, calidad de alertas y disposición de pago antes de escalar.

El MVP requiere aproximadamente $4,000 y puede financiarse mediante bootstrap. Una inversión posterior solo se evaluará si los pilotos demuestran demanda y retorno económico.

### El Problema
Firmas medianas gastan 8+ horas en análisis inicial de cada cliente. Pierden contexto cuando cambian auditores. Retrabajan documentación constantemente. Los auditores junior no aprenden bajo mentoría real.

### Financiero (Escenario Base - Año 2)
- **Clientes:** 30 firmas medianas
- **Ingresos:** $79,500
- **Costos:** $34,713
- **Ganancia neta:** $44,787 (56% margen)
- **Capital inicial MVP:** $4,000 (bootstrap posible)
- **Capital futuro (condicional):** $15,000 (solo si métricas justifican extensiones)

---

## 🔍 EL PROBLEMA: TRES DOLORES CONCRETOS

### Dolor 1: Análisis Manual + Inconsistencia
**El síntoma:** Cada auditor analiza TB de forma distinta. Un senior ve patrones que un junior pierde. No existe forma de standarizar.

**El costo:** 
- 8 horas por cliente en análisis inicial
- 50% de análisis requieren retrabajo por calidad inconsistente
- Hallazgos no detectados = riesgo profesional

**El contexto:**
He trabajado como auditor. He visto a colegas gastar una semana en Excel buscando saldos negativos o variaciones inusuales. Luego el manager dice "le falta esto" y vuelven a empezar.

### Dolor 2: Pérdida de Contexto
**El síntoma:** Cada auditoría es "desde cero". No se recuerda que en 2024 encontramos un problema similar. Los patrones no se conectan.

**El costo:**
- Análisis menos profundo (sin benchmark histórico)
- Riesgos repetidos año a año
- Conocimiento institucional se pierde cuando se va un senior

### Dolor 3: Mentoría Inexistente
**El síntoma:** Junior usa ChatGPT genérico para preguntas de auditoría. Recibe respuestas vagas. No aprende realmente. Confía en IA en lugar de su criterio.

**El costo:**
- Juniors no desarrollan destreza auditoria
- Ciclos largos para que un junior sea competente
- Firma queda dependiente de seniors

---

## 💡 LA SOLUCIÓN: SocioAI MVP

### Qué Hace

**Aplicación Web que:**

1. **Carga TB/Mayores** en Excel o formulario simple
2. **Analiza automáticamente** usando reglas determinísticas + IA
   - Detecta: saldos anómalos, variaciones anormales, cuentas inusuales
   - Explica: por qué es riesgo, qué norma aplica, qué procedimiento hacer
3. **Consulta histórico** del cliente
   - "¿Encontramos algo similar el año pasado?"
   - "¿Esta cuenta siempre tuvo este saldo?"
4. **Requiere validación humana obligatoria**
   - Auditor marca: ✅ Correcto / ❌ Falso positivo / ⏳ Revisar después
   - Sistema no permite exportar sin validación
5. **Exporta a Excel/Word** para incorporar en papeles de trabajo

### Qué NO Hace (Fuera del MVP)

- ❌ Analizar transacciones individuales (megadatos)
- ❌ Generar reportes finales automáticos
- ❌ Reemplazar validación profesional
- ❌ Integrarse con sistemas ERP
- ❌ Word Add-in avanzado con chat
- ❌ Modelo IA propio (usamos DeepSeek)

### Por Qué Web-First

```
Arquitectura:

┌─────────────────────────────────┐
│   AUDITOR (Navegador Web)       │
│   Chrome, Safari, Firefox       │
│   ✅ Funciona 100% en web       │
└─────────────┬───────────────────┘
              │
    ┌─────────▼──────────┐
    │  SocioAI Backend    │
    │  FastAPI + IA      │
    └────────────────────┘

Opcional: Excel Add-in (mejoría UX, no crítico)
├─ Si IT bloquea: auditor usa web
└─ Funcionalidad principal permanece disponible mediante navegador
```

---

## 👁️ CASO DE USO: UN DÍA EN AUDITORÍA

### Sin SocioAI
```
08:00 AM | Auditor abre Excel con TB (183 cuentas)
         | Lee manualmente: 2 horas
         | Busca patrones: 1.5 horas
         | 
10:30 AM | Consulta ChatGPT: "¿Qué es NIC 18?"
         | Respuesta genérica, pierde tiempo: 30 min
         |
11:00 AM | Pregunta a senior: 30 min
         |
11:30 AM | Empieza a escribir en Word: 1.5 horas
         |
13:00 PM | Manager revisa, pide cambios: 45 min
         |
13:45 PM | TOTAL: 5 horas 45 minutos = $862.50 costo

PROBLEMA: Incompleto, junior no aprendió nada
```

### Con SocioAI
```
08:00 AM | Auditor sube Excel a SocioAI
         | Click: "Analizar"
         | ESPERA: 15 segundos
         |
08:01 AM | VE EN PANEL:
         | ✅ 4 hallazgos detectados
         | ├─ H001: Saldo acreedor inusual en cuentas por cobrar
         | ├─ H002: Variación significativa vs 2024
         | ├─ H003: Depreciación acumulada no ha aumentado
         | └─ Procedimientos sugeridos + norma aplicable
         |
08:15 AM | Lee y entiende (junior aprende): 10 min
         | Chat: "¿Por qué esto es riesgo?" 
         | SocioAI: explicación con fundamento
         |
08:25 AM | Exporta análisis a Word
         | Realiza revisión final manualmente
         | Documento listo: 15 min
         |
08:40 AM | Manager revisa dashboard
         | Ve: precisión 87%, contexto 2024, hallazgos
         | Aprueba: 5 min
         |
08:45 AM | TOTAL: 45 minutos = $112.50 costo

BENEFICIO: 5x más rápido, junior aprendió, completo
```

---

## 🏆 ANÁLISIS COMPETITIVO HONESTO

| Competidor | Modelo | Target | Fortaleza | Debilidad |
|------------|--------|--------|-----------|-----------|
| **Caseware AiDA** | Cotización comercial | Big 4 + firmas grandes | Integración ecosistema Caseware | Complejidad/costo para medianas |
| **DataSnipper** | Cotización comercial | Automatización Excel/auditoría | Sampling y validación robusto | Enfoque diferente (Excel sampling) |
| **MindBridge** | Cotización comercial | Analítica de riesgos/supervisión | Capacidades IA avanzadas | Enfoque enterprise, no LATAM |
| **ChatGPT genérico** | $20/mes | Cualquiera | Accesible | Sin contexto auditoria, no auditado |
| **SocioAI Analytics** | $100-$300/mes | Medianas LATAM especialistas NIIF | Accesible, local, NIIF-especializado | MVP inicial, sin integraciones complejas |

### Nuestra Ventaja DEFENDIBLE HOY
- **Accesibilidad de precio** ($100-$300/mes vs cotización comercial de competidores)
- **Soporte local** en español, con auditor que entiende el contexto NIIF-Latinoamérica
- **Especializado NIIF** Latinoamérica (no genérico global)
- **Implementación ágil** en 2-3 semanas vs ciclos más largos de plataformas enterprise
- **MVP funcional ahora** mientras competencia tarda más en iterar

### Nuestra Ventaja FUTURA (Condicional)
- Fine-tuned model si métricas lo justifican (no es requisito)
- Modelo propio si tokens resultan caros en escala (decisión data-driven)

---

## ✅ VALIDACIÓN ACTUAL

### Evidencia Existente
- Experiencia profesional de auditor (identificó el problema real)
- Prototipo funcionando con DeepSeek
- Feedback positivo de colegas auditores

### Plan de Validación Inicial (Meses 1-2)
```
Meta: 10 entrevistas estructuradas
├─ Pregunta: "¿Cuál es tu mayor frustración en análisis inicial?"
├─ Objetivo: validar problema existe
└─ Resultado: ¿Sí/No resuena el problema?

Meta: 3-5 firmas piloto activas
├─ Procesar 20-30 balanzas reales
├─ Medir: tiempo sin herramienta vs con herramienta
├─ Preguntar: "¿Pagarías por esto?"
└─ Resultado: evidencia de ahorro + disposición a pagar

Hitos medibles (no predicciones):
├─ Tiempo promedio análisis sin herramienta: X minutos
├─ Tiempo promedio análisis con herramienta: Y minutos
├─ Ahorro por análisis: X-Y (medible)
├─ Confianza en hallazgos: 1-10 Likert
└─ NPS: ¿Recomendarías?
```

---

## 💰 MODELO DE INGRESOS

### Estructura Simple (Lo que ve el cliente)

```
PLAN PILOTO
├─ $100/mes
├─ 1 firma
├─ ~20 análisis/mes
├─ Soporte directo (email/chat)
└─ Válido 3 meses

PLAN PROFESIONAL
├─ $300/mes
├─ 2-3 firmas
├─ ~100 análisis/mes
├─ Dashboard avanzado
├─ Histórico de 3 años
└─ Renovación anual

PLAN ENTERPRISE
├─ Custom (contactar)
├─ Múltiples firmas
├─ SLA 99.9%
├─ Soporte dedicado
└─ Integraciones custom
```

### Estructura Interna (Cómo monitoreamos márgenes)

Internamente monitoreamos consumo de tokens para entender costos reales y ajustar arquitectura según sea necesario. Cliente nunca ve esta complejidad.

---

## 🚀 GO-TO-MARKET: VALIDACIÓN ANTES DE ESCALA

### Fase 1: Pilotos Locales (Meses 1-4)
```
Target: 3-5 firmas medianas en Ecuador
├─ Enfoque: Soporte presencial + hands-on
├─ Objetivo: Medición real de ROI
├─ Conversión esperada: ¿50%? ¿0%? Validaremos
└─ Timeline: 12 semanas
```

### Fase 2: Expansión Condicionada (Meses 5-12)
```
SOLO SI métricas de pilotos son positivas:
├─ Métricas mínimas para escalar:
│  ├─ Ahorro tiempo: >50% comprobado
│  ├─ NPS: >40 (recomendable)
│  └─ Disposición a pagar: ≥70% de pilotos
│
├─ Si se cumplen: expande a 10-15 firmas
├─ Si NO se cumplen: pivota el producto
└─ NO escalamos "por fe"
```

### Fase 3: Regional (Año 2+)
```
Basado en results de fase 2
├─ Colombia, Perú, Bolivia (NIIF)
├─ Versión USGAP (si demanda existe)
└─ Expansión consciente
```

---

## 🔒 SEGURIDAD & PRIVACIDAD (Desde MVP)

### MVP Incluye (Desde Día 1)
```
Mínimo sólido:
├─ Cifrado en tránsito (HTTPS/TLS)
├─ Cifrado en reposo mediante servicios administrados del proveedor cloud
├─ Separación de datos por firma (database isolation)
├─ Control de acceso por roles (auditor, admin, viewer)
├─ Autenticación multi-factor (2FA) con opciones estándar
├─ Audit logs (quién accedió qué, cuándo)
├─ Política de retención (datos se borran a X años)
├─ Contratos de privacidad (DPA con cliente)
├─ Minimización/seudonimización de datos sensibles antes de IA
└─ Prohibición explícita: datos reales sin autorización escrita
```

### Futuro (Año 2+)
```
Cuando escale y sea rentable:
├─ SOC 2 Type II
├─ GDPR compliance
└─ Backup geográfico redundante
```

### Normativa Local (Ecuador)
Consultaremos con asesor legal especializado en Superintendencia de Protección de Datos Personales. No es "para después"; es parte del MVP.

---

## 📈 ROADMAP REALISTA

### MVP (Semanas 1-12)
```
✅ Aplicación web simple
✅ Upload de TB/Mayores (Excel o formulario)
✅ Análisis básico (reglas determinísticas + IA)
✅ Hallazgos con explicación auditada
✅ Validación obligatoria (checkbox)
✅ Memoria histórica (cliente anterior)
✅ Export a Excel/Word simple
✅ Seguridad mínima (cifrado, separación datos)
✅ Soporte email

FUERA del MVP:
❌ Word Add-in con chat avanzado
❌ Fine-tuning (usamos DeepSeek vanilla)
❌ Modelo IA propio
❌ API pública
❌ Multi-idioma
❌ Certificaciones
❌ Benchmarking sectorial
```

### V1 (Meses 5-8, Condicional)
```
SOLO si métricas de MVP son positivas:
├─ Dashboard avanzado (ver histórico, tendencias)
├─ Comparación año a año (¿qué cambió?)
├─ Chat normativo mejorado
├─ Integración básica Caseware (si cliente lo pide)
└─ Soporte por chat
```

### V2 (Meses 9-12, Condicional)
```
SOLO si ingresos permiten:
├─ Fine-tuning DeepSeek (si precisión < 95%)
├─ Excel Add-in (si pilotos lo validan)
├─ Mayores detallados
└─ Análisis de flujos de caja
```

### Modelo Propio (Año 2+, Condicional)
```
SOLO si TODAS se cumplen:
├─ DeepSeek 10x el precio, O
├─ Fine-tuning no alcanza 95% precisión, O
├─ Requisito regulatorio lo hace necesario
│
Y SOLO si:
├─ 3+ clientes pagando activamente
├─ LTV (customer lifetime value) > 3x CAC
└─ ROI de modelo propio es >3x
```

---

## 💹 PROYECCIONES FINANCIERAS

### Escenario CONSERVADOR (Año 2)

**Supuestos:**
- Ramp-up conservador: 5 clientes promedio (meses 1-3), 13 clientes promedio (meses 4-6), 23 clientes promedio (meses 7-12)
- Precio promedio por período: $250 (meses 1-3), $350 (meses 4-6), $450 (meses 7-12)
- Año finaliza con ~30 clientes activos en estado estable

**Ingresos por período:**

| Período | Clientes Promedio | Precio Promedio | Meses | Total |
|---------|------------------|------------------|-------|-------|
| Meses 1-3 | 5 | $250 | 3 | $3,750 |
| Meses 4-6 | 13 | $350 | 3 | $13,650 |
| Meses 7-12 | 23 | $450 | 6 | $62,100 |
| **Total Año 2** | **30 final** | **$350 promedio** | **12** | **$79,500** |

**Costos operativos:**

| Concepto | Mensual | Anual |
|----------|---------|-------|
| IA (DeepSeek) | $30 | $360 |
| Infrastructure (AWS) | $400 | $4,800 |
| Salarios (tú + ops) | $1,500 | $18,000 |
| Legal/Compliance | $200 | $2,400 |
| Marketing básico | $500 | $6,000 |
| Contingency (10%) | $263 | $3,153 |
| **TOTAL** | **$2,893** | **$34,713** |

**Ganancia Neta:**
- Ingresos: $79,500
- Costos: $34,713
- **Ganancia: $44,787**
- **Margen: 56%**

### Escenario BASE (Año 2)

| Métrica | Valor |
|---------|-------|
| Clientes fin año | 50 |
| Ingreso promedio | $400 |
| Ingresos totales | $120,000 |
| Costos operativos | $45,000 |
| Ganancia neta | $75,000 |
| Margen | 62% |

### Escenario OPTIMISTA (Año 2)

| Métrica | Valor |
|---------|-------|
| Clientes fin año | 75 |
| Ingreso promedio | $450 |
| Ingresos totales | $162,000 |
| Costos operativos | $55,000 |
| Ganancia neta | $107,000 |
| Margen | 66% |

### Año 3 (Base Case: 30 clientes Año 2 finales)

| Periodo | Clientes | Ingresos | Costos | Ganancia | Margen |
|---------|----------|----------|--------|----------|--------|
| Año 1 (beta) | 0 | $0 | $4,000 | -$4,000 | - |
| Año 2 | 30 | $79,500 | $34,713 | $44,787 | 56% |
| Año 3 | 80 | $288,000 | $68,000 | $220,000 | 76% |

---

## 💰 SOLICITUD DE INVERSIÓN

### MVP: $3,000 - $5,000 (Bootstrap-friendly)

**Opción A: Bootstrap Puro (Tu inversión)**
```
Costo: $4,000
├─ Desarrollo backend + web UI: $2,000
├─ AWS infrastructure (3 meses): $1,000
├─ Legal (privacidad básica): $500
└─ Remanente: $500

Timeline: 4-5 meses
Ventaja: 100% del equity es tuya
```

**Opción B: Angel Investor Pequeño (Recomendado)**
```
Tu inversión: $2,000
Angel inversión: $5,000
Total: $7,000

Estructura:
├─ Tú: $2,000 (90% ownership)
├─ Angel: $5,000 (10% ownership)
└─ Hito: Primera firma pagando = ambos felices

Timeline: 4 meses
Ventaja: Capital para marketing inicial + buffer
```

### Futuro: $15,000 - $30,000 (Condicional, Año 2)

**SOLO si se cumplen:**
```
✅ 3+ clientes pagando activamente
✅ Ahorro tiempo comprobado >50%
✅ LTV/CAC ratio >2.0
✅ Fine-tuning o modelo propio es bottleneck real

Uso:
├─ Fine-tuning + infrastructure para modelo
├─ Contratación part-time (soporte)
├─ Expansión regional (viajes + marketing)
└─ Buffer operativo

Financiamiento: Mezcla de revenue + nuevo capital
```

---

## 📌 TIMELINE CRÍTICO

```
Meses 1-2: Validación
├─ 10 entrevistas
├─ 3-5 firmas piloto
└─ Medición real

Meses 3-4: MVP Launch
├─ Herramienta lista
├─ Pilotos activos
└─ Primeras métricas

Mes 5-6: Go/No-Go Decision
├─ ¿Métricas son positivas?
├─ SÍ → Escalamos a 15 firmas
└─ NO → Pivotamos o pausamos

Meses 7-12: Growth Phase
├─ 20-30 firmas en sistema
├─ Documentación de ROI
└─ Decision sobre V1 features
```

---

## 🎯 MÉTRICAS DE ÉXITO (Lo que realmente medimos)

```
Mes 1-4 (MVP):
├─ Tiempo sin herramienta vs con: ¿>50% ahorro?
├─ Confianza auditor en hallazgos: 1-10 Likert
├─ Precisión (hallazgos validados): ¿>80%?
├─ "¿Pagarías por esto?": ¿>70% dicen sí?
└─ NPS: ¿>40?

Mes 5+ (Growth):
├─ Churn rate: <10% mensual
├─ CAC (costo adquisición): <$1,000
├─ LTV (valor lifetime): >$1,200
├─ Net retention: >100% (expansion revenue)
└─ Conversión piloto → pago: ¿>60%?
```

---

## 🌟 POR QUÉ AHORA, POR QUÉ NOSOTROS

**El Momento (Market):**
- NIIF genera demanda por auditoría de calidad
- Firmas medianas no compran BigTech caras
- LATAM carece de herramientas especializadas
- DeepSeek permite IA a costo accesible

**El Equipo (People):**
- Auditor con problema real, no teórico
- Entiende el flujo (papeles, normativa, dolor)
- Builder pragmático (MVP no fantasía)
- Dispuesto a validar vs. asumir

**La Solución (Product):**
- No es "ChatGPT con corbata"
- Es asistencia auditoria concreta (reducir tiempo 50%+)
- Memoria histórica (valor que no existe)
- Validación humana obligatoria (responsabilidad profesional)

---

## 📞 CONTACTO

**Fundador:** [Tu nombre]  
**Email:** [Tu email]  
**LinkedIn:** [Tu perfil]  
**Demo:** Disponible con NDA

---

**SocioAI Analytics** — Análisis que aprende. Auditoría que confía.

*Última actualización: Junio 2026*  
*Versión: Final - Investment Ready*
