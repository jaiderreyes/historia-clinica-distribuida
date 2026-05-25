# 🤖 Integración MCP — Historia Clínica Distribuida

Este proyecto expone sus capacidades a agentes de IA mediante el **Model Context Protocol (MCP)**, permitiendo que herramientas como Antigravity (Cursor), Claude Desktop y otros agentes interactúen directamente con el sistema.

## Arquitectura MCP

Existen **dos puntos de acceso MCP**:

### 1. FastAPI-MCP (HTTP) — `/mcp`
Expone **automáticamente todos los endpoints REST** de la API como herramientas MCP disponibles via HTTP SSE.

- **URL**: `http://localhost:8001/mcp`
- **Cómo funciona**: `fastapi-mcp` escanea todos los endpoints de `app.py` y los convierte en herramientas MCP con sus schemas Pydantic y documentación Swagger.

### 2. Servidor MCP dedicado (stdio) — `mcp_server.py`
Servidor MCP especializado con **herramientas de dominio** del sistema clínico. Se conecta via **stdio** (protocolo estándar para Cursor/Claude Desktop).

---

## Herramientas MCP disponibles

| Herramienta | Descripción |
|---|---|
| `estado_nodos` | Estado de los 3 nodos PostgreSQL distribuidos |
| `ejecutar_query_sql` | Ejecuta SELECT en todos los nodos y combina resultados |
| `buscar_paciente_nodo` | Busca un paciente por documento_id en el nodo correcto |
| `listar_pacientes_nodo` | Lista pacientes de un nodo específico (nodo1/2/3) |
| `buscar_paciente_fhir` | Busca paciente en HAPI FHIR por número de documento |
| `obtener_paciente_fhir` | Obtiene paciente FHIR completo por su ID único |
| `salud_sistema` | Estado de todo el sistema: API + DB nodos + HAPI FHIR |
| `estadisticas_distribucion` | Conteo de registros por tabla en cada nodo |

---

## Configuración para Cursor (Antigravity)

La configuración ya está en `.cursor/mcp.json`. Cursor la detecta automáticamente.

Para activarla en Cursor:
1. Abre **Cursor Settings** → **MCP**
2. El servidor `historia-clinica` debería aparecer listado
3. Actívalo con el toggle

### Variables de entorno configurables

| Variable | Default | Descripción |
|---|---|---|
| `USE_DOCKER_NAMES` | `false` | `true` cuando se ejecuta dentro de Docker |
| `FHIR_BASE_URL` | `http://localhost:8080/fhir` | URL del servidor HAPI FHIR |
| `APP_BASE_URL` | `http://localhost:8001` | URL de la API FastAPI |

---

## Configuración para Claude Desktop

Agrega esto a `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "historia-clinica": {
      "command": "/Users/jaiderreyes/Github/historia-clinica-distribuida/venv312/bin/python",
      "args": ["/Users/jaiderreyes/Github/historia-clinica-distribuida/mcp_server.py"],
      "env": {
        "USE_DOCKER_NAMES": "false",
        "FHIR_BASE_URL": "http://localhost:8080/fhir",
        "APP_BASE_URL": "http://localhost:8001"
      }
    }
  }
}
```

---

## Uso del servidor MCP HTTP (cuando la app está corriendo)

Con la API corriendo en `http://localhost:8001`, el endpoint MCP está disponible en:

```
http://localhost:8001/mcp
```

### Conectar con MCP Inspector (debug)
```bash
npx @modelcontextprotocol/inspector http://localhost:8001/mcp
```

### Conectar cliente MCP al servidor HTTP
```python
from mcp.client.sse import sse_client
from mcp import ClientSession

async with sse_client("http://localhost:8001/mcp") as (read, write):
    async with ClientSession(read, write) as session:
        await session.initialize()
        tools = await session.list_tools()
        print(tools)
```

---

## Ejecutar el servidor MCP standalone (stdio)

```bash
# Activar entorno Python 3.12
source venv312/bin/activate

# Ejecutar directamente (modo stdio, para testing)
python mcp_server.py

# Probar con MCP dev tools
mcp dev mcp_server.py
```

---

## Requisitos

- **Python 3.12** (en `venv312/`) — requerido por `fastapi-mcp` y `mcp` SDK
- El venv principal (`venv/`) usa Python 3.9 y solo soporta la API FastAPI sin MCP

### Instalar dependencias MCP (si es necesario)
```bash
python3.12 -m venv venv312
source venv312/bin/activate
pip install -r requirements.txt
```

---

## Fragmentación y enrutamiento de datos

El sistema usa **fragmentación horizontal** por `documento_id`:

| Rango documento_id | Nodo |
|---|---|
| `< 4.000.000.000` | Nodo 1 (puerto 5433) |
| `4.000.000.000 – 6.999.999.999` | Nodo 2 (puerto 5434) |
| `≥ 7.000.000.000` | Nodo 3 (puerto 5435) |

La herramienta `buscar_paciente_nodo` usa esta lógica automáticamente.
