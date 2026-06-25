#!/usr/bin/env bash
# Script para inicializar las bases de datos en los nodos PostgreSQL
# Uso: ./init-databases.sh

set -e

echo "🔧 Inicializando bases de datos en los nodos PostgreSQL..."
echo ""

# Esperar a que los contenedores estén listos
echo "⏳ Esperando a que los nodos estén listos..."
sleep 5

# Función para cargar el esquema en un nodo
load_schema() {
    local port=$1
    local sql_file=$2
    local nodo_name=$3
    
    echo "📊 Cargando esquema en $nodo_name (puerto $port)..."
    
    if docker exec -i pg_nodo${nodo_name: -1} psql -U admin -d historia_clinica < $sql_file; then
        echo "✅ Esquema cargado exitosamente en $nodo_name"
    else
        echo "❌ Error al cargar esquema en $nodo_name"
        return 1
    fi
}

# Cargar esquemas en cada nodo
load_schema 5433 nodo1.sql "Nodo 1"
echo ""
load_schema 5434 nodo2.sql "Nodo 2"
echo ""
load_schema 5435 nodo3.sql "Nodo 3"
echo ""

echo "📊 Creando base de datos FHIR en Nodo 1..."
if docker exec -i pg_nodo1 psql -U admin -d postgres -c "CREATE DATABASE fhir_db;" 2>/dev/null; then
    echo "✅ Base de datos FHIR creada exitosamente"
else
    echo "ℹ️  Base de datos FHIR ya existe (esto es normal)"
fi
echo ""

echo "✨ Inicialización completada!"
echo ""
echo "📝 Puedes verificar las tablas con:"
echo "   docker exec -it pg_nodo1 psql -U admin -d historia_clinica -c '\\dt'"
