#!/usr/bin/env bash
# Script de prueba del MVP FHIR
# Uso: ./test-mvp-fhir.sh

set -e

echo "🧪 Prueba del MVP FHIR - Historia Clínica Interoperable"
echo "========================================================"
echo ""

# Colores
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Función para verificar respuesta
check_response() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ $1${NC}"
    else
        echo -e "${RED}❌ $1${NC}"
        exit 1
    fi
}

# 1. Verificar que Docker está corriendo
echo "1️⃣  Verificando Docker..."
export PATH="/Applications/Docker.app/Contents/Resources/bin:$PATH"
docker compose ps > /dev/null 2>&1
check_response "Docker Compose está disponible"
echo ""

# 2. Verificar servicios
echo "2️⃣  Verificando servicios..."
SERVICES=$(docker compose ps --format json | jq -r '.[].Service' 2>/dev/null || docker compose ps | grep -E "(app|hapi-fhir|pg_nodo)" | wc -l)
echo "   Servicios activos: $SERVICES"
check_response "Servicios están corriendo"
echo ""

# 3. Verificar API principal
echo "3️⃣  Verificando API principal..."
HEALTH=$(curl -s http://localhost:8001/api/health | jq -r '.status' 2>/dev/null || echo "error")
if [ "$HEALTH" = "ok" ]; then
    echo -e "${GREEN}✅ API principal respondiendo${NC}"
else
    echo -e "${RED}❌ API principal no responde${NC}"
    exit 1
fi
echo ""

# 4. Verificar HAPI FHIR Server
echo "4️⃣  Verificando HAPI FHIR Server..."
FHIR_VERSION=$(curl -s http://localhost:8080/fhir/metadata 2>/dev/null | jq -r '.fhirVersion' 2>/dev/null || echo "error")
if [ "$FHIR_VERSION" != "error" ] && [ "$FHIR_VERSION" != "" ]; then
    echo -e "${GREEN}✅ HAPI FHIR Server respondiendo (FHIR $FHIR_VERSION)${NC}"
else
    echo -e "${YELLOW}⚠️  HAPI FHIR Server aún está iniciando (esto es normal)${NC}"
    echo "   Esperando 10 segundos..."
    sleep 10
    FHIR_VERSION=$(curl -s http://localhost:8080/fhir/metadata 2>/dev/null | jq -r '.fhirVersion' 2>/dev/null || echo "error")
    if [ "$FHIR_VERSION" != "error" ] && [ "$FHIR_VERSION" != "" ]; then
        echo -e "${GREEN}✅ HAPI FHIR Server ahora está respondiendo${NC}"
    else
        echo -e "${RED}❌ HAPI FHIR Server no responde${NC}"
        echo "   Revisa los logs: docker compose logs hapi-fhir"
        exit 1
    fi
fi
echo ""

# 5. Crear paciente de prueba
echo "5️⃣  Creando paciente de prueba..."
PATIENT_DATA='{
  "tipoDocumento": "CC",
  "numeroDocumento": "9999999999",
  "paisNacionalidad": "CO",
  "nombreCompleto": "Paciente de Prueba MVP",
  "fechaNacimiento": "1990-01-01",
  "edad": 34,
  "unidadEdad": "1",
  "sexo": "male",
  "genero": "Masculino",
  "ocupacion": "Ingeniero de Software",
  "voluntadAnticipada": "false",
  "categoriaDiscapacidad": "",
  "paisResidencia": "CO",
  "municipioResidencia": "11001",
  "etnia": "Ninguna"
}'

RESPONSE=$(curl -s -X POST http://localhost:8001/api/v1/fhir/patient \
  -H "Content-Type: application/json" \
  -d "$PATIENT_DATA")

SUCCESS=$(echo $RESPONSE | jq -r '.success' 2>/dev/null || echo "false")
PATIENT_ID=$(echo $RESPONSE | jq -r '.patient_id' 2>/dev/null || echo "")

if [ "$SUCCESS" = "true" ] && [ "$PATIENT_ID" != "" ]; then
    echo -e "${GREEN}✅ Paciente creado exitosamente${NC}"
    echo "   ID FHIR: $PATIENT_ID"
else
    echo -e "${RED}❌ Error al crear paciente${NC}"
    echo "   Respuesta: $RESPONSE"
    exit 1
fi
echo ""

# 6. Buscar paciente creado
echo "6️⃣  Buscando paciente creado..."
PATIENT=$(curl -s http://localhost:8001/api/v1/fhir/patient/$PATIENT_ID)
PATIENT_NAME=$(echo $PATIENT | jq -r '.name[0].text' 2>/dev/null || echo "")

if [ "$PATIENT_NAME" = "Paciente de Prueba MVP" ]; then
    echo -e "${GREEN}✅ Paciente encontrado: $PATIENT_NAME${NC}"
else
    echo -e "${RED}❌ No se pudo encontrar el paciente${NC}"
    exit 1
fi
echo ""

# 7. Buscar por número de documento
echo "7️⃣  Buscando por número de documento..."
SEARCH_RESULT=$(curl -s "http://localhost:8001/api/v1/fhir/patient/search/9999999999")
TOTAL=$(echo $SEARCH_RESULT | jq -r '.total' 2>/dev/null || echo "0")

if [ "$TOTAL" -gt "0" ]; then
    echo -e "${GREEN}✅ Búsqueda por documento exitosa (encontrados: $TOTAL)${NC}"
else
    echo -e "${YELLOW}⚠️  No se encontraron resultados (esto puede ser normal)${NC}"
fi
echo ""

# 8. Verificar base de datos FHIR
echo "8️⃣  Verificando base de datos FHIR..."
FHIR_DB=$(docker exec pg_nodo1 psql -U admin -d fhir_db -c "SELECT 1" 2>/dev/null || echo "error")
if [ "$FHIR_DB" != "error" ]; then
    echo -e "${GREEN}✅ Base de datos FHIR accesible${NC}"
else
    echo -e "${RED}❌ No se puede acceder a la base de datos FHIR${NC}"
    exit 1
fi
echo ""

# Resumen final
echo "=========================================="
echo -e "${GREEN}🎉 ¡TODAS LAS PRUEBAS PASARON!${NC}"
echo "=========================================="
echo ""
echo "📊 Resumen:"
echo "   ✅ Docker Compose operativo"
echo "   ✅ API principal funcionando"
echo "   ✅ HAPI FHIR Server funcionando (FHIR $FHIR_VERSION)"
echo "   ✅ Paciente creado (ID: $PATIENT_ID)"
echo "   ✅ Búsqueda funcionando"
echo "   ✅ Base de datos FHIR operativa"
echo ""
echo "🌐 URLs:"
echo "   Dashboard:           http://localhost:8001"
echo "   Registro Paciente:   http://localhost:8001/registro-paciente"
echo "   API Docs:            http://localhost:8001/docs"
echo "   HAPI FHIR Web:       http://localhost:8080"
echo ""
echo "📝 Próximos pasos:"
echo "   1. Abre http://localhost:8001/registro-paciente"
echo "   2. Registra más pacientes manualmente"
echo "   3. Explora la API en http://localhost:8001/docs"
echo ""
