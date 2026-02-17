# Docker Configuration Guide

## 🐳 Overview

This document describes the Docker configuration for the Distributed Electronic Health Record System, including the setup of three PostgreSQL nodes and the HAPI FHIR server.

## 📋 Prerequisites

- Docker Engine 20.10+
- Docker Compose v2.0+ (or docker-compose v1.29+)
- At least 4GB available RAM
- Ports 5433, 5434, 5435, and 8080 available

## 🏗️ Architecture

### Services

1. **pg_nodo1** - PostgreSQL Node 1 (Port 5433)
2. **pg_nodo2** - PostgreSQL Node 2 (Port 5434)
3. **pg_nodo3** - PostgreSQL Node 3 (Port 5435)
4. **hapi-fhir** - HAPI FHIR Server (Port 8080)

### Networks

- **db-network**: Internal network for database communication
- **fhir-network**: Network for FHIR server communication

### Volumes

- **pg_data_nodo1**: Persistent data for Node 1
- **pg_data_nodo2**: Persistent data for Node 2
- **pg_data_nodo3**: Persistent data for Node 3
- **hapi-data**: Persistent data for HAPI FHIR

## 🚀 Quick Start

### 1. Start All Services

```bash
# Using Docker Compose v2
docker compose up -d

# Using Docker Compose v1
docker-compose up -d
```

### 2. Verify Status

```bash
# Check running containers
docker compose ps

# Expected output:
# NAME        STATUS      PORTS
# pg_nodo1    Up (healthy)    0.0.0.0:5433->5432/tcp
# pg_nodo2    Up (healthy)    0.0.0.0:5434->5432/tcp
# pg_nodo3    Up (healthy)    0.0.0.0:5435->5432/tcp
# hapi-fhir   Up              0.0.0.0:8080->8080/tcp
```

### 3. Initialize Databases

```bash
# Load schema on each node
psql -h localhost -p 5433 -U admin -d historia_clinica -f nodo1.sql
psql -h localhost -p 5434 -U admin -d historia_clinica -f nodo2.sql
psql -h localhost -p 5435 -U admin -d historia_clinica -f nodo3.sql
```

## 🔧 Configuration Details

### PostgreSQL Nodes

Each node is configured with:

```yaml
environment:
  POSTGRES_USER: admin
  POSTGRES_PASSWORD: admin
  POSTGRES_DB: historia_clinica
  POSTGRES_INITDB_ARGS: "--encoding=UTF8 --locale=en_US.UTF-8"
```

**Health Check:**
- Command: `pg_isready -U admin -d historia_clinica`
- Interval: 10 seconds
- Timeout: 5 seconds
- Retries: 5

### HAPI FHIR Server

Configuration:
```yaml
environment:
  spring.datasource.url: jdbc:postgresql://pg_nodo1:5432/historia_clinica
  spring.datasource.username: admin
  spring.datasource.password: admin
  hapi.fhir.fhir_version: R4
```

Access: http://localhost:8080

## 📊 Resource Management

### Memory Limits

Default configuration:
- Each PostgreSQL node: 512MB
- HAPI FHIR: 2GB

To modify, edit `docker-compose.yml`:

```yaml
services:
  pg_nodo1:
    deploy:
      resources:
        limits:
          memory: 1G
        reservations:
          memory: 512M
```

## 🔍 Monitoring

### View Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f pg_nodo1
docker compose logs -f hapi-fhir

# Last 100 lines
docker compose logs --tail=100 pg_nodo1
```

### Container Stats

```bash
# Real-time resource usage
docker stats

# Specific containers
docker stats pg_nodo1 pg_nodo2 pg_nodo3
```

## 🛠️ Common Operations

### Stop Services

```bash
# Stop all
docker compose stop

# Stop specific service
docker compose stop pg_nodo1
```

### Restart Services

```bash
# Restart all
docker compose restart

# Restart specific service
docker compose restart pg_nodo2
```

### Remove Services

```bash
# Stop and remove containers (keeps volumes)
docker compose down

# Remove containers and volumes (WARNING: deletes data)
docker compose down -v
```

## 💾 Backup and Restore

### Backup Database

```bash
# Backup Node 1
docker exec pg_nodo1 pg_dump -U admin historia_clinica > backup_nodo1.sql

# Backup all nodes
for i in 1 2 3; do
  docker exec pg_nodo$i pg_dump -U admin historia_clinica > backup_nodo$i.sql
done
```

### Restore Database

```bash
# Restore Node 1
docker exec -i pg_nodo1 psql -U admin -d historia_clinica < backup_nodo1.sql
```

### Backup Volumes

```bash
# Backup volume data
docker run --rm \
  -v pg_data_nodo1:/data \
  -v $(pwd):/backup \
  alpine tar czf /backup/nodo1_data.tar.gz -C /data .
```

## 🔐 Security

### Change Default Credentials

1. Edit `docker-compose.yml`:
```yaml
environment:
  POSTGRES_USER: your_user
  POSTGRES_PASSWORD: your_secure_password
```

2. Update `middleware.py` with new credentials

3. Recreate containers:
```bash
docker compose down -v
docker compose up -d
```

### Network Isolation

The services use internal networks:
- Database nodes communicate via `db-network`
- FHIR server uses `fhir-network`
- Only specified ports are exposed to host

## 🐛 Troubleshooting

### Port Already in Use

```bash
# Find process using port
lsof -i :5433
# or
netstat -an | grep 5433

# Kill process or change port in docker-compose.yml
```

### Container Won't Start

```bash
# Check logs
docker compose logs pg_nodo1

# Remove and recreate
docker compose rm -f pg_nodo1
docker compose up -d pg_nodo1
```

### Database Connection Issues

```bash
# Test connection
docker exec -it pg_nodo1 psql -U admin -d historia_clinica

# Verify network
docker network inspect historia-clinica-distribuida_db-network
```

### Health Check Failing

```bash
# Manual health check
docker exec pg_nodo1 pg_isready -U admin -d historia_clinica

# Check PostgreSQL logs
docker compose logs pg_nodo1 | grep -i error
```

## 📈 Performance Tuning

### PostgreSQL Configuration

Create `postgresql.conf` and mount it:

```yaml
volumes:
  - ./postgresql.conf:/etc/postgresql/postgresql.conf
command: postgres -c config_file=/etc/postgresql/postgresql.conf
```

Recommended settings:
```conf
max_connections = 100
shared_buffers = 256MB
effective_cache_size = 1GB
work_mem = 4MB
maintenance_work_mem = 64MB
```

## 🔄 Updates

### Update Images

```bash
# Pull latest images
docker compose pull

# Recreate containers with new images
docker compose up -d
```

### Update Configuration

```bash
# Edit docker-compose.yml
nano docker-compose.yml

# Apply changes
docker compose up -d
```

## 📚 Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [PostgreSQL Docker Image](https://hub.docker.com/_/postgres)
- [HAPI FHIR Documentation](https://hapifhir.io/)
- [Docker Compose Reference](https://docs.docker.com/compose/compose-file/)

---

**Last Updated**: 2026-02-17  
**Version**: 2.0.0
