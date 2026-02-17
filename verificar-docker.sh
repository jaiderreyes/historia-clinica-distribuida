#!/usr/bin/env bash
# Verificación de Docker Compose para Historia Clínica Distribuida
# Uso: ./verificar-docker.sh

set -e
cd "$(dirname "$0")"

echo "=== Verificación Docker Compose ==="
echo ""

# 1. Docker disponible
if ! command -v docker &>/dev/null; then
  echo "❌ Docker no está instalado o no está en el PATH."
  echo "   Instala Docker Desktop o Docker Engine: https://docs.docker.com/get-docker/"
  exit 1
fi
echo "✓ Docker: $(docker --version)"

# 2. Docker Compose (v2 o v1)
COMPOSE_CMD=""
if docker compose version &>/dev/null; then
  COMPOSE_CMD="docker compose"
elif command -v docker-compose &>/dev/null; then
  COMPOSE_CMD="docker-compose"
else
  echo "❌ Docker Compose no encontrado. Usa 'docker compose' (v2) o instala docker-compose (v1)."
  exit 1
fi
echo "✓ Compose: $COMPOSE_CMD"
echo ""

# 3. Puertos en uso
for port in 5433 5434 5435; do
  if (lsof -i :$port -sTCP:LISTEN -t &>/dev/null) || (netstat -an 2>/dev/null | grep -q "[.:]$port .*LISTEN"); then
    echo "⚠ Puerto $port ya está en uso. Libera el puerto o detén el proceso que lo usa."
    echo "  Ejemplo: lsof -i :$port"
  fi
done
echo "✓ Puertos 5433, 5434, 5435 comprobados"
echo ""

# 4. Levantar servicios
echo "Levantando contenedores..."
$COMPOSE_CMD up -d

echo ""
echo "Esperando a que PostgreSQL esté listo (healthcheck)..."
sleep 3
for i in 1 2 3 4 5 6 7 8 9 10; do
  if $COMPOSE_CMD ps 2>/dev/null | grep -q "healthy"; then
    break
  fi
  echo "  intento $i/10..."
  sleep 2
done

echo ""
echo "Estado de los contenedores:"
$COMPOSE_CMD ps

echo ""
echo "=== Probar conexión desde el host (requiere psql o Python) ==="
if command -v psql &>/dev/null; then
  for port in 5433 5434 5435; do
    if PGPASSWORD=admin psql -h 127.0.0.1 -p $port -U admin -d historia_clinica -c "SELECT 1" &>/dev/null; then
      echo "✓ Nodo puerto $port: conexión OK"
    else
      echo "✗ Nodo puerto $port: no se pudo conectar"
    fi
  done
else
  echo "  (psql no instalado; la app Python probará al usar consultas)"
  echo "  Si la app falla al conectar, asegúrate de que los 3 contenedores estén 'Up' y 'healthy'."
fi

echo ""
echo "=== Resumen ==="
echo "  Nodo 1: localhost:5433 (documento_id < 4e9)"
echo "  Nodo 2: localhost:5434 (4e9 <= documento_id < 7e9)"
echo "  Nodo 3: localhost:5435 (documento_id >= 7e9)"
echo ""
echo "  Cargar esquema (primera vez):"
echo "    psql -h localhost -p 5433 -U admin -d historia_clinica -f nodo1.sql"
echo "    psql -h localhost -p 5434 -U admin -d historia_clinica -f nodo2.sql"
echo "    psql -h localhost -p 5435 -U admin -d historia_clinica -f nodo3.sql"
echo ""
