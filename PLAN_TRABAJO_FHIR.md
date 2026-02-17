# 📋 Plan de Trabajo: Sistema de Historia Clínica Interoperable con FHIR

## 🎯 Objetivo General

Desarrollar un sistema completo de Historia Clínica Interoperable basado en el estándar FHIR (Fast Healthcare Interoperability Resources) que permita simular la carga de datos cuando un paciente llega por primera vez a una clínica, utilizando los 57 campos definidos en la normativa colombiana de interoperabilidad.

---

## 📊 Arquitectura Propuesta

```
┌─────────────────────────────────────────────────────────────┐
│                    FRONTEND (React/Vue)                      │
│  ┌────────────────────────────────────────────────────┐    │
│  │  Formulario HC Interoperable (57 campos)           │    │
│  │  - Datos demográficos                              │    │
│  │  - Datos de atención                               │    │
│  │  - Tecnologías en salud                            │    │
│  │  - Diagnósticos                                    │    │
│  │  - Egreso                                          │    │
│  └────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                            ↓ HTTP/REST
┌─────────────────────────────────────────────────────────────┐
│              BACKEND API (FastAPI/Python)                    │
│  ┌────────────────────────────────────────────────────┐    │
│  │  Transformación de datos → Recursos FHIR          │    │
│  │  - Patient (Paciente)                              │    │
│  │  - Encounter (Encuentro/Atención)                  │    │
│  │  - MedicationRequest (Medicamentos)                │    │
│  │  - Condition (Diagnósticos)                        │    │
│  │  - Procedure (Procedimientos)                      │    │
│  └────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                            ↓ FHIR REST API
┌─────────────────────────────────────────────────────────────┐
│              HAPI FHIR SERVER (Java/Docker)                  │
│  ┌────────────────────────────────────────────────────┐    │
│  │  Almacenamiento de recursos FHIR                   │    │
│  │  Validación según perfiles FHIR R4/R5              │    │
│  │  API REST estándar FHIR                            │    │
│  └────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                            ↓ JDBC
┌─────────────────────────────────────────────────────────────┐
│         BASE DE DATOS DISTRIBUIDA (PostgreSQL)               │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐             │
│  │  Nodo 1  │    │  Nodo 2  │    │  Nodo 3  │             │
│  │ doc < 4B │    │ 4B-7B    │    │ doc ≥ 7B │             │
│  └──────────┘    └──────────┘    └──────────┘             │
└─────────────────────────────────────────────────────────────┘
```

---

## 📝 Los 57 Campos de Historia Clínica Interoperable

### 1. Datos de Identificación del Usuario (15 campos)
1. Tipo de documento de identidad
2. Número de documento de identidad
3. País de nacionalidad
4. Nombre completo
5. Fecha de nacimiento
6. Edad
7. Unidad de medida de edad
8. Sexo
9. Género
10. Ocupación
11. Voluntad anticipada
12. Categoría de discapacidad
13. País de residencia
14. Municipio de residencia
15. Etnia

### 2. Datos de la Atención (9 campos)
16. Entidad de salud
17. Fecha y hora de ingreso
18. Modalidad de entrega del servicio
19. Entorno de atención
20. Vía de ingreso
21. Causa de la atención
22. Fecha y hora del triage
23. Clasificación del triage
24. Comunidad étnica

### 3. Tecnologías en Salud (11 campos)
25. Descripción del medicamento
26. Dosis
27. Vía de administración
28. Frecuencia
29. Días de tratamiento
30. Unidades aplicadas
31. Identificación del personal de salud
32. Finalidad de la tecnología
33. Tipo de diagnóstico de ingreso
34. Diagnóstico de ingreso
35. Tipo de diagnóstico de egreso

### 4. Diagnósticos (4 campos)
36. Diagnóstico de egreso
37. Diagnóstico relacionado 1
38. Diagnóstico relacionado 2
39. Diagnóstico relacionado 3

### 5. Datos de Egreso (18 campos)
40. Fecha y hora de salida
41. Condición de salida
42. Diagnóstico de muerte
43. Código del prestador
44. Tipo de incapacidad
45. Días de incapacidad
46. Días de licencia de maternidad
47. Alergias
48. Antecedentes familiares
49. Riesgos ocupacionales
50. Responsable del egreso
51. Zona de residencia
52. Dirección de residencia
53. Teléfono
54. Correo electrónico
55. Nombre del responsable
56. Parentesco del responsable
57. Teléfono del responsable

---

## 🗓️ Fases del Proyecto

### **FASE 1: Configuración de HAPI FHIR Server** (Semana 1)

#### Objetivos:
- ✅ Instalar y configurar HAPI FHIR Server
- ✅ Integrar con PostgreSQL distribuido
- ✅ Configurar perfiles FHIR para Colombia

#### Tareas:

**1.1. Agregar HAPI FHIR al docker-compose.yml**
```yaml
services:
  hapi-fhir:
    image: hapiproject/hapi:latest
    container_name: hapi_fhir_server
    ports:
      - "8080:8080"
    environment:
      - spring.datasource.url=jdbc:postgresql://pg_nodo1:5432/fhir_db
      - spring.datasource.username=admin
      - spring.datasource.password=admin
      - hapi.fhir.fhir_version=R4
    depends_on:
      - pg_nodo1
    networks:
      - historia_clinica_net
```

**1.2. Crear base de datos FHIR en cada nodo**
```sql
CREATE DATABASE fhir_db;
```

**1.3. Configurar perfiles FHIR colombianos**
- Definir StructureDefinition para Patient (Paciente)
- Definir StructureDefinition para Encounter (Atención)
- Definir ValueSets para códigos colombianos (CIE-10, CUPS)

**Entregables:**
- ✅ HAPI FHIR Server funcionando en http://localhost:8080/fhir
- ✅ Documentación de endpoints FHIR
- ✅ Perfiles FHIR configurados

---

### **FASE 2: Backend - API de Transformación** (Semana 2)

#### Objetivos:
- ✅ Crear API FastAPI que reciba los 57 campos
- ✅ Transformar datos a recursos FHIR
- ✅ Enviar recursos a HAPI FHIR Server

#### Tareas:

**2.1. Crear modelos Pydantic para los 57 campos**
```python
# models/hc_interoperable.py
class DatosIdentificacion(BaseModel):
    tipo_documento: str
    numero_documento: str
    pais_nacionalidad: str
    nombre_completo: str
    fecha_nacimiento: date
    edad: int
    # ... resto de campos
```

**2.2. Crear transformadores FHIR**
```python
# transformers/fhir_transformer.py
class FHIRTransformer:
    def to_patient(self, datos: DatosIdentificacion) -> dict:
        """Transforma datos a recurso FHIR Patient"""
        
    def to_encounter(self, datos: DatosAtencion) -> dict:
        """Transforma datos a recurso FHIR Encounter"""
        
    def to_medication_request(self, datos: TecnologiasSalud) -> dict:
        """Transforma datos a recurso FHIR MedicationRequest"""
```

**2.3. Crear endpoints de la API**
```python
# endpoints/hc_endpoints.py
@app.post("/api/v1/hc/crear")
async def crear_historia_clinica(hc: HistoriaClinicaCompleta):
    """Recibe los 57 campos y crea recursos FHIR"""
    
@app.get("/api/v1/hc/{documento_id}")
async def obtener_historia_clinica(documento_id: str):
    """Obtiene HC completa desde HAPI FHIR"""
```

**2.4. Integrar con HAPI FHIR**
```python
# services/fhir_service.py
class FHIRService:
    def __init__(self):
        self.base_url = "http://hapi-fhir:8080/fhir"
    
    def create_patient(self, patient_resource: dict):
        """POST a HAPI FHIR Server"""
        
    def search_patient(self, identifier: str):
        """GET desde HAPI FHIR Server"""
```

**Entregables:**
- ✅ API REST con endpoints documentados
- ✅ Transformadores FHIR completos
- ✅ Integración con HAPI FHIR funcionando
- ✅ Tests unitarios

---

### **FASE 3: Frontend - Formulario Interactivo** (Semana 3)

#### Objetivos:
- ✅ Crear interfaz web moderna para captura de datos
- ✅ Validación de campos en tiempo real
- ✅ Experiencia de usuario optimizada

#### Tareas:

**3.1. Elegir stack tecnológico**
- **Opción A**: React + TypeScript + Tailwind CSS
- **Opción B**: Vue 3 + TypeScript + Vuetify
- **Opción C**: HTML5 + JavaScript Vanilla + CSS moderno (más simple)

**3.2. Diseñar estructura del formulario**
```
┌─────────────────────────────────────────┐
│  Historia Clínica - Primera Consulta   │
├─────────────────────────────────────────┤
│  [Paso 1/5] Datos de Identificación    │
│  ┌───────────────────────────────────┐ │
│  │ Tipo documento: [▼]               │ │
│  │ Número: [____________]            │ │
│  │ Nombre: [____________]            │ │
│  └───────────────────────────────────┘ │
│                                         │
│  [Anterior] [Siguiente →]              │
└─────────────────────────────────────────┘
```

**3.3. Implementar wizard multi-paso**
- Paso 1: Datos de Identificación (15 campos)
- Paso 2: Datos de Atención (9 campos)
- Paso 3: Tecnologías en Salud (11 campos)
- Paso 4: Diagnósticos (4 campos)
- Paso 5: Datos de Egreso (18 campos)

**3.4. Validaciones y UX**
- Validación en tiempo real
- Mensajes de error claros
- Autocompletado para códigos (CIE-10, CUPS)
- Guardado automático (draft)
- Indicador de progreso

**3.5. Integración con Backend**
```javascript
// services/api.js
async function crearHistoriaClinica(datos) {
    const response = await fetch('/api/v1/hc/crear', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(datos)
    });
    return response.json();
}
```

**Entregables:**
- ✅ Formulario web completo y funcional
- ✅ Validaciones implementadas
- ✅ Diseño responsive
- ✅ Integración con backend

---

### **FASE 4: Simulación de Flujo Clínico** (Semana 4)

#### Objetivos:
- ✅ Simular el flujo completo de atención
- ✅ Generar datos de prueba realistas
- ✅ Visualización de historia clínica

#### Tareas:

**4.1. Crear generador de datos de prueba**
```python
# utils/data_generator.py
class DataGenerator:
    def generar_paciente_aleatorio(self):
        """Genera datos realistas de paciente"""
        
    def generar_atencion_urgencias(self):
        """Simula llegada a urgencias"""
        
    def generar_atencion_consulta_externa(self):
        """Simula consulta externa"""
```

**4.2. Implementar flujos de atención**
- Flujo 1: Urgencias (triage → atención → egreso)
- Flujo 2: Consulta externa (cita → atención → seguimiento)
- Flujo 3: Hospitalización (ingreso → evolución → egreso)

**4.3. Dashboard de visualización**
```
┌─────────────────────────────────────────┐
│  Historia Clínica - Juan Pérez         │
├─────────────────────────────────────────┤
│  📋 Datos Demográficos                  │
│  🏥 Atenciones (3)                      │
│  💊 Medicamentos (5)                    │
│  🩺 Diagnósticos (2)                    │
│  📊 Timeline de atenciones              │
└─────────────────────────────────────────┘
```

**4.4. Reportes y exportación**
- Exportar HC en formato FHIR JSON
- Exportar HC en formato PDF
- Exportar HC en formato HL7 v2

**Entregables:**
- ✅ Generador de datos funcionando
- ✅ Simulación de flujos completa
- ✅ Dashboard de visualización
- ✅ Exportación en múltiples formatos

---

### **FASE 5: Integración y Pruebas** (Semana 5)

#### Objetivos:
- ✅ Integración completa de todos los componentes
- ✅ Pruebas de interoperabilidad
- ✅ Optimización de rendimiento

#### Tareas:

**5.1. Pruebas de integración**
- Flujo completo: Frontend → Backend → HAPI FHIR → PostgreSQL
- Validación de recursos FHIR
- Pruebas de fragmentación distribuida

**5.2. Pruebas de interoperabilidad**
- Validar recursos contra perfiles FHIR oficiales
- Probar con herramientas FHIR (Postman, Insomnia)
- Validar con FHIR Validator

**5.3. Optimización**
- Caché de recursos frecuentes
- Índices en PostgreSQL
- Paginación de resultados

**5.4. Documentación**
- Guía de usuario
- Documentación técnica
- Ejemplos de uso

**Entregables:**
- ✅ Sistema completamente integrado
- ✅ Suite de pruebas completa
- ✅ Documentación finalizada
- ✅ Sistema optimizado

---

## 🛠️ Stack Tecnológico Completo

### Backend
- **FastAPI** - Framework web Python
- **Pydantic** - Validación de datos
- **fhir.resources** - Librería Python para FHIR
- **httpx** - Cliente HTTP para comunicación con HAPI FHIR
- **PostgreSQL** - Base de datos distribuida

### FHIR Server
- **HAPI FHIR** - Servidor FHIR de referencia
- **PostgreSQL** - Almacenamiento de recursos FHIR

### Frontend (Opción recomendada: React)
- **React 18** - Framework UI
- **TypeScript** - Tipado estático
- **Tailwind CSS** - Estilos
- **React Hook Form** - Manejo de formularios
- **Zod** - Validación de esquemas
- **Axios** - Cliente HTTP

### DevOps
- **Docker** - Contenerización
- **Docker Compose** - Orquestación
- **GitHub Actions** - CI/CD (opcional)

---

## 📦 Estructura de Archivos Propuesta

```
historia-clinica-distribuida/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── models/
│   │   │   ├── hc_interoperable.py
│   │   │   └── fhir_resources.py
│   │   ├── transformers/
│   │   │   └── fhir_transformer.py
│   │   ├── services/
│   │   │   ├── fhir_service.py
│   │   │   └── database_service.py
│   │   ├── endpoints/
│   │   │   ├── hc_endpoints.py
│   │   │   └── fhir_endpoints.py
│   │   └── utils/
│   │       ├── data_generator.py
│   │       └── validators.py
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── FormularioHC/
│   │   │   │   ├── Paso1Identificacion.tsx
│   │   │   │   ├── Paso2Atencion.tsx
│   │   │   │   ├── Paso3Tecnologias.tsx
│   │   │   │   ├── Paso4Diagnosticos.tsx
│   │   │   │   └── Paso5Egreso.tsx
│   │   │   └── Dashboard/
│   │   │       ├── VisualizadorHC.tsx
│   │   │       └── TimelineAtenciones.tsx
│   │   ├── services/
│   │   │   └── api.ts
│   │   ├── types/
│   │   │   └── hc.types.ts
│   │   └── App.tsx
│   ├── package.json
│   └── Dockerfile
├── hapi-fhir/
│   ├── config/
│   │   └── application.yaml
│   └── profiles/
│       ├── Patient-co.json
│       ├── Encounter-co.json
│       └── ValueSets/
├── docker-compose.yml
├── init-databases.sh
└── README.md
```

---

## 📊 Recursos FHIR a Implementar

### 1. Patient (Paciente)
```json
{
  "resourceType": "Patient",
  "identifier": [{
    "system": "http://www.minsalud.gov.co/identificacion",
    "value": "1234567890"
  }],
  "name": [{
    "text": "Juan Pérez García"
  }],
  "birthDate": "1985-03-15",
  "gender": "male"
}
```

### 2. Encounter (Encuentro/Atención)
```json
{
  "resourceType": "Encounter",
  "status": "finished",
  "class": {
    "code": "AMB",
    "display": "Ambulatorio"
  },
  "subject": {
    "reference": "Patient/123"
  },
  "period": {
    "start": "2026-02-14T10:00:00Z",
    "end": "2026-02-14T11:30:00Z"
  }
}
```

### 3. MedicationRequest (Solicitud de Medicamento)
```json
{
  "resourceType": "MedicationRequest",
  "status": "active",
  "intent": "order",
  "medicationCodeableConcept": {
    "text": "Acetaminofén 500mg"
  },
  "subject": {
    "reference": "Patient/123"
  },
  "dosageInstruction": [{
    "text": "1 tableta cada 8 horas por 3 días"
  }]
}
```

### 4. Condition (Diagnóstico)
```json
{
  "resourceType": "Condition",
  "code": {
    "coding": [{
      "system": "http://hl7.org/fhir/sid/icd-10",
      "code": "J00",
      "display": "Rinofaringitis aguda"
    }]
  },
  "subject": {
    "reference": "Patient/123"
  }
}
```

---

## 🎯 Criterios de Éxito

### Funcionales
- ✅ Captura de los 57 campos obligatorios
- ✅ Transformación correcta a recursos FHIR
- ✅ Almacenamiento distribuido funcionando
- ✅ Consulta de HC completa
- ✅ Exportación en formatos estándar

### No Funcionales
- ✅ Tiempo de respuesta < 2 segundos
- ✅ Validación FHIR al 100%
- ✅ Interfaz responsive
- ✅ Documentación completa
- ✅ Cobertura de tests > 80%

---

## 📅 Cronograma Detallado

| Semana | Fase | Actividades Principales | Entregables |
|--------|------|------------------------|-------------|
| 1 | HAPI FHIR Setup | Instalación, configuración, perfiles | HAPI FHIR operativo |
| 2 | Backend API | Modelos, transformadores, endpoints | API REST completa |
| 3 | Frontend | Formulario, validaciones, UX | Interfaz funcional |
| 4 | Simulación | Generador datos, flujos, dashboard | Sistema simulado |
| 5 | Integración | Pruebas, optimización, documentación | Sistema completo |

---

## 🚀 Próximos Pasos Inmediatos

### 1. Decisión de Stack Frontend
**Pregunta**: ¿Prefieres React, Vue o HTML/JS vanilla?

### 2. Configurar HAPI FHIR
```bash
# Agregar al docker-compose.yml
# Levantar servidor FHIR
# Verificar funcionamiento
```

### 3. Crear estructura de proyecto
```bash
mkdir -p backend/app/{models,transformers,services,endpoints,utils}
mkdir -p frontend/src/{components,services,types}
mkdir -p hapi-fhir/{config,profiles}
```

---

## 📚 Referencias

- [FHIR R4 Specification](https://hl7.org/fhir/R4/)
- [HAPI FHIR Documentation](https://hapifhir.io/)
- [Resolución 866 de 2021 - MinSalud Colombia](https://www.minsalud.gov.co/)
- [Perfiles FHIR Colombia](https://build.fhir.org/ig/HL7/fhir-ips/)

---

**Fecha de creación**: 2026-02-14  
**Versión**: 1.0  
**Autor**: Sistema de Historia Clínica Distribuida
