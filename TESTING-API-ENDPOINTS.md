# Testing API Endpoints: Carta de Control

**Ambiente:** Local (http://localhost:8000)  
**Autenticación:** Bearer token requerido en header `Authorization`

---

## 🔐 Obtener Token (Login)

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "echoe@company.com",
    "password": "your-password"
  }'
```

**Respuesta:**
```json
{
  "status": "success",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "user": {
      "id": "user-123",
      "email": "echoe@company.com",
      "rol": "JUNIOR"
    }
  }
}
```

---

## 📋 Endpoint 1: Carta de Control (Hallazgos Finalizados)

**URL:** `GET /api/reportes/papeles-trabajo/{cliente_id}/carta-control`

**Headers:**
```
Authorization: Bearer {token}
Content-Type: application/json
```

**Ejemplo con cliente_id = "cliente-123":**

```bash
curl -X GET http://localhost:8000/api/reportes/papeles-trabajo/cliente-123/carta-control \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

**Respuesta exitosa (200):**
```json
{
  "status": "success",
  "data": {
    "cliente_id": "cliente-123",
    "tipo_reporte": "CARTA_CONTROL",
    "total_hallazgos": 5,
    "hallazgos": [
      {
        "codigo_papel": "130.03",
        "nombre": "Conciliación cuentas por cobrar",
        "motivo": "Validar que el saldo total de CXC en libros coincide con la suma detallada de clientes",
        "aseveracion": "INTEGRIDAD",
        "observacion_final": "Encontrada diferencia de $2,500 en saldo CXC. Investigación identificó factura duplicada #4521 por $2,500.",
        "efecto_financiero": "CON_EFECTO",
        "impacto": "CXC debe reducirse por $2,500 en EE.FF.",
        "accion_recomendada": "Ajuste de asiento: DR Devoluciones -$2,500 CR CXC -$2,500",
        "revisado_por_socio": "jcarlos",
        "fecha_finalizacion": "2026-04-16T15:45:00"
      },
      {
        "codigo_papel": "130.04",
        "nombre": "Resumen de antigüedad CXC",
        "motivo": "Evaluar el riesgo de cobranza identificando saldos vencidos por período",
        "aseveracion": "INTEGRIDAD",
        "observacion_final": "Cliente A tiene saldo vencido de $50,000 (60+ días). Contacto con cliente confirma que será pagado próxima semana. Cobro posterior al cierre ($50,000 recibido en 2026-04-05).",
        "efecto_financiero": "SIN_EFECTO",
        "impacto": "Ninguno (se cobró en cierre correcto)",
        "accion_recomendada": "Documentado en archivo. No hay provisión requerida.",
        "revisado_por_socio": "jcarlos",
        "fecha_finalizacion": "2026-04-16T15:50:00"
      }
    ],
    "resumen": {
      "sin_efecto": 3,
      "con_efecto": 1,
      "ajuste_requerido": 1,
      "total": 5
    }
  }
}
```

**Qué observar:**
- ✅ `observacion_final`: Conclusión aprobada por Socio (SIN historial)
- ✅ `motivo`: Descripción enriquecida explicando POR QUÉ se audita
- ✅ `efecto_financiero`: Clasificación (SIN_EFECTO, CON_EFECTO, AJUSTE_REQUERIDO)
- ✅ `impacto` y `accion_recomendada`: Detalles de ajustes
- ❌ NO incluye: observaciones parciales de Junior/Senior, comentarios

---

## 📈 Endpoint 2: Hallazgos por Línea de Cuenta

**URL:** `GET /api/reportes/papeles-trabajo/{cliente_id}/hallazgos-por-ls`

```bash
curl -X GET http://localhost:8000/api/reportes/papeles-trabajo/cliente-123/hallazgos-por-ls \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

**Respuesta exitosa (200):**
```json
{
  "status": "success",
  "data": {
    "cliente_id": "cliente-123",
    "tipo_reporte": "HALLAZGOS_POR_LS",
    "lineas_con_hallazgos": ["110", "130", "324", "425"],
    "hallazgos_por_ls": {
      "110": {
        "total": 1,
        "sin_efecto": 0,
        "con_efecto": 1,
        "hallazgos": [
          {
            "codigo": "110.08",
            "nombre": "Valor Neto Realizable (Inventario)",
            "observacion": "Identificado inventario obsoleto (producto XYZ) sin movimiento en 12 meses...",
            "efecto": "AJUSTE_REQUERIDO"
          }
        ]
      },
      "130": {
        "total": 2,
        "sin_efecto": 1,
        "con_efecto": 1,
        "hallazgos": [
          {
            "codigo": "130.03",
            "nombre": "Conciliación cuentas por cobrar",
            "observacion": "Encontrada diferencia de $2,500 en saldo CXC...",
            "efecto": "CON_EFECTO"
          },
          {
            "codigo": "130.04",
            "nombre": "Resumen de antigüedad CXC",
            "observacion": "Cliente A tiene saldo vencido de $50,000...",
            "efecto": "SIN_EFECTO"
          }
        ]
      },
      "324": {
        "total": 1,
        "sin_efecto": 1,
        "con_efecto": 0,
        "hallazgos": [
          {
            "codigo": "324.04",
            "nombre": "Declaración de IVA",
            "observacion": "IVA a pagar calculado: $25,000...",
            "efecto": "SIN_EFECTO"
          }
        ]
      },
      "425": {
        "total": 1,
        "sin_efecto": 1,
        "con_efecto": 0,
        "hallazgos": [
          {
            "codigo": "425.03",
            "nombre": "Conciliación cuentas por pagar",
            "observacion": "Conciliación de CXP vs facturas por pagar: diferencia de $500...",
            "efecto": "SIN_EFECTO"
          }
        ]
      }
    }
  }
}
```

---

## 📊 Endpoint 3: Resumen Ejecutivo

**URL:** `GET /api/reportes/papeles-trabajo/{cliente_id}/resumen-ejecutivo`

```bash
curl -X GET http://localhost:8000/api/reportes/papeles-trabajo/cliente-123/resumen-ejecutivo \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

**Respuesta exitosa (200):**
```json
{
  "status": "success",
  "data": {
    "cliente_id": "cliente-123",
    "tipo_reporte": "RESUMEN_EJECUTIVO",
    "estadisticas": {
      "total_papeles_auditados": 78,
      "total_hallazgos": 5,
      "hallazgos_sin_efecto": 3,
      "hallazgos_con_efecto": 1,
      "ajustes_requeridos": 1,
      "porcentaje_hallazgos": 6.41
    },
    "hallazgos_significativos": [
      {
        "codigo": "130.03",
        "nombre": "Conciliación cuentas por cobrar",
        "impacto": "CXC debe reducirse por $2,500 en EE.FF.",
        "accion": "Ajuste de asiento: DR Devoluciones -$2,500 CR CXC -$2,500"
      },
      {
        "codigo": "110.08",
        "nombre": "Valor Neto Realizable (Inventario)",
        "impacto": "Provisión gasto por obsolescencia $7,000 / DR Gasto, CR Provisión",
        "accion": "Asiento: DR Gasto obsolescencia $7,000 CR Provisión inventario $7,000"
      }
    ],
    "conclusiones": [
      "Auditados todos los papeles requeridos",
      "Se identificaron 5 observaciones",
      "2 requieren ajuste en EE.FF."
    ]
  }
}
```

---

## ⚠️ Códigos de Error

### 401 - No Autenticado
```json
{
  "status": "error",
  "code": "UNAUTHORIZED",
  "message": "Token no válido o expirado"
}
```

### 403 - Sin Permiso
```json
{
  "status": "error",
  "code": "FORBIDDEN",
  "message": "No tienes permiso para acceder a este reporte"
}
```

### 404 - Cliente No Encontrado
```json
{
  "status": "error",
  "code": "NOT_FOUND",
  "message": "Cliente no existe"
}
```

### 500 - Error del Servidor
```json
{
  "status": "error",
  "code": "REPORTE_ERROR",
  "message": "Error generando carta de control: [detalles]"
}
```

---

## 🧪 Testing con Postman

1. **Crear colección:** "Papeles-Trabajo API"
2. **Crear variable global:** `token` = (pegar token del login)
3. **Crear variable global:** `cliente_id` = "cliente-123"
4. **Crear requests:**

### Request 1: Carta de Control
```
GET http://localhost:8000/api/reportes/papeles-trabajo/{{cliente_id}}/carta-control
Header: Authorization = Bearer {{token}}
```

### Request 2: Hallazgos por L/S
```
GET http://localhost:8000/api/reportes/papeles-trabajo/{{cliente_id}}/hallazgos-por-ls
Header: Authorization = Bearer {{token}}
```

### Request 3: Resumen Ejecutivo
```
GET http://localhost:8000/api/reportes/papeles-trabajo/{{cliente_id}}/resumen-ejecutivo
Header: Authorization = Bearer {{token}}
```

---

## 🔍 Validaciones a Verificar

### Respuesta CORRECTA de Carta de Control:
- ✅ `total_hallazgos > 0` si hay observaciones finalizadas
- ✅ `hallazgos[].observacion_final` ≠ null (conclusión final)
- ✅ `hallazgos[].motivo` contiene descripción enriquecida
- ✅ `hallazgos[].efecto_financiero` ∈ ["SIN_EFECTO", "CON_EFECTO", "AJUSTE_REQUERIDO"]
- ✅ `hallazgos[].revisado_por_socio` = usuario que finalizó
- ✅ `resumen.total` = suma de sin_efecto + con_efecto + ajuste_requerido
- ❌ `hallazgos[].junior_observation` no debe existir
- ❌ `hallazgos[].senior_comment` no debe existir
- ❌ `hallazgos[].history` no debe existir

### Respuesta CORRECTA de Resumen Ejecutivo:
- ✅ `estadisticas.total_papeles_auditados` ≤ 78 (máximo papeles en BD)
- ✅ `estadisticas.total_hallazgos` = # observaciones finalizadas
- ✅ `estadisticas.porcentaje_hallazgos` = (total_hallazgos / total_papeles) * 100
- ✅ `hallazgos_significativos` solo contiene efectos CON_EFECTO o AJUSTE_REQUERIDO
- ✅ `conclusiones` array con al menos 3 elementos

---

## 📱 Testing Frontend

### Navegar a Reportes:
```
URL: http://localhost:3000/reportes?cliente_id=cliente-123&cliente_nombre=Empresa%20XYZ
```

### Verificar:
1. Página carga sin errores
2. 3 tabs visibles: "Resumen Ejecutivo", "Hallazgos Detallados", "Por Línea de Cuenta"
3. Tab Resumen muestra:
   - Números grandes (estadísticas)
   - Hallazgos significativos con impacto
   - Conclusiones en lista
4. Tab Hallazgos muestra:
   - Cada hallazgo en card
   - Motivo visible
   - Observación final visible
   - Badges de efecto (verde/amarillo/rojo)
5. Tab Por L/S muestra:
   - Agrupar por línea de cuenta
   - Total y conteos por L/S

---

## 🚀 Flujo Completo de Testing

**Pre-requisito:** Tener al menos 1 observación finalizada en papeles-trabajo

1. Login como Junior
2. Crear observación
3. Login como Senior
4. Aprobar observación
5. Login como Socio
6. Finalizar observación + llenar campos
7. Logout
8. Login como cualquier usuario
9. GET /reportes/papeles-trabajo/cliente-123/carta-control
10. Verificar que retorna SOLO observacion_final, SIN historial
11. Navegar a /reportes?cliente_id=cliente-123
12. Verificar que CartaControl carga datos correctamente

---

**Estado:** LISTO PARA TESTING
