# 📋 Implementación: Papeles de Trabajo v2 con Observaciones

**Fecha:** 16-04-2026  
**Estado:** Generado - Listo para Implementar

---

## 📊 Lo que se ha generado

### 1. **Clasificación de Papeles (78 Total)**
- ✅ Script Python que extrae papeles de `Pruebas modelo/`
- ✅ Clasificación automática por:
  - **Aseveración NIA:** EXISTENCIA, INTEGRIDAD, VALORACIÓN, DERECHOS, PRESENTACIÓN
  - **Importancia:** CRÍTICO, ALTO, MEDIO, BAJO
  - **Obligatorio:** SÍ, NO, CONDICIONAL
- ✅ JSON generado: `data/papeles_clasificados.json`

### 2. **Líneas de Cuenta (LS) Encontradas**
```
1 (PPE), 5 (Propiedades Inv), 10 (Intangibles), 11 (Derecho Uso),
20 (Inversiones), 110 (Inventarios), 130 (CXC), 136 (Impuestos Activo),
140 (Efectivo), 200 (Patrimonio), 324 (Impuestos Pasivo),
325 (Impuesto Diferido), 330 (Obligaciones Financieras),
415 (Beneficios Empleados), 425 (CXP), 1500 (Ingresos), 1600 (Gastos)
```

### 3. **Base de Datos - Migraciones Creadas**

#### `backend/migrations/002_create_papeles_templates.sql`
```sql
workpapers_templates
├── id, codigo (130.03), numero (03), ls (130)
├── nombre, aseveracion, importancia, obligatorio
├── descripcion (POR QUÉ se realiza)
└── archivo_original
```

#### `backend/migrations/003_create_papeles_observations.sql`
```sql
workpapers_observations
├── file_id (FK a workpapers_files)
├── codigo_papel (130.03)
├── Junior: observation, by, at, status
├── Senior: review, comment, by, at
├── Socio: review, comment, by, at
├── status (PENDIENTE, APROBADO, RECHAZADO, NO_APLICA, FINALIZADO)
└── historial completo (quién, cuándo, qué)

workpapers_observation_history
├── observation_id (FK)
├── rol (junior, senior, socio)
├── accion (escribio, aprobó, rechazó, comentó)
├── contenido_anterior, contenido_nuevo
└── usuario, changed_at
```

### 4. **Modelos SQLAlchemy**
- ✅ `backend/models/workpapers_template.py`
- ✅ `backend/models/workpapers_observation.py`

### 5. **Nuevas Rutas Backend**
Archivo: `backend/routes/papeles_templates.py`

```
GET  /api/papeles-trabajo/{cliente_id}/templates/ls/{ls}
     └─ Obtiene papeles de una L/S, ordenados por importancia

GET  /api/papeles-trabajo/templates
     └─ Obtiene todos los papeles (para dropdown)

POST /api/papeles-trabajo/{cliente_id}/observations/{file_id}/{codigo_papel}
     └─ Crea/actualiza observación (Junior escribe, Senior/Socio revisan)

GET  /api/papeles-trabajo/{cliente_id}/observations/{file_id}/{codigo_papel}
     └─ Obtiene observación + historial completo

POST /api/papeles-trabajo/{cliente_id}/observations/{file_id}/{codigo_papel}/approve
     └─ Senior/Socio aprueban, rechazan o comentan
```

### 6. **Script para Cargar Datos**
Archivo: `backend/scripts/seed_workpapers_templates.py`

```bash
# Carga los 78 papeles desde JSON a la BD
python backend/scripts/seed_workpapers_templates.py
```

---

## 🚀 Pasos para Implementar

### PASO 1: Ejecutar Migraciones

```bash
# 1. Crear tabla de templates
mysql -u root -p < backend/migrations/002_create_papeles_templates.sql

# 2. Crear tabla de observaciones
mysql -u root -p < backend/migrations/003_create_papeles_observations.sql

# (O usando tu ORM favorito)
```

### PASO 2: Cargar Datos de Papeles

```bash
cd "C:\Users\echoe\Desktop\Nuevo Socio AI"

# Ejecutar script de carga
python backend/scripts/seed_workpapers_templates.py

# Output esperado:
# Encontrados 78 papeles en data/papeles_clasificados.json
# Papeles previos eliminados
# Exito! 78 papeles insertados
```

### PASO 3: Registrar Nuevas Rutas en Backend

En `backend/main.py`, agregar:

```python
from backend.routes.papeles_templates import router as papeles_templates_router

# ... después de otras rutas
app.include_router(papeles_templates_router)
```

### PASO 4: Actualizar Frontend - Componentes Nuevos

Crear nuevo componente en `frontend/components/papeles-trabajo/PapelesObservaciones.tsx`:

```tsx
"use client";

import React, { useState } from "react";
import { Button } from "@/components/ui/button";

interface Observation {
  id: number;
  codigo_papel: string;
  junior_observation?: string;
  junior_by?: string;
  junior_at?: string;
  senior_review?: string;
  senior_comment?: string;
  senior_by?: string;
  senior_at?: string;
  socio_review?: string;
  socio_comment?: string;
  socio_by?: string;
  socio_at?: string;
  status: string;
}

interface PapelesObservacionesProps {
  fileId: number;
  clienteId: string;
  codigoPapel: string;
  rol: "junior" | "semi" | "senior" | "socio";
}

export function PapelesObservaciones({
  fileId,
  clienteId,
  codigoPapel,
  rol,
}: PapelesObservacionesProps) {
  const [observation, setObservation] = useState<Observation | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [observationText, setObservationText] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  // Cargar observación
  const loadObservation = async () => {
    try {
      const response = await fetch(
        `/api/papeles-trabajo/${clienteId}/observations/${fileId}/${codigoPapel}`
      );
      if (response.ok) {
        const data = await response.json();
        setObservation(data.data.observation);
      }
    } catch (error) {
      console.error("Error cargando observación:", error);
    }
  };

  // Guardar observación
  const saveObservation = async () => {
    try {
      setIsLoading(true);
      const response = await fetch(
        `/api/papeles-trabajo/${clienteId}/observations/${fileId}/${codigoPapel}`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ observation_text: observationText }),
        }
      );

      if (response.ok) {
        await loadObservation();
        setIsModalOpen(false);
        setObservationText("");
      }
    } catch (error) {
      console.error("Error guardando observación:", error);
    } finally {
      setIsLoading(false);
    }
  };

  React.useEffect(() => {
    loadObservation();
  }, [codigoPapel]);

  const canWrite = rol === "junior";
  const canReview = rol === "senior" || rol === "socio";

  return (
    <div className="border-t border-gray-200 pt-4 mt-4">
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-semibold text-gray-900">Observaciones</h3>
        {(canWrite || canReview) && (
          <Button
            onClick={() => setIsModalOpen(true)}
            className="text-sm bg-blue-600 hover:bg-blue-700 text-white"
          >
            + Agregar
          </Button>
        )}
      </div>

      {observation ? (
        <div className="space-y-3 bg-gray-50 p-4 rounded">
          {observation.junior_observation && (
            <div>
              <p className="text-xs font-semibold text-gray-600 uppercase">
                Junior ({observation.junior_by})
              </p>
              <p className="text-sm text-gray-800 mt-1">
                {observation.junior_observation}
              </p>
              <p className="text-xs text-gray-500 mt-1">{observation.junior_at}</p>
            </div>
          )}

          {observation.senior_review && (
            <div className="border-t border-gray-200 pt-3">
              <p className="text-xs font-semibold text-gray-600 uppercase">
                Senior Review: {observation.senior_review}
              </p>
              {observation.senior_comment && (
                <p className="text-sm text-gray-800 mt-1">
                  {observation.senior_comment}
                </p>
              )}
              <p className="text-xs text-gray-500 mt-1">
                {observation.senior_by} - {observation.senior_at}
              </p>
            </div>
          )}

          {observation.socio_review && (
            <div className="border-t border-gray-200 pt-3">
              <p className="text-xs font-semibold text-gray-600 uppercase">
                Socio: {observation.socio_review}
              </p>
              {observation.socio_comment && (
                <p className="text-sm text-gray-800 mt-1">
                  {observation.socio_comment}
                </p>
              )}
              <p className="text-xs text-gray-500 mt-1">
                {observation.socio_by} - {observation.socio_at}
              </p>
            </div>
          )}
        </div>
      ) : (
        <p className="text-gray-500 text-sm">Sin observaciones</p>
      )}

      {/* Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h2 className="text-lg font-bold mb-4">
              Agregar Observación - {codigoPapel}
            </h2>
            <textarea
              value={observationText}
              onChange={(e) => setObservationText(e.target.value)}
              placeholder="Describe lo que encontraste..."
              className="w-full border border-gray-300 rounded p-3 mb-4 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              rows={5}
            />
            <div className="flex justify-end gap-2">
              <Button
                onClick={() => setIsModalOpen(false)}
                className="bg-gray-300 hover:bg-gray-400 text-gray-800"
              >
                Cancelar
              </Button>
              <Button
                onClick={saveObservation}
                disabled={isLoading || !observationText.trim()}
                className="bg-blue-600 hover:bg-blue-700 text-white"
              >
                {isLoading ? "Guardando..." : "Guardar"}
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
```

### PASO 5: Actualizar Página Papeles-Trabajo

En `frontend/app/papeles-trabajo/[clienteId]/page.tsx`:

```tsx
// Agregar import
import { PapelesObservaciones } from "@/components/papeles-trabajo/PapelesObservaciones";

// En el componente, cuando muestres un papel:
<PapelesObservaciones
  fileId={selectedV2File?.id}
  clienteId={clienteId}
  codigoPapel="130.03"
  rol={role}
/>
```

### PASO 6: Mostrar Lista de Papeles por LS

En la UI, cuando el usuario selecciona un LS (dropdown):

```tsx
// Fetch papeles por LS
const response = await fetch(
  `/api/papeles-trabajo/${clienteId}/templates/ls/130`
);
const data = await response.json();

// Mostrar list
data.data.templates.map(t => (
  <div key={t.codigo}>
    <h3>{t.codigo} - {t.nombre}</h3>
    <p>Aseveración: {t.aseveracion}</p>
    <p>Importancia: {t.importancia}</p>
    <p>Descripción: {t.descripcion}</p>
    <button onClick={() => downloadPapel(t.codigo)}>
      Descargar
    </button>
    <button onClick={() => openObservations(t.codigo)}>
      + Observación
    </button>
  </div>
))
```

---

## 📝 Descripción POR QUÉ

Cada papel tiene descripción del **POR QUÉ** se realiza (para Junior). Ejemplos:

```
130.03: "Por qué se realiza conciliación de cuentas por cobrar en rol Junior"
130.07: "Por qué se realizan confirmaciones de saldos en rol Junior"
425.03: "Por qué se realiza conciliación de cuentas por pagar en rol Junior"
```

---

## 🔄 Flujo de Observaciones

```
1. JUNIOR escribe OBSERVACIÓN
   "Encontré duplicado factura #4521, diferencia $2,500"
   Status: PENDIENTE_SENIOR

2. SENIOR revisa
   - ✅ APROBADO: "Correcto, lo confirmo"
   - ❌ RECHAZADO: "No me cuadra, revisar"
   - 💬 PENDIENTE_ACLARACION: "¿Cuál es el impacto?"
   Status: PENDIENTE_SOCIO o RECHAZADO

3. SOCIO revisa TODO
   - ✅ FINALIZADO: "Sin efectos para EE.FF."
   - ❌ REVISAR: "Esto no se consideró"
   - 💬 NO_APLICA: "Para esta empresa no aplica"
   Status: FINALIZADO

Historial registra TODO:
├─ Junior escribió observación - 16-04-2026 10:30
├─ Senior aprobó - 16-04-2026 14:15
│  "Correcto, lo confirmo"
└─ Socio finalizó - 16-04-2026 15:45
   "Sin efectos para EE.FF."
```

---

## 📊 JSON Generado

**Ubicación:** `data/papeles_clasificados.json`

**Estructura:**
```json
{
  "total": 78,
  "lineas_de_cuenta": [1, 5, 10, ..., 1600],
  "papeles": [
    {
      "codigo": "130.03",
      "numero": "03",
      "ls": 130,
      "nombre": "Conciliación cuentas por cobrar",
      "aseveracion": "INTEGRIDAD",
      "importancia": "CRÍTICO",
      "obligatorio": "SÍ",
      "descripcion": "Por qué se realiza conciliación de cuentas por cobrar...",
      "archivo_original": "..."
    },
    ...
  ],
  "papeles_por_ls": {
    "130": [...],
    "140": [...],
    ...
  }
}
```

---

## ✅ Checklist de Implementación

- [ ] Ejecutar migraciones (002, 003)
- [ ] Ejecutar seed script
- [ ] Incluir nuevas rutas en main.py
- [ ] Crear componente PapelesObservaciones.tsx
- [ ] Actualizar página papeles-trabajo
- [ ] Agregar dropdown con LS
- [ ] Mostrar papeles clasificados por LS
- [ ] Test: Escibir observación como Junior
- [ ] Test: Revisar como Senior
- [ ] Test: Finalizar como Socio
- [ ] Verificar historial completo
- [ ] Verificar datos en reportes

---

## 🎯 Resultado Final

```
PAPELES-TRABAJO v2 COMPLETO:
✅ Descargar plantilla Excel por LS
✅ Subir Excel relleno
✅ Ver datos parseados
✅ Escribir OBSERVACIONES en el sistema
✅ Senior revisa y comenta
✅ Socio finaliza
✅ HISTORIAL completo: quién, cuándo, qué
✅ Base para REPORTES
```

---

**Creado:** 16-04-2026 22:45 UTC  
**Por:** Claude Code Agent  
**Estado:** Listo para Implementar
