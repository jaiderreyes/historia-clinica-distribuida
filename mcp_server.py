"""
mcp_server.py - Servidor MCP dedicado para Historia Clínica Distribuida

Expone herramientas especializadas para que agentes de IA (como Antigravity)
puedan interactuar directamente con el sistema de historias clínicas:
  - Consultar estado de nodos PostgreSQL distribuidos
  - Buscar y obtener pacientes FHIR
  - Ejecutar queries SQL en todos los nodos
  - Insertar registros clínicos (FIRH)
  - Verificar salud del sistema HAPI FHIR

Uso:
    python mcp_server.py
    # O como herramienta MCP stdio (para Cursor/Claude Desktop):
    # mcp dev mcp_server.py
"""

import asyncio
import json
import os
import sys

import psycopg2
from psycopg2.extras import RealDictCursor
import httpx

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Tool,
    TextContent,
    CallToolResult,
)
from pydantic import AnyUrl

# ─────────────────────────────────────────────
# Configuración de nodos
# ─────────────────────────────────────────────
USE_DOCKER_NAMES = os.getenv("USE_DOCKER_NAMES", "false").lower() == "true"
FHIR_BASE_URL = os.getenv("FHIR_BASE_URL", "http://localhost:8080/fhir")
APP_BASE_URL = os.getenv("APP_BASE_URL", "http://localhost:8001")

if USE_DOCKER_NAMES:
    NODOS = [
        {"id": "nodo1", "host": "pg_nodo1", "port": 5432, "user": "admin", "password": "admin", "dbname": "historia_clinica"},
        {"id": "nodo2", "host": "pg_nodo2", "port": 5432, "user": "admin", "password": "admin", "dbname": "historia_clinica"},
        {"id": "nodo3", "host": "pg_nodo3", "port": 5432, "user": "admin", "password": "admin", "dbname": "historia_clinica"},
    ]
else:
    NODOS = [
        {"id": "nodo1", "host": "localhost", "port": 5433, "user": "admin", "password": "admin", "dbname": "historia_clinica"},
        {"id": "nodo2", "host": "localhost", "port": 5434, "user": "admin", "password": "admin", "dbname": "historia_clinica"},
        {"id": "nodo3", "host": "localhost", "port": 5435, "user": "admin", "password": "admin", "dbname": "historia_clinica"},
    ]


# ─────────────────────────────────────────────
# Helpers de base de datos
# ─────────────────────────────────────────────
def _conectar_nodo(nodo: dict):
    return psycopg2.connect(
        host=nodo["host"],
        port=nodo["port"],
        user=nodo["user"],
        password=nodo["password"],
        dbname=nodo["dbname"],
        connect_timeout=5,
    )


def _nodo_por_documento(documento_id: int) -> dict:
    if documento_id < 4_000_000_000:
        return NODOS[0]
    elif documento_id < 7_000_000_000:
        return NODOS[1]
    else:
        return NODOS[2]


# ─────────────────────────────────────────────
# Implementaciones de las herramientas
# ─────────────────────────────────────────────

def tool_estado_nodos() -> str:
    """Verifica el estado de conectividad de los 3 nodos PostgreSQL."""
    resultados = []
    for nodo in NODOS:
        info = {"nodo": nodo["id"], "host": nodo["host"], "puerto": nodo["port"], "estado": "DOWN", "error": None}
        try:
            conn = _conectar_nodo(nodo)
            with conn.cursor() as cur:
                cur.execute("SELECT version();")
                version = cur.fetchone()[0]
            conn.close()
            info["estado"] = "UP"
            info["version"] = version
        except Exception as e:
            info["error"] = str(e)
        resultados.append(info)
    nodos_up = sum(1 for n in resultados if n["estado"] == "UP")
    return json.dumps({
        "resumen": f"{nodos_up}/{len(NODOS)} nodos activos",
        "nodos": resultados
    }, ensure_ascii=False, indent=2)


def tool_ejecutar_query(query: str) -> str:
    """Ejecuta una query SQL de solo lectura en todos los nodos y une los resultados."""
    if any(kw in query.upper() for kw in ("DROP", "DELETE", "TRUNCATE", "ALTER", "CREATE")):
        return json.dumps({"error": "Solo se permiten queries SELECT para seguridad."})
    
    resultados_totales = []
    nodos_estado = []
    for nodo in NODOS:
        estado = {"nodo": nodo["id"], "estado": "DOWN"}
        try:
            conn = _conectar_nodo(nodo)
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query)
                filas = [dict(f) for f in cur.fetchall()]
            conn.close()
            estado["estado"] = "UP"
            estado["filas_obtenidas"] = len(filas)
            resultados_totales.extend(filas)
        except Exception as e:
            estado["error"] = str(e)
        nodos_estado.append(estado)
    
    return json.dumps({
        "query": query,
        "total_filas": len(resultados_totales),
        "nodos_estado": nodos_estado,
        "resultados": resultados_totales,
    }, ensure_ascii=False, indent=2, default=str)


def tool_buscar_paciente_nodo(documento_id: int) -> str:
    """Busca un paciente en el nodo correcto según su documento_id."""
    nodo = _nodo_por_documento(documento_id)
    try:
        conn = _conectar_nodo(nodo)
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT * FROM usuario WHERE documento_id = %s;",
                (documento_id,)
            )
            filas = [dict(f) for f in cur.fetchall()]
        conn.close()
        if filas:
            return json.dumps({
                "encontrado": True,
                "nodo": nodo["id"],
                "paciente": filas[0],
            }, ensure_ascii=False, indent=2, default=str)
        else:
            return json.dumps({"encontrado": False, "nodo": nodo["id"], "mensaje": f"No se encontró paciente con documento_id={documento_id}"})
    except Exception as e:
        return json.dumps({"error": str(e), "nodo": nodo["id"]})


def tool_listar_pacientes_nodo(nodo_id: str, limite: int = 20) -> str:
    """Lista pacientes de un nodo específico (nodo1, nodo2 o nodo3)."""
    nodo_map = {n["id"]: n for n in NODOS}
    if nodo_id not in nodo_map:
        return json.dumps({"error": f"Nodo '{nodo_id}' no existe. Usa: nodo1, nodo2, nodo3"})
    nodo = nodo_map[nodo_id]
    try:
        conn = _conectar_nodo(nodo)
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT documento_id, nombre_completo, fecha_nacimiento, edad, sexo FROM usuario LIMIT %s;",
                (min(limite, 100),)
            )
            filas = [dict(f) for f in cur.fetchall()]
        conn.close()
        return json.dumps({
            "nodo": nodo_id,
            "total": len(filas),
            "pacientes": filas
        }, ensure_ascii=False, indent=2, default=str)
    except Exception as e:
        return json.dumps({"error": str(e), "nodo": nodo_id})


async def tool_buscar_paciente_fhir(identifier: str) -> str:
    """Busca un paciente en HAPI FHIR por número de documento."""
    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            resp = await client.get(
                f"{FHIR_BASE_URL}/Patient",
                params={"identifier": identifier},
                headers={"Accept": "application/fhir+json"},
            )
            resp.raise_for_status()
            bundle = resp.json()
            pacientes = []
            if bundle.get("entry"):
                pacientes = [e["resource"] for e in bundle["entry"]]
            return json.dumps({
                "total": bundle.get("total", len(pacientes)),
                "pacientes": pacientes,
            }, ensure_ascii=False, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e), "fhir_url": FHIR_BASE_URL})


async def tool_obtener_paciente_fhir(patient_id: str) -> str:
    """Obtiene un paciente FHIR por su ID único."""
    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            resp = await client.get(
                f"{FHIR_BASE_URL}/Patient/{patient_id}",
                headers={"Accept": "application/fhir+json"},
            )
            if resp.status_code == 404:
                return json.dumps({"error": f"Paciente FHIR '{patient_id}' no encontrado"})
            resp.raise_for_status()
            return json.dumps(resp.json(), ensure_ascii=False, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)})


async def tool_salud_sistema() -> str:
    """Verifica la salud completa del sistema: API, nodos DB y FHIR."""
    resultado = {"api": {}, "nodos_db": {}, "hapi_fhir": {}}
    
    # API principal
    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            r = await client.get(f"{APP_BASE_URL}/api/health")
            resultado["api"] = {"estado": "UP", "datos": r.json()}
        except Exception as e:
            resultado["api"] = {"estado": "DOWN", "error": str(e)}
        
        # HAPI FHIR
        try:
            r = await client.get(f"{FHIR_BASE_URL}/metadata", headers={"Accept": "application/fhir+json"})
            meta = r.json()
            resultado["hapi_fhir"] = {
                "estado": "UP",
                "fhir_version": meta.get("fhirVersion"),
                "software": meta.get("software", {}).get("name"),
            }
        except Exception as e:
            resultado["hapi_fhir"] = {"estado": "DOWN", "error": str(e)}
    
    # Nodos PostgreSQL
    nodos_estado = []
    for nodo in NODOS:
        info = {"nodo": nodo["id"], "estado": "DOWN"}
        try:
            conn = _conectar_nodo(nodo)
            conn.close()
            info["estado"] = "UP"
        except Exception as e:
            info["error"] = str(e)
        nodos_estado.append(info)
    
    resultado["nodos_db"] = nodos_estado
    nodos_up = sum(1 for n in nodos_estado if n["estado"] == "UP")
    resultado["resumen"] = (
        f"API: {resultado['api']['estado']} | "
        f"DB: {nodos_up}/{len(NODOS)} nodos | "
        f"FHIR: {resultado['hapi_fhir']['estado']}"
    )
    
    return json.dumps(resultado, ensure_ascii=False, indent=2)


def tool_estadisticas_distribucion() -> str:
    """Obtiene estadísticas de distribución de datos entre los 3 nodos."""
    stats = []
    tablas = ["usuario", "atencion", "diagnostico", "egreso", "tecnologia_salud"]
    
    for nodo in NODOS:
        nodo_stats = {"nodo": nodo["id"], "tablas": {}, "estado": "DOWN"}
        try:
            conn = _conectar_nodo(nodo)
            with conn.cursor() as cur:
                for tabla in tablas:
                    try:
                        cur.execute(f"SELECT COUNT(*) FROM {tabla};")
                        count = cur.fetchone()[0]
                        nodo_stats["tablas"][tabla] = count
                    except Exception:
                        nodo_stats["tablas"][tabla] = "N/A"
            conn.close()
            nodo_stats["estado"] = "UP"
            nodo_stats["total_registros"] = sum(
                v for v in nodo_stats["tablas"].values() if isinstance(v, int)
            )
        except Exception as e:
            nodo_stats["error"] = str(e)
        stats.append(nodo_stats)
    
    total_global = sum(
        n.get("total_registros", 0) for n in stats if isinstance(n.get("total_registros"), int)
    )
    
    return json.dumps({
        "total_registros_global": total_global,
        "distribucion_por_nodo": stats,
    }, ensure_ascii=False, indent=2)


# ─────────────────────────────────────────────
# Definición de herramientas MCP
# ─────────────────────────────────────────────
TOOLS: list[Tool] = [
    Tool(
        name="estado_nodos",
        description=(
            "Verifica el estado de los 3 nodos PostgreSQL del sistema distribuido. "
            "Retorna si cada nodo está UP o DOWN y su versión de PostgreSQL."
        ),
        inputSchema={"type": "object", "properties": {}, "required": []},
    ),
    Tool(
        name="ejecutar_query_sql",
        description=(
            "Ejecuta una query SQL SELECT en todos los nodos PostgreSQL y combina los resultados. "
            "Útil para buscar datos sin saber en qué nodo están. Solo permite SELECT."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Query SQL SELECT a ejecutar. Ejemplo: 'SELECT * FROM usuario LIMIT 5;'",
                }
            },
            "required": ["query"],
        },
    ),
    Tool(
        name="buscar_paciente_nodo",
        description=(
            "Busca un paciente por su número de documento en el nodo correcto "
            "según la fragmentación horizontal (doc < 4B → nodo1, 4B-7B → nodo2, > 7B → nodo3)."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "documento_id": {
                    "type": "integer",
                    "description": "Número de documento del paciente (cédula, etc.)",
                }
            },
            "required": ["documento_id"],
        },
    ),
    Tool(
        name="listar_pacientes_nodo",
        description="Lista los pacientes registrados en un nodo PostgreSQL específico.",
        inputSchema={
            "type": "object",
            "properties": {
                "nodo_id": {
                    "type": "string",
                    "enum": ["nodo1", "nodo2", "nodo3"],
                    "description": "Identificador del nodo a consultar.",
                },
                "limite": {
                    "type": "integer",
                    "description": "Número máximo de pacientes a retornar (max 100). Default: 20.",
                    "default": 20,
                },
            },
            "required": ["nodo_id"],
        },
    ),
    Tool(
        name="buscar_paciente_fhir",
        description=(
            "Busca un paciente en HAPI FHIR Server por número de documento/identificador. "
            "Retorna el recurso FHIR Patient completo."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "identifier": {
                    "type": "string",
                    "description": "Número de documento o identificador a buscar en FHIR.",
                }
            },
            "required": ["identifier"],
        },
    ),
    Tool(
        name="obtener_paciente_fhir",
        description="Obtiene un paciente FHIR completo por su ID único en HAPI FHIR Server.",
        inputSchema={
            "type": "object",
            "properties": {
                "patient_id": {
                    "type": "string",
                    "description": "ID único del paciente en HAPI FHIR (ej: '1', '123', etc.).",
                }
            },
            "required": ["patient_id"],
        },
    ),
    Tool(
        name="salud_sistema",
        description=(
            "Verifica el estado de salud de todo el sistema: "
            "API FastAPI, nodos PostgreSQL y servidor HAPI FHIR."
        ),
        inputSchema={"type": "object", "properties": {}, "required": []},
    ),
    Tool(
        name="estadisticas_distribucion",
        description=(
            "Muestra estadísticas de cuántos registros hay en cada tabla "
            "de cada nodo PostgreSQL. Útil para entender la distribución de datos."
        ),
        inputSchema={"type": "object", "properties": {}, "required": []},
    ),
]


# ─────────────────────────────────────────────
# Servidor MCP principal
# ─────────────────────────────────────────────
server = Server("historia-clinica-mcp")


@server.list_tools()
async def list_tools() -> list[Tool]:
    return TOOLS


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    try:
        if name == "estado_nodos":
            result = tool_estado_nodos()

        elif name == "ejecutar_query_sql":
            result = tool_ejecutar_query(arguments["query"])

        elif name == "buscar_paciente_nodo":
            result = tool_buscar_paciente_nodo(int(arguments["documento_id"]))

        elif name == "listar_pacientes_nodo":
            result = tool_listar_pacientes_nodo(
                arguments["nodo_id"],
                int(arguments.get("limite", 20)),
            )

        elif name == "buscar_paciente_fhir":
            result = await tool_buscar_paciente_fhir(arguments["identifier"])

        elif name == "obtener_paciente_fhir":
            result = await tool_obtener_paciente_fhir(arguments["patient_id"])

        elif name == "salud_sistema":
            result = await tool_salud_sistema()

        elif name == "estadisticas_distribucion":
            result = tool_estadisticas_distribucion()

        else:
            result = json.dumps({"error": f"Herramienta '{name}' no reconocida."})

    except Exception as e:
        result = json.dumps({"error": str(e), "herramienta": name})

    return [TextContent(type="text", text=result)]


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


if __name__ == "__main__":
    asyncio.run(main())
