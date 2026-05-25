# Cambios: Flujo de Admisión + Triage

**Fecha:** 2026-03-06
**Módulo afectado:** `templates/admision-paciente.html`

---

## Problema que se resolvió

El flujo de admisión anterior registraba al paciente en la base de datos distribuida y en HAPI FHIR, pero **no creaba un registro de atención ni aplicaba triage**. El proceso terminaba en una pantalla de "Paciente registrado" sin continuar con el flujo clínico real de llegada a urgencias/consulta.

---

## Cambios realizados

### 1. Barra de progreso — de 3 a 4 pasos

| Antes | Después |
|-------|---------|
| Identificar → Verificar → Registrar | Identificar → Verificar → Registrar → **Triage** |

Se añadió `id="sn4"`, `id="sl4"` y `id="line3"` al HTML de la barra de pasos.

### 2. Nuevo panel 4 — Formulario de Admisión + Triage

Reemplazó el antiguo panel de resultado (que pasó a ser el panel 5).

**Campos del formulario:**

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `entidad_salud` | text | EPS / IPS / Hospital |
| `fecha_ingreso` | datetime-local | Auto-rellena con hora actual |
| `modalidad_entrega` | select | Intramural / Extramural / Telemedicina |
| `entorno_atencion` | select | Hospitalario / Ambulatorio / Domiciliario / Urgencias |
| `via_ingreso` | select | Espontánea / Remitido / Urgencias / Traslado |
| `fecha_triage` | datetime-local | Auto-rellena con hora actual |
| `causa_atencion` | textarea | Motivo de consulta libre |
| `clasificacion_triage` | radio cards | Niveles I–V (ver tabla) |

**Clasificación de triage — Resolución 5596 de 2015 (Colombia):**

| Nivel | Color | Nombre | Descripción |
|-------|-------|--------|-------------|
| I | Rojo | Reanimación | Riesgo vital inmediato |
| II | Naranja | Emergencia | Riesgo vital potencial |
| III | Amarillo | Urgencia | Condición que puede empeorar |
| IV | Verde | Menos urgente | Estable, puede esperar |
| V | Azul | No urgente | Sin riesgo vital |

### 3. Panel 5 — Resultado final

El antiguo panel de resultado se renumeró de panel4 a **panel5** y se actualizó para mostrar:
- Nivel de triage asignado con descripción
- ID de atención generado por la base de datos
- Nodo distribuido donde quedó guardado el registro
- Número de documento del paciente

Botones al finalizar:
- **Nueva admisión** — reinicia el flujo desde el paso 1
- **Ir a Módulo Médico** — redirige a `/medico` para continuar la atención

### 4. CSS — Estilos de tarjetas de triage

Se añadieron las clases `.triage-option` y `.triage-card` con efecto visual al seleccionar cada nivel (resaltado con `box-shadow` y `filter: brightness`). El radio button queda oculto y la tarjeta actúa como selector visual.

### 5. JavaScript — Lógica actualizada

**Variables globales añadidas:**
```javascript
let currentDocId = null;   // documento_id del paciente en proceso
let currentNombre = '';    // nombre para mostrar en el encabezado del triage
```

**`goToStep(n)`** — actualizada para manejar 5 paneles (1 al 5).

**`updateStepBar(n)`** — actualizada para manejar 4 pasos visuales (1 al 4).

**Nueva función `goToTriageStep(docId, nombre)`:**
- Guarda el `documento_id` activo en `currentDocId`
- Auto-rellena `fecha_ingreso` y `fecha_triage` con la hora actual del sistema
- Muestra nombre y documento en el encabezado del formulario
- Navega al panel 4

**`admitirExistente()`** — antes mostraba directamente el resultado. Ahora llama a `goToTriageStep()` con los datos del paciente encontrado.

**Submit del formulario de registro (paso 3)** — antes hacía `goToStep(4)`. Ahora llama a `goToTriageStep()` tras un registro exitoso.

**Nuevo listener `triageForm.submit`:**
- Valida que se haya seleccionado un nivel de triage (I al V)
- Llama a `POST /api/v1/medico/atencion` (endpoint ya existente en `app.py`)
- Registra la atención en el nodo PostgreSQL correcto según `documento_id`
- Muestra el resumen en el panel 5

### 6. Endpoint utilizado (sin cambios en el backend)

```
POST /api/v1/medico/atencion
```
Definido en `app.py` con el modelo `AtencionRequest`. Recibe todos los campos del triage y retorna `atencion_id` y `nodo`.

---

## Flujo completo después de los cambios

```
[1] Identificar
    Ingresar tipo + número de documento
    |
[2] Verificar
    Paciente encontrado en DB local  --> "Admitir"           --+
    Paciente encontrado en FHIR      --> "Importar y admitir" -+
    Paciente nuevo                   --> "Registrar"           |
    |                                                          |
[3] Registrar  (solo si es paciente nuevo)                     |
    Llena datos demograficos, guarda en DB + FHIR              |
    |                                                          |
    +<---------------------------------------------------------+
    |
[4] Triage  <-- NUEVO
    Entidad, Modalidad, Entorno, Via de ingreso
    Motivo de consulta
    Clasificacion I / II / III / IV / V
    |
[5] Resultado
    Atencion ID + Triage asignado + Nodo DB
```

---

## Cambios a futuro

### Prioridad Alta

#### 1. Endpoint dedicado `POST /api/v1/admision/triage`

Actualmente el triage reutiliza `/api/v1/medico/atencion`. Se debe crear un endpoint propio en `app.py` que:
- Valide que el `documento_id` exista en la tabla `usuario` antes de insertar en `atencion`
- Retorne información enriquecida (nombre del paciente, nodo, timestamp, nivel de triage)
- Separe semánticamente la lógica de admisión de la lógica del módulo médico

```python
# Pendiente en app.py
@app.post("/api/v1/admision/triage")
async def admision_triage(data: TriageAdmisionRequest):
    # 1. Verificar que el paciente existe en usuario
    # 2. Insertar en atencion con clasificacion_triage
    # 3. Retornar atencion_id, nodo, datos del paciente
    ...
```

#### 2. Validación de FK antes del triage

Si el paciente fue registrado solo en HAPI FHIR pero no en la tabla `usuario` de la DB local, el `INSERT INTO atencion` fallará por la restricción de clave foránea `FOREIGN KEY (documento_id) REFERENCES usuario(documento_id)`. Se debe:
- Verificar la existencia en DB local antes de mostrar el formulario de triage
- Si no existe, ofrecer la opción de importar desde FHIR y crear el registro en `usuario` primero

#### 3. Guardar la admisión en HAPI FHIR como recurso `Encounter`

El estándar HL7 FHIR R4 mapea una atención/admisión al recurso `Encounter`. Se debe:
- Crear un `Encounter` en HAPI FHIR al confirmar el triage
- Vincular el `Encounter.subject` con el `Patient` FHIR ya registrado
- Incluir la clasificación de triage en `Encounter.priority` (código SNOMED CT)
- Guardar el `encounter_id` en la tabla `atencion` (requiere migración)

```sql
-- Migracion pendiente en nodo1.sql, nodo2.sql, nodo3.sql
ALTER TABLE atencion ADD COLUMN fhir_encounter_id VARCHAR(64);
```

### Prioridad Media

#### 4. Registrar el profesional que aplica el triage

La tabla `atencion` no registra quién clasificó al paciente. Se necesita:
- Agregar campo `id_personal_triage UUID` en `atencion` con FK a `profesional_salud`
- En el formulario de triage, agregar un selector de profesional de salud
- Utilizar el listado de `profesional_salud` para poblar el select

```sql
-- Migracion pendiente
ALTER TABLE atencion ADD COLUMN id_personal_triage UUID;
ALTER TABLE atencion ADD CONSTRAINT fk_triage_profesional
    FOREIGN KEY (id_personal_triage) REFERENCES profesional_salud(id_personal_salud);
```

#### 5. Historial de atenciones en el paso de verificación

Cuando un paciente ya existe, mostrar en el paso 2 sus atenciones anteriores: fechas, diagnósticos, última clasificación de triage. Requiere llamar a `GET /api/v1/medico/historia/{documento_id}` y renderizar los resultados en el panel de verificación.

#### 6. Cola de espera por nivel de triage

Después de registrar la admisión, el paciente debe aparecer en una lista de espera ordenada por nivel de triage (I primero, V último). Pendiente crear:
- `GET /api/v1/admision/cola` — atenciones del día sin egreso, ordenadas por `clasificacion_triage`
- Template `cola-espera.html` — vista con actualización automática cada pocos segundos

#### 7. Re-triage

Cuando las condiciones del paciente cambian mientras espera, se debe poder actualizar la clasificación de triage sin crear una nueva atención. Requiere:
- `PATCH /api/v1/admision/triage/{atencion_id}` — actualiza `clasificacion_triage` y `fecha_triage`
- Botón "Re-clasificar" en la cola de espera

### Prioridad Baja

#### 8. Alertas para triage I y II

Cuando se registre triage nivel I (Rojo) o II (Naranja), notificar al módulo médico en tiempo real. Opciones:
- WebSocket desde el servidor FastAPI
- Polling agresivo desde el frontend del médico
- Integración con un sistema de notificaciones interno

#### 9. Estadísticas de triage

Dashboard con distribución de clasificaciones por día/semana/mes. Se puede construir como una query distribuida sobre los tres nodos:

```sql
SELECT clasificacion_triage, COUNT(*) as total
FROM atencion
WHERE fecha_triage >= NOW() - INTERVAL '30 days'
GROUP BY clasificacion_triage
ORDER BY clasificacion_triage;
```

#### 10. Tolerancia a fallos en el registro de triage

Si el nodo PostgreSQL asignado según `documento_id` está caído, el triage falla sin alternativa. Estrategia propuesta:
- Escritura temporal en un nodo disponible con columna `nodo_origen_real` y flag `pendiente_sincronizacion = true`
- Job periódico que migre los registros al nodo correcto cuando vuelva a estar disponible

---

## Archivos modificados

| Archivo | Tipo de cambio | Descripcion |
|---------|----------------|-------------|
| `templates/admision-paciente.html` | Modificado | Nuevo paso 4 de triage, panel 5 de resultado, CSS y JS actualizados |

## Archivos no modificados (reutilizados)

| Archivo | Razon |
|---------|-------|
| `app.py` | Se reutilizo el endpoint `POST /api/v1/medico/atencion` ya existente |
| `middleware.py` | Sin cambios necesarios |
| `nodo1.sql`, `nodo2.sql`, `nodo3.sql` | La tabla `atencion` ya tenia los campos `fecha_triage` y `clasificacion_triage` |

---

**Version del sistema:** 2.1.0
**Proxima tarea recomendada:** Crear endpoint dedicado `/api/v1/admision/triage` con validacion de FK
