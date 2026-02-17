# 🐳 Guía de Ejecución con Docker

## 📋 Prerrequisitos

- Docker Desktop instalado (incluye Docker Compose)
- Puertos disponibles: 5433, 5434, 5435, 8001

## 🚀 Inicio Rápido

### 1. Levantar todos los servicios

```bash
# Construir y levantar todos los contenedores
docker compose up -d --build
```

Este comando:
- ✅ Construye la imagen de la aplicación FastAPI
- ✅ Levanta 3 nodos PostgreSQL (pg_nodo1, pg_nodo2, pg_nodo3)
- ✅ Levanta la aplicación web en el puerto 8001
- ✅ Espera a que los nodos estén saludables antes de iniciar la app

### 2. Inicializar las bases de datos

```bash
# Dar permisos de ejecución al script
chmod +x init-databases.sh

# Ejecutar el script de inicialización
./init-databases.sh
```

### 3. Acceder a la aplicación

- **Dashboard Web**: http://localhost:8001
- **Carga HC**: http://localhost:8001/carga-hc
- **API Docs**: http://localhost:8001/docs

## 🔍 Comandos Útiles

### Ver estado de los contenedores
```bash
docker compose ps
```

### Ver logs de un servicio
```bash
# Logs de la aplicación
docker compose logs -f app

# Logs de un nodo específico
docker compose logs -f pg_nodo1
docker compose logs -f pg_nodo2
docker compose logs -f pg_nodo3
```

### Detener los servicios
```bash
docker compose down
```

### Detener y eliminar volúmenes (⚠️ elimina datos)
```bash
docker compose down -v
```

### Reiniciar un servicio específico
```bash
docker compose restart app
docker compose restart pg_nodo1
```

## 🔧 Verificación Manual

### Conectarse a un nodo PostgreSQL
```bash
# Nodo 1
docker exec -it pg_nodo1 psql -U admin -d historia_clinica

# Nodo 2
docker exec -it pg_nodo2 psql -U admin -d historia_clinica

# Nodo 3
docker exec -it pg_nodo3 psql -U admin -d historia_clinica
```

### Ver tablas en un nodo
```bash
docker exec -it pg_nodo1 psql -U admin -d historia_clinica -c '\dt'
```

### Ejecutar una consulta de prueba
```bash
docker exec -it pg_nodo1 psql -U admin -d historia_clinica -c 'SELECT * FROM usuario;'
```

## 🏗️ Arquitectura Docker

```
┌─────────────────────────────────────────────────┐
│           Docker Network (bridge)               │
│                                                 │
│  ┌──────────────┐                              │
│  │     app      │  Puerto: 8001                │
│  │  (FastAPI)   │  Imagen: Custom              │
│  └──────┬───────┘                              │
│         │                                       │
│    ┌────┴────┬────────┬────────┐              │
│    │         │        │        │              │
│  ┌─▼──┐   ┌─▼──┐  ┌─▼──┐   ┌─▼──┐          │
│  │pg_ │   │pg_ │  │pg_ │   │    │          │
│  │nodo│   │nodo│  │nodo│   │    │          │
│  │ 1  │   │ 2  │  │ 3  │   │    │          │
│  └────┘   └────┘  └────┘   └────┘          │
│  :5433    :5434   :5435                      │
│                                               │
└───────────────────────────────────────────────┘
```

## 📊 Distribución de Datos

- **Nodo 1** (Puerto 5433): `documento_id < 4,000,000,000`
- **Nodo 2** (Puerto 5434): `4,000,000,000 ≤ documento_id < 7,000,000,000`
- **Nodo 3** (Puerto 5435): `documento_id ≥ 7,000,000,000`

## 🐛 Solución de Problemas

### Error: "port is already allocated"
```bash
# Ver qué proceso está usando el puerto
lsof -i :8001
lsof -i :5433

# Cambiar el puerto en docker-compose.yml o detener el proceso
```

### Error: "Cannot connect to the Docker daemon"
```bash
# Asegurarse de que Docker Desktop está corriendo
open -a Docker
```

### Los contenedores no inician
```bash
# Ver logs detallados
docker compose logs

# Reconstruir desde cero
docker compose down -v
docker compose up -d --build
```

### La app no puede conectarse a los nodos
```bash
# Verificar que los nodos estén healthy
docker compose ps

# Verificar la red
docker network inspect historia-clinica-distribuida_historia_clinica_net
```

## 🔄 Actualizar el Código

Si haces cambios en el código:

```bash
# Reconstruir solo la aplicación
docker compose up -d --build app

# O reconstruir todo
docker compose down
docker compose up -d --build
```

## 📦 Volúmenes

Los datos de PostgreSQL se persisten en volúmenes Docker:
- `pg_data_nodo1`
- `pg_data_nodo2`
- `pg_data_nodo3`

Para hacer backup:
```bash
docker run --rm -v pg_data_nodo1:/data -v $(pwd):/backup alpine tar czf /backup/nodo1_backup.tar.gz -C /data .
```

## 🎯 Próximos Pasos

1. Accede al dashboard: http://localhost:8001
2. Verifica el estado de los nodos
3. Prueba ejecutar consultas SQL
4. Carga datos de prueba desde http://localhost:8001/carga-hc
