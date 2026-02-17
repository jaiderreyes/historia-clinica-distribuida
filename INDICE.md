# 📚 Índice de Documentación - Historia Clínica Distribuida + FHIR

## 🎯 Estado Actual del Proyecto

**Fase Actual**: Sistema base con Docker operativo ✅  
**Próxima Fase**: Implementación FHIR + Formulario de 57 campos 🚀

---

## 📖 Guías de Documentación

### 1. **Sistema Actual (Docker + PostgreSQL)**

#### 📄 [README.md](./README.md)
- **Qué es**: Documentación general del proyecto
- **Cuándo leer**: Primera vez que accedes al proyecto
- **Contenido**: Arquitectura, instalación, uso básico
- **Tiempo de lectura**: 10 minutos

#### 📄 [DOCKER.md](./DOCKER.md)
- **Qué es**: Guía completa de Docker
- **Cuándo leer**: Cuando necesites trabajar con contenedores
- **Contenido**: Comandos, troubleshooting, arquitectura Docker
- **Tiempo de lectura**: 8 minutos

#### 📄 [EJECUTANDO.md](./EJECUTANDO.md)
- **Qué es**: Estado actual del sistema en ejecución
- **Cuándo leer**: Para verificar que todo está funcionando
- **Contenido**: Servicios activos, pruebas realizadas, próximos pasos
- **Tiempo de lectura**: 5 minutos

---

### 2. **Nuevo Plan FHIR (Interoperabilidad)**

#### 📄 [PLAN_TRABAJO_FHIR.md](./PLAN_TRABAJO_FHIR.md) ⭐ **PRINCIPAL**
- **Qué es**: Plan completo de trabajo para implementar FHIR
- **Cuándo leer**: Antes de empezar la implementación FHIR
- **Contenido**: 
  - 5 fases detalladas (5 semanas)
  - Arquitectura completa
  - Stack tecnológico
  - Recursos FHIR a implementar
  - Cronograma
- **Tiempo de lectura**: 20 minutos

#### 📄 [INICIO_RAPIDO_FHIR.md](./INICIO_RAPIDO_FHIR.md) ⭐ **ACCIÓN INMEDIATA**
- **Qué es**: Guía de inicio rápido para comenzar HOY
- **Cuándo leer**: Cuando quieras empezar a implementar
- **Contenido**:
  - Checklist de inicio
  - MVP (Minimum Viable Product)
  - Tareas priorizadas
  - Comandos útiles
  - Decisiones clave
- **Tiempo de lectura**: 10 minutos

#### 📄 [57_CAMPOS_HC.md](./57_CAMPOS_HC.md) ⭐ **REFERENCIA**
- **Qué es**: Especificación completa de los 57 campos
- **Cuándo leer**: Durante el desarrollo del formulario
- **Contenido**:
  - Lista completa de campos
  - Tipos de datos
  - Valores permitidos
  - Ejemplos
  - Mapeo a FHIR
- **Tiempo de lectura**: 15 minutos (referencia continua)

---

## 🗺️ Ruta de Aprendizaje Recomendada

### Para Empezar Desde Cero

```
1. README.md (10 min)
   ↓
2. EJECUTANDO.md (5 min) - Verificar que el sistema actual funciona
   ↓
3. PLAN_TRABAJO_FHIR.md (20 min) - Entender el plan completo
   ↓
4. INICIO_RAPIDO_FHIR.md (10 min) - Decidir por dónde empezar
   ↓
5. 57_CAMPOS_HC.md (referencia) - Consultar durante desarrollo
```

**Tiempo total**: ~45 minutos + desarrollo

### Para Continuar el Desarrollo

```
1. INICIO_RAPIDO_FHIR.md - Ver tareas priorizadas
   ↓
2. 57_CAMPOS_HC.md - Referencia de campos
   ↓
3. PLAN_TRABAJO_FHIR.md - Consultar fase actual
```

---

## 🎯 Decisiones Pendientes

Antes de continuar con la implementación, necesitas decidir:

### 1. **Stack de Frontend**
- [ ] **Opción A**: React + TypeScript (profesional, escalable)
- [ ] **Opción B**: HTML/JS Vanilla (rápido, simple)
- [ ] **Opción C**: Vue 3 (intermedio)

**Recomendación**: HTML/JS Vanilla para MVP, migrar a React después

### 2. **Alcance del MVP**
- [ ] **Opción A**: Solo Patient (15 campos de identificación)
- [ ] **Opción B**: Patient + Encounter (24 campos)
- [ ] **Opción C**: Sistema completo (57 campos)

**Recomendación**: Opción A para validar flujo rápidamente

### 3. **Prioridad**
- [ ] **Velocidad**: MVP funcional en 1 semana
- [ ] **Calidad**: Sistema completo en 5 semanas
- [ ] **Balanceado**: MVP en 1 semana + iteraciones

**Recomendación**: Balanceado

---

## 📋 Checklist de Implementación

### Fase 1: HAPI FHIR Server (Esta Semana)
- [ ] Agregar HAPI FHIR a docker-compose.yml
- [ ] Levantar y verificar HAPI FHIR
- [ ] Probar endpoints FHIR con curl
- [ ] Crear recurso Patient de prueba

### Fase 2: Backend API (Próxima Semana)
- [ ] Crear estructura de carpetas backend
- [ ] Instalar fhir.resources
- [ ] Crear modelos Pydantic
- [ ] Implementar transformador FHIR
- [ ] Crear endpoints REST

### Fase 3: Frontend (Semana 3)
- [ ] Elegir stack (React/HTML/Vue)
- [ ] Crear formulario de identificación
- [ ] Implementar validaciones
- [ ] Integrar con backend
- [ ] Probar flujo completo

---

## 🚀 Comandos Rápidos

### Ver Estado Actual
```bash
export PATH="/Applications/Docker.app/Contents/Resources/bin:$PATH"
docker compose ps
curl http://localhost:8001/api/health
```

### Acceder al Sistema
- Dashboard: http://localhost:8001
- API Docs: http://localhost:8001/docs
- HAPI FHIR (cuando esté): http://localhost:8080/fhir

### Ver Documentación
```bash
# Abrir plan de trabajo
open PLAN_TRABAJO_FHIR.md

# Abrir guía de inicio
open INICIO_RAPIDO_FHIR.md

# Abrir referencia de campos
open 57_CAMPOS_HC.md
```

---

## 📊 Estructura del Proyecto

```
historia-clinica-distribuida/
├── 📚 DOCUMENTACIÓN
│   ├── README.md                    # Documentación general
│   ├── DOCKER.md                    # Guía de Docker
│   ├── EJECUTANDO.md                # Estado actual
│   ├── PLAN_TRABAJO_FHIR.md        # Plan completo FHIR ⭐
│   ├── INICIO_RAPIDO_FHIR.md       # Guía de inicio ⭐
│   └── 57_CAMPOS_HC.md             # Referencia de campos ⭐
│
├── 🐳 DOCKER
│   ├── docker-compose.yml           # Orquestación de servicios
│   ├── Dockerfile                   # Imagen de la app
│   ├── .dockerignore               # Exclusiones
│   └── init-databases.sh           # Inicialización BD
│
├── 🔧 BACKEND ACTUAL
│   ├── app.py                       # API FastAPI
│   ├── middleware.py                # Consultas distribuidas
│   └── requirements.txt             # Dependencias Python
│
├── 🎨 FRONTEND ACTUAL
│   ├── templates/
│   │   ├── index.html              # Dashboard
│   │   └── firh.html               # Formulario HC
│   └── static/
│       ├── style.css               # Estilos
│       └── script.js               # Lógica frontend
│
├── 🗄️ BASE DE DATOS
│   ├── nodo1.sql                    # Esquema nodo 1
│   ├── nodo2.sql                    # Esquema nodo 2
│   └── nodo3.sql                    # Esquema nodo 3
│
└── 🚀 PRÓXIMOS (a crear)
    ├── backend/                     # Backend FHIR
    ├── frontend/                    # Frontend React/Vue
    └── hapi-fhir/                   # Configuración HAPI FHIR
```

---

## 🎓 Recursos de Aprendizaje

### FHIR
- [FHIR R4 Specification](https://hl7.org/fhir/R4/)
- [FHIR in 5 minutes](https://www.hl7.org/fhir/overview.html)
- [FHIR Patient Resource](https://www.hl7.org/fhir/patient.html)

### HAPI FHIR
- [HAPI FHIR Documentation](https://hapifhir.io/)
- [HAPI FHIR Docker](https://hub.docker.com/r/hapiproject/hapi)

### Python FHIR
- [fhir.resources](https://pypi.org/project/fhir.resources/)
- [FHIR Client Python](https://github.com/smart-on-fhir/client-py)

### Normativa Colombia
- [Resolución 866 de 2021](https://www.minsalud.gov.co/)
- [MinSalud - Interoperabilidad](https://www.minsalud.gov.co/)

---

## ❓ Preguntas Frecuentes

### ¿Por dónde empiezo?
👉 Lee **INICIO_RAPIDO_FHIR.md** y decide el stack de frontend.

### ¿Cuánto tiempo tomará?
👉 MVP: 1 semana | Sistema completo: 5 semanas (ver PLAN_TRABAJO_FHIR.md)

### ¿Qué son los 57 campos?
👉 Lee **57_CAMPOS_HC.md** para la especificación completa.

### ¿Cómo funciona FHIR?
👉 Lee la sección de arquitectura en **PLAN_TRABAJO_FHIR.md**

### ¿El sistema actual funciona?
👉 Verifica en **EJECUTANDO.md** y prueba http://localhost:8001

---

## 📞 Próximos Pasos

1. **Lee INICIO_RAPIDO_FHIR.md** (10 minutos)
2. **Decide el stack de frontend** (React/HTML/Vue)
3. **Confirma el alcance del MVP** (15/24/57 campos)
4. **Comienza la implementación** siguiendo el plan

---

**Última actualización**: 2026-02-14  
**Versión del proyecto**: 2.0 (FHIR en desarrollo)  
**Estado**: Sistema base operativo, FHIR en planificación
