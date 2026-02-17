# Sistema de Historia Clínica Distribuida

## 🏥 Descripción General

Sistema completo de historia clínica distribuida que implementa fragmentación horizontal de datos sobre PostgreSQL, con una interfaz web de monitoreo y gestión en tiempo real. El sistema simula un entorno de base de datos distribuida utilizando contenedores Docker y un middleware Python para coordinar consultas distribuidas.

## 🏗️ Arquitectura del Sistema

### Componentes Principales

- **3 Nodos PostgreSQL**: Contenedores independientes con fragmentación de datos por `documento_id`
- **API FastAPI**: Backend para gestión de nodos y ejecución de consultas distribuidas
- **Frontend Web**: Dashboard en tiempo real para monitoreo y control
- **Middleware Python**: Lógica de coordinación de consultas distribuidas

### Esquema de Fragmentación

Los datos se distribuyen según el rango de `documento_id`:
- **Nodo 1** (Puerto 5433): `documento_id < 4,000,000,000`
- **Nodo 2** (Puerto 5434): `4,000,000,000 ≤ documento_id < 7,000,000,000`
- **Nodo 3** (Puerto 5435): `documento_id ≥ 7,000,000,000`

## 🛠️ Stack Tecnológico

### Backend
- **Python 3.8+**: Lenguaje principal
- **FastAPI**: Framework API REST
- **PostgreSQL 15**: Sistema de base de datos
- **Psycopg2**: Driver PostgreSQL para Python
- **Docker SDK**: Gestión de contenedores
- **Uvicorn**: Servidor ASGI

### Frontend
- **HTML5/CSS3/JavaScript**: Tecnologías web estándar
- **Phosphor Icons**: Biblioteca de iconos
- **CSS Grid/Flexbox**: Diseño responsivo
- **Fetch API**: Comunicación asíncrona

### Infraestructura
- **Docker**: Contenerización
- **Docker Compose**: Orquestación de servicios
- **Volúmenes Docker**: Persistencia de datos

## 📊 Modelo de Datos

### Tablas Principales

1. **usuario**: Información demográfica del paciente
2. **atencion**: Registro de eventos de atención médica
3. **tecnologia_salud**: Medicamentos y procedimientos
4. **diagnostico**: Diagnósticos de ingreso y egreso
5. **egreso**: Información de alta médica
6. **profesional_salud**: Datos del personal de salud

### Relaciones
- `usuario` ← `atencion` ← `tecnologia_salud`
- `atencion` ← `diagnostico`
- `atencion` ← `egreso`
- `profesional_salud` ← `tecnologia_salud`

## 🚀 Configuración y Despliegue

### Prerrequisitos
```bash
# Instalar Docker y Docker Compose
# Verificar instalación
docker --version
docker-compose --version

# Instalar Python 3.8+
python3 --version

# Clonar repositorio
git clone <repository-url>
cd historia-clinica-distribuida
```

### Instalación de Dependencias
```bash
# Crear entorno virtual (recomendado)
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# Instalar dependencias Python
pip install fastapi uvicorn psycopg2-binary docker pydantic
```

### Despliegue de Infraestructura
```bash
# Levantar nodos PostgreSQL
docker-compose up -d

# Verificar estado de contenedores
docker-compose ps

# Cargar esquema en cada nodo
psql -h localhost -p 5433 -U admin -d historia_clinica -f nodo1.sql
psql -h localhost -p 5434 -U admin -d historia_clinica -f nodo2.sql
psql -h localhost -p 5435 -U admin -d historia_clinica -f nodo3.sql
```

### Iniciar Aplicación
```bash
# Iniciar servidor API
python app.py
# O con uvicorn directamente
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

### Acceso a la Aplicación
- **Dashboard Web**: http://localhost:8000
- **API Endpoints**: http://localhost:8000/api
- **Documentación API**: http://localhost:8000/docs

## 🔧 Funcionalidades

### Gestión de Nodos
- **Monitoreo en tiempo real**: Estado y disponibilidad de cada nodo
- **Control de contenedores**: Start/Stop/Restart de nodos individuales
- **Visualización de puertos**: Mapeo de puertos de cada nodo

### Consultas Distribuidas
- **Ejecución transparente**: Queries SQL ejecutados en todos los nodos
- **Agregación de resultados**: Combinación automática de resultados
- **Manejo de fallos**: Continúa operando con nodos caídos
- **Estado de nodos**: Reporte de disponibilidad por consulta

### Interfaz Web
- **Dashboard responsivo**: Diseño adaptativo para diferentes dispositivos
- **Actualización automática**: Polling cada 3 segundos
- **Feedback visual**: Indicadores de estado y progreso
- **Consola SQL**: Editor de consultas con resaltado de sintaxis

## 📁 Estructura del Proyecto

```
historia-clinica-distribuida/
├── app.py                    # API FastAPI principal
├── middleware.py             # Lógica de consultas distribuidas
├── docker-compose.yml       # Orquestación de contenedores
├── requirements.txt          # Dependencias Python
├── nodo1.sql                # Esquema para nodo 1
├── nodo2.sql                # Esquema para nodo 2
├── nodo3.sql                # Esquema para nodo 3
├── templates/
│   └── index.html          # Interfaz web principal
├── static/
│   ├── style.css           # Estilos CSS
│   └── script.js           # Lógica JavaScript frontend
└── README.md               # Documentación del proyecto
```

## 🔌 API Endpoints

### Gestión de Nodos
- `GET /api/nodes` - Listar estado de todos los nodos
- `POST /api/nodes/{node_id}/{action}` - Control de nodos (start/stop/restart)

### Consultas Distribuidas
- `POST /api/execute-query` - Ejecutar consulta en todos los nodos

### Web Interface
- `GET /` - Dashboard principal
- `GET /static/*` - Recursos estáticos

## 🧪 Ejemplos de Uso

### Consultas SQL de Ejemplo
```sql
-- Consulta básica de usuarios
SELECT documento_id, nombre_completo, edad FROM usuario;

-- Consulta con JOINs
SELECT u.nombre_completo, a.entidad_salud, a.fecha_ingreso
FROM usuario u 
JOIN atencion a ON u.documento_id = a.documento_id;

-- Consulta de diagnósticos
SELECT d.diagnostico_ingreso, d.diagnostico_egreso
FROM diagnostico d
JOIN atencion a ON d.atencion_id = a.atencion_id;
```

### Operaciones CRUD
```sql
-- Insertar usuario (se dirige al nodo correcto automáticamente)
INSERT INTO usuario (documento_id, nombre_completo, edad, sexo)
VALUES (123456789, 'Juan Pérez', 35, 'M');

-- Actualizar datos
UPDATE usuario SET edad = 36 WHERE documento_id = 123456789;

-- Eliminar registro
DELETE FROM usuario WHERE documento_id = 123456789;
```

## 🔍 Monitoreo y Diagnóstico

### Verificación de Estado
```bash
# Estado de contenedores
docker-compose ps

# Logs de contenedores
docker-compose logs pg_nodo1
docker-compose logs pg_nodo2
docker-compose logs pg_nodo3

# Conexión directa a nodos
psql -h localhost -p 5433 -U admin -d historia_clinica
psql -h localhost -p 5434 -U admin -d historia_clinica
psql -h localhost -p 5435 -U admin -d historia_clinica
```

### Métricas de Rendimiento
- **Latencia de consultas**: Tiempo de respuesta distribuida
- **Disponibilidad**: Porcentaje de nodos operativos
- **Distribución de datos**: Balance de carga entre nodos

## 🛡️ Consideraciones de Seguridad

### Configuración por Defecto
- **Credenciales**: admin/admin (solo para desarrollo)
- **Red interna**: Comunicación entre contenedores Docker
- **CORS**: Permitido desde cualquier origen (solo desarrollo)

### Recomendaciones para Producción
- Cambiar credenciales por defecto
- Implementar SSL/TLS
- Configurar firewall y redes privadas
- Auditoría de accesos y logs

## 🔄 Mantenimiento

### Tareas Regulares
```bash
# Limpiar contenedores e imágenes no utilizadas
docker system prune -a

# Realizar backup de volúmenes
docker run --rm -v pg_data_nodo1:/data -v $(pwd):/backup alpine tar czf /backup/nodo1_backup.tar.gz -C /data .

# Actualizar imágenes
docker-compose pull
docker-compose up -d
```

### Escalado
- **Horizontal**: Agregar nuevos nodos modificando `docker-compose.yml`
- **Vertical**: Aumentar recursos de contenedores existentes
- **Rebalanceo**: Redistribuir datos según nuevas particiones

## 🐛 Solución de Problemas

### Docker Compose
Si los nodos PostgreSQL no arrancan o la app no conecta:

1. **Comprobar Docker y Compose**
   - Docker: `docker --version`
   - Compose v2: `docker compose version` → usar `docker compose up -d`
   - Compose v1: `docker-compose --version` → usar `docker-compose up -d`

2. **Script de verificación** (recomendado)
   ```bash
   ./verificar-docker.sh
   ```
   Comprueba Docker, puertos 5433–5435, levanta los contenedores y opcionalmente prueba la conexión.

3. **Puertos ocupados**  
   Si 5433, 5434 o 5435 están en uso, detén el proceso o cambia los puertos en `docker-compose.yml` (y en `middleware.py` si cambias).

4. **Estado y salud**
   ```bash
   docker compose ps   # o docker-compose ps
   ```
   Los tres nodos deberían estar `Up` y `healthy` (healthcheck con `pg_isready`).

5. **Logs**
   ```bash
   docker compose logs pg_nodo1
   docker compose logs -f pg_nodo2   # seguir en tiempo real
   ```

### Problemas Comunes
1. **Nodos no inician**: Verificar disponibilidad de puertos 5433-5435; ejecutar `./verificar-docker.sh`.
2. **Conexión rechazada**: Confirmar que contenedores estén corriendo y `healthy`; esperar unos segundos tras `up -d`.
3. **Query sin resultados**: Verificar que datos existan en el rango correcto; cargar esquema con `nodo1.sql`, `nodo2.sql`, `nodo3.sql`.

### Depuración
```bash
# Verificar conectividad
telnet localhost 5433
telnet localhost 5434
telnet localhost 5435

# Probar conexión PostgreSQL
python -c "import psycopg2; print('Driver OK')"

# Verificar logs de aplicación
python app.py  # Ejecutar en modo verbose
```

## 📈 Mejoras Futuras

### Planeadas
- [ ] Autenticación y autorización de usuarios
- [ ] Interfaz de administración avanzada
- [ ] Métricas de rendimiento y graficos
- [ ] Sistema de backup automático
- [ ] Sharding automático basado en carga

### Opcionales
- [ ] Migración a Kubernetes
- [ ] Implementación de Redis para caché
- [ ] Sistema de notificaciones en tiempo real
- [ ] API GraphQL alternativa

## 📄 Licencia

Este proyecto es para fines educativos y de demostración. Consulte la licencia específica para términos de uso.

## 👥 Contribuciones

Las contribuciones son bienvenidas. Por favor:
1. Fork del repositorio
2. Crear rama de características
3. Enviar Pull Request con descripción detallada

---

**Autor**: Sistema de Historia Clínica Distribuida  
**Versión**: 2.0.0  
**Última actualización**: 2026-02-17